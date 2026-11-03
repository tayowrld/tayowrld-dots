#!/usr/bin/env python3
"""Keep each new Sway window at the end of a per-workspace spiral."""

import fcntl
import json
import os
import socket
import struct
import subprocess
import sys

MAGIC = b"i3-ipc"
MARK = "__retro_spiral_tail"


def receive(sock):
    def exact(size):
        chunks = []
        while size:
            chunk = sock.recv(size)
            if not chunk:
                raise EOFError("Sway IPC disconnected")
            chunks.append(chunk)
            size -= len(chunk)
        return b"".join(chunks)

    header = exact(14)
    if header[:6] != MAGIC:
        raise ValueError("Unexpected Sway IPC response")
    size, message_type = struct.unpack("<II", header[6:])
    return message_type, json.loads(exact(size))


def request(message_type, body=b""):
    with socket.socket(socket.AF_UNIX) as sock:
        sock.connect(os.environ["SWAYSOCK"])
        sock.sendall(MAGIC + struct.pack("<II", len(body), message_type) + body)
        return receive(sock)[1]


def leaves(node):
    children = node.get("nodes", [])
    if children:
        for child in children:
            yield from leaves(child)
    elif node.get("type") == "con" and (node.get("app_id") or node.get("window")):
        yield node["id"]


def workspaces(node):
    if node.get("type") == "workspace" and node.get("name") != "__i3_scratch":
        yield node
    for child in node.get("nodes", []):
        yield from workspaces(child)


def is_ordinary_tiling(node, wanted, floating=False):
    if node.get("id") == wanted:
        return not floating and node.get("floating") not in ("user_on", "auto_on")
    for child in node.get("nodes", []):
        found = is_ordinary_tiling(child, wanted, floating)
        if found is not None:
            return found
    for child in node.get("floating_nodes", []):
        found = is_ordinary_tiling(child, wanted, True)
        if found is not None:
            return found
    return None


def has_special_layout(node):
    if node.get("layout") in ("tabbed", "stacked"):
        return True
    return any(has_special_layout(child) for child in node.get("nodes", []))


def command(line):
    result = subprocess.run(["swaymsg", "-r", line], capture_output=True, text=True)
    if result.returncode:
        print(f"spiral: {result.stderr.strip()}", file=sys.stderr)
        return False
    try:
        replies = json.loads(result.stdout)
        if any(not item.get("success", False) for item in replies):
            print(f"spiral: {replies}", file=sys.stderr)
            return False
    except (json.JSONDecodeError, TypeError):
        print(f"spiral: unexpected reply {result.stdout[:200]}", file=sys.stderr)
        return False
    return True


def main():
    runtime = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    lock = open(os.path.join(runtime, "retro-spiral.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0

    order = {ws["name"]: list(leaves(ws)) for ws in workspaces(request(4))}
    with socket.socket(socket.AF_UNIX) as events:
        events.connect(os.environ["SWAYSOCK"])
        body = b'["window"]'
        events.sendall(MAGIC + struct.pack("<II", len(body), 2) + body)
        _, response = receive(events)
        if not response.get("success"):
            raise RuntimeError("Cannot subscribe to Sway window events")
        print("retro spiral ready", flush=True)
        while True:
            _, event = receive(events)
            change = event.get("change")
            window_id = event.get("container", {}).get("id")
            if not isinstance(window_id, int):
                continue
            if change == "close":
                for ids in order.values():
                    if window_id in ids:
                        ids.remove(window_id)
                continue
            if change not in ("new", "move"):
                continue

            tree = request(4)
            workspace = next(
                (ws for ws in workspaces(tree) if window_id in set(leaves(ws))), None
            )
            if workspace is None or not is_ordinary_tiling(workspace, window_id):
                continue
            name = workspace["name"]
            present = list(leaves(workspace))
            for key, ids in order.items():
                if key != name and window_id in ids:
                    ids.remove(window_id)
            known = [item for item in order.get(name, []) if item in present and item != window_id]
            existing = [item for item in present if item != window_id]
            tail = known[-1] if known else (existing[-1] if existing else None)
            if change == "new" and tail is not None and not has_special_layout(workspace):
                direction = "horizontal" if len(existing) % 2 else "vertical"
                line = (
                    f"unmark {MARK}; "
                    f"[con_id={tail}] mark --add {MARK}; "
                    f"[con_id={tail}] split {direction}; "
                    f"[con_id={window_id}] move container to mark {MARK}; "
                    f"unmark {MARK}"
                )
                command(line)
            order[name] = known + [item for item in existing if item not in known] + [window_id]


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (EOFError, OSError, RuntimeError, ValueError) as exc:
        print(f"spiral: {exc}", file=sys.stderr)
        sys.exit(1)
