#!/usr/bin/env python3
"""Route Island clicks to the sender's action or the owning Codex terminal."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

CODEX = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))


def run(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=4)
    except (OSError, subprocess.TimeoutExpired):
        return None


def lock_owner(path):
    try:
        stat = path.stat()
        for line in Path('/proc/locks').read_text().splitlines():
            fields = line.split()
            if len(fields) < 6 or fields[1] != 'FLOCK' or fields[3] != 'WRITE':
                continue
            major, minor, inode = fields[5].split(':')
            if (int(major, 16), int(minor, 16), int(inode)) == (os.major(stat.st_dev), os.minor(stat.st_dev), stat.st_ino):
                return int(fields[4])
            # A bind mount can expose a different device number than the
            # kernel lock table. Verify the owner's locked descriptor itself.
            if int(inode) == stat.st_ino:
                pid = int(fields[4])
                for fd in Path('/proc', str(pid), 'fd').iterdir():
                    try:
                        info = Path('/proc', str(pid), 'fdinfo', fd.name).read_text()
                        if fd.samefile(path) and 'FLOCK' in info and fields[5] in info:
                            return pid
                    except OSError:
                        continue
    except (OSError, ValueError):
        pass
    return None


def ancestors(pid):
    seen = []
    while pid and pid not in seen:
        seen.append(pid)
        try:
            status = Path('/proc', str(pid), 'status').read_text()
            pid = int(re.search(r'^PPid:\s*(\d+)', status, re.M)[1])
        except (OSError, TypeError):
            break
    return seen


def codex_window(row, clients):
    sid = str(row.get('codexThread', ''))
    # Older saved alerts included only a session suffix. Resolve it only when
    # it uniquely identifies a currently held session.
    suffix = re.search(r'\bSession ([a-zA-Z0-9_-]{8})\b', str(row.get('body', '')))
    if not sid and suffix:
        matches = [p.stem for p in (CODEX / 'thread-writer-locks').glob('*.lock')
                   if p.stem.endswith(suffix[1]) and lock_owner(p)]
        if len(matches) == 1:
            sid = matches[0]
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', sid):
        return None
    pid = lock_owner(CODEX / 'thread-writer-locks' / (sid + '.lock'))
    for parent in ancestors(pid):
        for client in clients:
            if client.get('pid') == parent:
                return client
    return None


def focus(client):
    address = str(client.get('address', ''))
    if not re.fullmatch(r'0x[0-9a-fA-F]+', address):
        return False
    result = run(['hyprctl', 'dispatch', 'hl.dsp.focus({ window = "address:' + address + '" })'])
    if result and result.returncode == 0:
        return True
    result = run(['hyprctl', 'dispatch', 'focuswindow', 'address:' + address])
    return bool(result and result.returncode == 0)


def open_notification(row):
    result = run(['hyprctl', 'clients', '-j'])
    try:
        clients = json.loads(result.stdout) if result and result.returncode == 0 else []
    except ValueError:
        clients = []
    if row.get('app') == 'Codex':
        window = codex_window(row, clients)
        # Never focus a different Codex session when the original has ended.
        return bool(window and focus(window))
    key = str(row.get('key', ''))
    if key:
        result = run(['omarchy-shell', 'island-notifications', 'invokeKey', key])
        if result and result.returncode == 0 and result.stdout.strip() == 'ok':
            return True
    # The sender may have withdrawn the notification, or the shell restarted.
    def normalize(value):
        return re.sub(r'[^a-z0-9]', '', str(value).lower())
    identities = [normalize(row.get(k, '')) for k in ('desktopEntry', 'app')]
    for identity in identities:
        if not identity:
            continue
        for client in clients:
            if any(identity in normalize(client.get(k, '')) for k in ('class', 'initialClass')):
                return focus(client)
    return False


if __name__ == '__main__':
    try:
        success = open_notification(json.loads(sys.argv[1]))
    except (ValueError, IndexError):
        success = False
    sys.exit(0 if success else 1)
