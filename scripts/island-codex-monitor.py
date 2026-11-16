#!/usr/bin/env python3
"""Read-only Codex session monitor and informational lifecycle hook for Island.

The hook writes status and sends desktop notifications. It never returns an
approval decision, edits a conversation, or starts a model request.
"""
import argparse
import datetime as dt
import fcntl
import hashlib
import html
import json
import os
import re
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time

CODEX = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
STATE = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'omarchy/island-codex'


def needs_input(name, args):
    if name.split('__')[-1] in ('request_user_input', 'request_user_input_async') or 'elicitation' in name.lower():
        return True
    code = args if isinstance(args, str) else str(args.get('code', '')) if isinstance(args, dict) else ''
    return bool(re.search(r'\btools\.request_user_input(?:_async)?\s*\(', code))


def stamp(value):
    try:
        return int(dt.datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp() * 1000)
    except (TypeError, ValueError, AttributeError):
        return 0


def load(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix='.event-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as file:
            json.dump(value, file)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def hook(data, state=STATE, notify=True):
    sid = str(data.get('session_id', ''))
    if not sid or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in sid):
        return
    event = data.get('hook_event_name', '')
    tool = str(data.get('tool_name', ''))
    args = data.get('tool_input') or {}
    input_request = needs_input(tool, args)
    if event == 'PermissionRequest':
        status, reason = 'asking', 'approval'
    elif event == 'PreToolUse' and input_request:
        status, reason = 'asking', 'input'
    elif event in ('Stop', 'Interrupt', 'SessionEnd'):
        status, reason = 'idle', ''
    elif event == 'SessionStart':
        status, reason = 'idle', ''
    elif event in ('UserPromptSubmit', 'PreToolUse', 'PostToolUse'):
        status, reason = 'working', ''
    else:
        return
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = state / (sid + '.json')
    with (state / (sid + '.lock')).open('a') as guard:
        fcntl.flock(guard, fcntl.LOCK_EX)
        previous = load(target)
        fingerprint = hashlib.sha256(json.dumps(args, sort_keys=True).encode()).hexdigest()[:16]
        notice = ':'.join([str(data.get('turn_id', '')), str(data.get('tool_use_id', '')), reason, fingerprint])
        row = {'id': sid, 'state': status, 'reason': reason,
               'updatedAt': int(data.get('event_timestamp_ms') or time.time() * 1000),
               'lastNotice': previous.get('lastNotice', ''),
               'lastNoticeAt': previous.get('lastNoticeAt', 0),
               'lastNoticeReason': previous.get('lastNoticeReason', '')}
        if status != 'asking' and previous.get('notificationId'):
            try:
                subprocess.run(['gdbus', 'call', '--session', '--dest', 'org.freedesktop.Notifications',
                                '--object-path', '/org/freedesktop/Notifications', '--method',
                                'org.freedesktop.Notifications.CloseNotification', str(previous['notificationId'])],
                               timeout=1, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (OSError, subprocess.TimeoutExpired):
                pass
        elif previous.get('notificationId'):
            row['notificationId'] = previous['notificationId']
        recent = reason == row['lastNoticeReason'] and time.time() * 1000 - row['lastNoticeAt'] < 3000
        if status == 'asking' and notice != row['lastNotice'] and not recent:
            row['lastNotice'] = notice
            row['lastNoticeAt'] = int(time.time() * 1000)
            row['lastNoticeReason'] = reason
            if notify:
                project = Path(str(data.get('cwd') or str(Path.home()))).name
                title = 'Codex needs approval' if reason == 'approval' else 'Codex needs your input'
                body = html.escape(project) + ' · Session ' + sid[-8:]
                try:
                    sent = subprocess.run(['notify-send', '-p', '-a', 'Codex', '-u', 'normal', '-t', '10000',
                                           '-h', 'string:x-island-codex-thread:' + sid, title, body],
                                          timeout=1, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                    if isinstance(sent.stdout, str) and sent.stdout.strip().isdigit():
                        row['notificationId'] = int(sent.stdout.strip())
                except (OSError, subprocess.TimeoutExpired):
                    pass
        save(target, row)


def held_threads(root=CODEX):
    """Ignore abandoned lock files; show only sessions held by live writers."""
    result = []
    for path in (root / 'thread-writer-locks').glob('*.lock'):
        if path.name.startswith('.'):
            continue
        try:
            with path.open('rb') as file:
                try:
                    fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(file, fcntl.LOCK_UN)
                except BlockingIOError:
                    result.append(path.stem)
        except OSError:
            pass
    return result


class Session:
    def __init__(self, sid, path, on_attention=None):
        self.id, self.path, self.offset = sid, Path(path), 0
        self.state, self.reason, self.started, self.completed, self.lifecycle = 'idle', '', 0, 0, 0
        self.pending = set()
        self.async_pending = set()
        self.on_attention = on_attention
        self.watch_started = int(time.time() * 1000)

    def take(self, row):
        body = row.get('payload') or {}
        now = stamp(row.get('timestamp'))
        if row.get('type') == 'event_msg':
            kind = body.get('type')
            if kind == 'task_started':
                self.state, self.reason = 'working', ''
                self.started, self.lifecycle = now, now
                self.pending.clear()
                self.async_pending.clear()
            elif kind in ('task_complete', 'turn_aborted'):
                self.state, self.reason = 'idle', ''
                self.completed, self.lifecycle = now, now
                self.pending.clear()
                self.async_pending.clear()
        elif row.get('type') == 'response_item':
            kind = body.get('type')
            if kind == 'message' and body.get('role') == 'user' and self.pending:
                content = body.get('content', [])
                text = ' '.join(str(part.get('text', '')) for part in content if isinstance(part, dict)) if isinstance(content, list) else str(content)
                if 'send_user_message_question_reply' in text or (text.strip() and not text.lstrip().startswith('<')):
                    self.pending.clear()
                    self.async_pending.clear()
                    self.state, self.reason, self.lifecycle = 'working', '', now
            elif kind in ('function_call', 'custom_tool_call'):
                name = str(body.get('name', ''))
                code = str(body.get('input', body.get('arguments', '')))
                if needs_input(name, code):
                    call_id = body.get('call_id', '')
                    fresh = call_id not in self.pending
                    self.pending.add(call_id)
                    if 'request_user_input_async' in name or re.search(r'\btools\.request_user_input_async\s*\(', code):
                        self.async_pending.add(call_id)
                    self.state, self.reason = 'asking', 'input'
                    if fresh and self.on_attention and now >= self.watch_started:
                        self.on_attention(call_id, now)
                elif not self.pending:
                    self.state, self.reason = 'working', ''
            elif kind in ('function_call_output', 'custom_tool_call_output'):
                call = body.get('call_id', '')
                if call in self.pending:
                    # An async input tool returning "accepted" only opened the
                    # question. It did not receive the user's answer yet.
                    if call in self.async_pending and re.search(r'accepted.{0,8}true', str(body.get('output', '')), re.I):
                        return
                    self.pending.discard(call)
                    self.async_pending.discard(call)
                    if not self.pending:
                        self.state, self.reason = 'working', ''

    def read(self):
        try:
            size = self.path.stat().st_size
            if size < self.offset:
                self.offset = 0
            with self.path.open('rb') as file:
                start = self.offset or max(0, size - 2 * 1024 * 1024)
                file.seek(start)
                chunk = file.read()
                end = chunk.rfind(b'\n') + 1
                self.offset = start + end
            for line in chunk[:end].splitlines():
                try:
                    self.take(json.loads(line))
                except (ValueError, TypeError, AttributeError):
                    continue
        except OSError:
            pass

    def snapshot(self, metadata, event=None):
        status, reason = self.state, self.reason
        if event and event.get('updatedAt', 0) >= self.lifecycle:
            status, reason = event.get('state', status), event.get('reason', reason)
        return {'id': self.id, 'state': status, 'reason': reason, 'startedAt': self.started,
                'doneAt': self.completed, 'project': Path(metadata.get('cwd') or str(Path.home())).name,
                'label': str(metadata.get('name') or metadata.get('agent_nickname') or metadata.get('title') or 'Codex ' + self.id[-8:]).replace('\n', ' ')[:160],
                'agent': 'codex'}


def metadata(ids, root=CODEX):
    if not ids:
        return {}
    try:
        with sqlite3.connect('file:' + str(root / 'state_5.sqlite') + '?mode=ro', uri=True, timeout=.3) as db:
            db.row_factory = sqlite3.Row
            marks = ','.join('?' for _ in ids)
            return {row['id']: dict(row) for row in db.execute(
                'SELECT id,rollout_path,cwd,title,name,agent_nickname FROM threads WHERE id IN (' + marks + ')', ids)}
    except sqlite3.Error:
        return {}


def watch(once=False):
    readers, last = {}, None
    while True:
        ids = held_threads()
        records = metadata(ids)
        rows = []
        for sid in ids:
            record = records.get(sid, {})
            path = record.get('rollout_path')
            if not path:
                path = next((str(p) for p in (CODEX / 'sessions').rglob('*' + sid + '.jsonl')), None)
            if not path:
                continue
            if sid not in readers:
                def alert(call_id, event_time, sid=sid, cwd=record.get('cwd', str(Path.home()))):
                    hook({'session_id': sid, 'hook_event_name': 'PreToolUse',
                          'tool_name': 'request_user_input', 'tool_use_id': call_id,
                          'cwd': cwd, 'event_timestamp_ms': event_time})
                readers[sid] = Session(sid, path, on_attention=alert)
            reader = readers[sid]
            reader.read()
            rows.append(reader.snapshot(record, load(STATE / (sid + '.json'))))
        readers = {sid: reader for sid, reader in readers.items() if sid in ids}
        rank = {'asking': 0, 'working': 1, 'idle': 2}
        rows.sort(key=lambda r: (rank.get(r['state'], 3), r['label']))
        out = json.dumps({'sessions': rows}, separators=(',', ':'))
        if out != last or once:
            print(out, flush=True)
            last = out
        if once:
            return
        if os.getppid() == 1:
            return
        time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('watch', 'once', 'hook'))
    options = parser.parse_args()
    try:
        if options.mode == 'hook':
            hook(json.load(sys.stdin))
            print('{}')
        else:
            watch(options.mode == 'once')
    except (BrokenPipeError, KeyboardInterrupt):
        pass
