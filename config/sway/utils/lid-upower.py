#!/usr/bin/python3
"""Reconcile the internal Sway output with UPower lid and output state."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

INTERNAL = 'eDP-1'
EXTERNAL = 'HDMI-A-1'
UP_IFACE = 'org.freedesktop.UPower'


def sway(*args):
    result = subprocess.run(['swaymsg', '-r', *args], check=True,
                            capture_output=True, text=True, timeout=4)
    data = json.loads(result.stdout)
    if isinstance(data, list) and any(x.get('success') is False for x in data):
        raise RuntimeError(str(data))
    return data


def desired_enabled(closed, outputs):
    external = any(o['name'] != INTERNAL and o.get('active', False) for o in outputs)
    return not closed or not external


def position_commands(outputs):
    active = {o['name']: o for o in outputs if o.get('active')}
    commands = []
    for name in (INTERNAL, EXTERNAL):
        if name not in active:
            continue
        x = active[INTERNAL]['rect']['width'] if name == EXTERNAL and INTERNAL in active else 0
        rect = active[name]['rect']
        if (rect['x'], rect['y']) != (x, 0):
            commands.append(f'output {name} position {x} 0')
    return commands


class Controller:
    def __init__(self, bus):
        self.bus = bus
        self.previous_closed = None
        self.previous_enabled = None
        self.sleeping = False
        self.last_error = None
        self.scan_pending = False

    def schedule_scan(self):
        if not self.scan_pending:
            self.scan_pending = True
            GLib.timeout_add(1800, self.scan_workspaces)
        return False

    def scan_workspaces(self):
        self.scan_pending = False
        try:
            outputs = sway('-t', 'get_outputs')
            if not any(o['name'] == INTERNAL and o.get('active') for o in outputs):
                return False
            workspaces = sway('-t', 'get_workspaces')
            focused = next((w['name'] for w in workspaces if w.get('focused')), None)
            if focused is None:
                return False
            # Visit existing workspaces only; do not create or assign empty ones.
            commands = [f'workspace --no-auto-back-and-forth {json.dumps(w["name"])}'
                        for w in workspaces if w['name'] != focused]
            for workspace in workspaces:
                if workspace.get('visible') and workspace['name'] != focused:
                    commands.append('workspace --no-auto-back-and-forth '
                                    + json.dumps(workspace['name']))
            commands.append(f'workspace --no-auto-back-and-forth {json.dumps(focused)}')
            sway('; '.join(commands))
            print(f'clamshell: refreshed {len(workspaces)} workspaces, restored {focused}', flush=True)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            print(f'clamshell scan: {exc}', file=sys.stderr, flush=True)
        return False

    def closed(self):
        obj = self.bus.get_object(UP_IFACE, '/org/freedesktop/UPower', introspect=False)
        props = dbus.Interface(obj, 'org.freedesktop.DBus.Properties')
        values = props.GetAll(UP_IFACE, timeout=3)
        return bool(values['LidIsPresent'] and values['LidIsClosed'])

    def reconcile(self, wake=False):
        if self.sleeping:
            return False
        try:
            outputs = sway('-t', 'get_outputs')
            panel = next((o for o in outputs if o['name'] == INTERNAL), None)
            if panel is None:
                return False
            # If UPower is unavailable, fail safe: never disable the only panel.
            try:
                closed = self.closed()
            except dbus.DBusException:
                closed = False
            enabled = desired_enabled(closed, outputs)
            opened = self.previous_closed is True and not closed
            restored = self.previous_enabled is False and enabled
            active = panel.get('active', False)
            panel_started = enabled and not active
            if enabled and (not active or wake or opened or restored):
                sway(f'output {INTERNAL} enable; output {INTERNAL} power on')
                print('internal enabled: lid open, external lost, or resume', flush=True)
            elif not enabled and active:
                sway(f'output {INTERNAL} disable')
                print('internal disabled: lid closed and external active', flush=True)
            outputs = sway('-t', 'get_outputs')
            commands = position_commands(outputs)
            if commands:
                sway('; '.join(commands))
            if panel_started:
                self.schedule_scan()
            self.previous_closed = closed
            self.previous_enabled = enabled
            self.last_error = None
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            if str(exc) != self.last_error:
                print(f'clamshell: {exc}', file=sys.stderr, flush=True)
                self.last_error = str(exc)
        return False

    def properties_changed(self, interface, changed, invalidated):
        if interface == UP_IFACE and ({'LidIsClosed', 'LidIsPresent'} &
                                     (set(changed) | set(invalidated))):
            self.reconcile()

    def prepare_sleep(self, sleeping):
        self.sleeping = bool(sleeping)
        if not self.sleeping:
            self.reconcile(wake=True)
            GLib.timeout_add(1500, self.reconcile)


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'watch'
    if action not in ('watch', 'open', 'close', 'sync'):
        raise SystemExit('Usage: lid.sh [watch|open|close|sync]')
    if action == 'open':
        sway(f'output {INTERNAL} enable; output {INTERNAL} power on')
        return
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    controller = Controller(bus)
    if action != 'watch':
        # close/sync always consult the actual lid state, not a stale command.
        controller.reconcile()
        return
    socket = os.environ['SWAYSOCK']
    digest = hashlib.sha256(socket.encode()).hexdigest()[:16]
    lock = open(Path(os.environ['XDG_RUNTIME_DIR']) / f'sway-lid-{digest}.lock', 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return
    loop = GLib.MainLoop()
    bus.add_signal_receiver(controller.properties_changed,
                            signal_name='PropertiesChanged',
                            dbus_interface='org.freedesktop.DBus.Properties',
                            path='/org/freedesktop/UPower')
    bus.add_signal_receiver(controller.prepare_sleep, signal_name='PrepareForSleep',
                            dbus_interface='org.freedesktop.login1.Manager',
                            bus_name='org.freedesktop.login1')
    subscriber = subprocess.Popen(['swaymsg', '-m', '-r', '-t', 'subscribe',
                                   '["output", "shutdown"]'], stdout=subprocess.PIPE,
                                  text=True)

    def events():
        for line in subscriber.stdout:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get('change') == 'exit':
                break
            GLib.idle_add(controller.reconcile)
        GLib.idle_add(loop.quit)

    def poll():
        controller.reconcile()
        return True

    threading.Thread(target=events, daemon=True).start()
    GLib.timeout_add_seconds(3, poll)
    for sig in (signal.SIGTERM, signal.SIGINT):
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, sig, loop.quit)
    controller.reconcile()
    try:
        loop.run()
    finally:
        subscriber.terminate()
        try:
            subscriber.wait(timeout=2)
        except subprocess.TimeoutExpired:
            subscriber.kill()
            subscriber.wait()


if __name__ == '__main__':
    main()
