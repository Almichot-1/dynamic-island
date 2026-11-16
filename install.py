#!/usr/bin/env python3
"""Install the portable Island Codex profile without copying live session data."""
import argparse
import datetime
import json
from pathlib import Path
import shlex
import shutil
import subprocess

SOURCE = Path(__file__).resolve().parent
RUNTIME = ('Island.qml', 'manifest.json', 'LICENSE', 'addons', 'companion', 'components', 'services', 'views')


def install(home, hooks=False):
    config = home / '.config/omarchy'
    target = config / 'plugins/guilhermerisu.island'
    backup = config / 'backups' / ('island-codex-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    if target.is_symlink():
        raise SystemExit('The installed plugin is a symlink; use a regular plugin directory first.')
    if target.resolve() == SOURCE:
        raise SystemExit('Clone this repository outside the installed plugin directory before running install.py.')
    settings_file = config / 'island.json'
    hooks_file = home / '.codex/hooks.json'
    settings = json.loads(settings_file.read_text()) if settings_file.exists() else {}
    hook_config = json.loads(hooks_file.read_text()) if hooks and hooks_file.exists() else {}
    backup.mkdir(parents=True)
    for path in (settings_file, config / 'shell.json', hooks_file if hooks else None):
        if path and path.exists():
            shutil.copy2(path, backup / path.name)
    if target.exists():
        shutil.copytree(target, backup / 'plugin')
    target.mkdir(parents=True, exist_ok=True)
    for name in RUNTIME:
        source, dest = SOURCE / name, target / name
        if source.is_dir():
            shutil.copytree(source, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(source, dest)
    library = home / '.local/lib'
    library.mkdir(parents=True, exist_ok=True)
    for name in ('island-codex-monitor.py', 'island-open-notification.py'):
        existing = library / name
        if existing.exists():
            shutil.copy2(existing, backup / name)
        shutil.copy2(SOURCE / 'scripts' / name, existing)
    settings.update(mediaPill=True, autoHideTiling=True, autoHideFullscreen=True,
                    hoverStyle='expand', hoverExpand=True, hoverCapsules=False,
                    downloads=False, reserveSpace=False)
    settings.setdefault('addons', {}).update(agents=True, timer=False)
    settings.setdefault('addonOptions', {}).setdefault('agents', {})['agent'] = 'codex'
    settings['controlCenterZones'] = '[["controls","notifications","addon:agents"]]'
    order = settings.get('controlCenterOrder')
    if isinstance(order, str):
        settings['controlCenterOrder'] = ','.join(x for x in order.split(',') if x != 'timer.timer')
    settings_file.write_text(json.dumps(settings, indent=2) + '\n')
    if hooks:
        command = '/usr/bin/python3 ' + shlex.quote(str(library / 'island-codex-monitor.py')) + ' hook'
        entries = hook_config.setdefault('hooks', {})
        for event in ('SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PermissionRequest',
                      'PostToolUse', 'Stop', 'Interrupt', 'SessionEnd'):
            group = entries.setdefault(event, [])
            exists = any('island-codex-monitor.py' in str(h.get('command', ''))
                         for g in group for h in g.get('hooks', []))
            if not exists:
                group.append({'matcher': '*', 'hooks': [{'type': 'command', 'command': command, 'timeout': 3}]})
        hooks_file.parent.mkdir(parents=True, exist_ok=True)
        hooks_file.write_text(json.dumps(hook_config, indent=2) + '\n')
    print('Installed Island Codex. Backup:', backup)
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hooks', action='store_true', help='Add informational lifecycle hooks (requires /hooks trust)')
    parser.add_argument('--activate', action='store_true', help='Select Island and run companion setup (updates shell/menu/keybindings and restarts shell)')
    args = parser.parse_args()
    target = install(Path.home(), args.hooks)
    if args.activate:
        subprocess.run(['omarchy', 'bar', 'use', 'guilhermerisu.island'], check=True)
        subprocess.run(['bash', str(target / 'companion/install.sh')], check=True)
    else:
        print('Activate with: omarchy bar use guilhermerisu.island')
        print('Then run: bash', target / 'companion/install.sh')
