#!/usr/bin/python3
"""Float REAPER child windows that XWayland exposes without WM_CLASS/title."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys


def sway(*args):
    result = subprocess.run(['swaymsg', '-r', *args], capture_output=True,
                            text=True, check=True, timeout=4)
    return json.loads(result.stdout)


def windows(node):
    if node.get('type') == 'con' and node.get('window'):
        yield node
    for child in node.get('nodes', []) + node.get('floating_nodes', []):
        yield from windows(child)


def is_reaper_popup(node):
    pid = node.get('pid')
    if not isinstance(pid, int) or node.get('shell') != 'xwayland':
        return False
    try:
        executable = os.readlink(f'/proc/{pid}/exe')
    except OSError:
        return False
    if Path(executable).name != 'reaper':
        return False
    props = node.get('window_properties') or {}
    title = props.get('title') or node.get('name') or ''
    return not (props.get('class') == 'REAPER' and 'REAPER v' in title)


def update():
    for node in windows(sway('-t', 'get_tree')):
        if is_reaper_popup(node) and node.get('floating') not in ('user_on', 'auto_on'):
            reply = sway(f"[con_id={node['id']}] floating enable")
            if any(not part.get('success') for part in reply):
                print(f"reaper popups: {reply}", file=sys.stderr, flush=True)


def main():
    lock_path = Path(os.environ['XDG_RUNTIME_DIR']) / 'reaper-popups.lock'
    with lock_path.open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        update()
        process = subprocess.Popen(['swaymsg', '-m', '-r', '-t', 'subscribe',
                                    '["window"]'], stdout=subprocess.PIPE, text=True)
        try:
            for line in process.stdout:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get('change') in ('new', 'title'):
                    update()
        finally:
            process.terminate()


if __name__ == '__main__':
    main()
