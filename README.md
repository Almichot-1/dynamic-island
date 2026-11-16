# Dynamic Island

A customized [Island for Omarchy](https://github.com/Guilhermerisu/island) with live Codex sessions, actionable notifications, and media that stays available when paused.

Based on Guilherme Pimenta's Island, upstream snapshot `664295d357dc6f5d57d975afcb664e13faacec12`, with local changes by Ahmed Yassin. The upstream MIT license is retained. This is a separately maintained snapshot, not an official upstream release.

## What changed

- Every open local Codex session appears with its project and status. Click a session to focus its terminal.
- New Codex input questions trigger desktop notifications. Click an alert to focus the correct session.
- Media keeps the main pill, with a small Codex indicator beside it. Codex alerts appear separately.
- Paused media remains loaded. Hover at the top edge to reveal it and click the play/pause button in the small media panel.
- Over tiled apps, Island retracts to a small top-edge handle, expands on hover, and retracts when the pointer leaves.
- Notification history works with the older Omarchy notification fallback. Telegram's chat action stays available after a banner disappears, until the app withdraws it or the shell restarts.
- Two-finger scrolling moves panels without changing volume, microphone gain, or brightness. Panel scrolling is faster.
- The Salah Reminder tile uses a prayer icon and a separate next-prayer countdown. The Salah plugin is installed separately.
- The Codex running timer and stale Downloads activity are disabled in this profile.

## Install

Requires Omarchy with Quickshell, Python 3, `notify-send` (libnotify), `gdbus`, `jq`, and Codex installed locally. Desktop changes were exercised on Omarchy 4.0.4 and its Hyprland Lua configuration. Newer releases may need adjustments.

```sh
git clone https://github.com/Almichot-1/dynamic-island.git
cd dynamic-island
python3 install.py --activate --hooks --with-salah
```

The installer backs up the existing plugin and settings under `~/.config/omarchy/backups/`. It installs the plugin and two Python helpers, merges the profile into `island.json`, and preserves unrelated settings. `--activate` selects the bar and runs bundled companion setup, which updates shell notification/OSD configuration, adds Island menu/keybinding integration, and restarts the shell. `--with-salah` installs Salah Reminder if needed and adds its tile automatically. Omit that flag if you do not want the prayer plugin. No config-file editing is needed.

The plugin retains the identifier `guilhermerisu.island` for companion compatibility, so this installation replaces an existing upstream Island installation. Keep this checkout outside the installed plugin directory. To update, run `git pull` here and rerun the installer.

To install files before activation, omit `--activate`; the installer prints activation commands.

### Optional Codex hooks

Input-question alerts use the local session watcher without hooks. For additional informational lifecycle and approval events:

```sh
python3 install.py --hooks --activate
```

Then review and trust the new hooks with `/hooks` in Codex. This one-time Codex trust step cannot be automated; question alerts work without it. Existing unrelated hooks are preserved. The helper never approves or denies tool calls and does not start agents. Approval-event delivery depends on hook support and trust in the installed Codex version.

## How session clicks work

The watcher discovers held local thread writer locks and reads session metadata and event tails. Notification clicks map the session lock owner to its terminal process, then focus that window through Hyprland. Ended sessions do not focus an unrelated agent. This targets local terminal sessions; remote agents and multiple sessions sharing the same terminal window may need manual selection.

Notification history is stored locally in `~/.local/state/omarchy/notifications/island-history.json`. The monitor writes its own status under `~/.local/state/omarchy/island-codex/`. These files and all Codex conversations, credentials, personal settings, and desktop screenshots are excluded from this repository.

Telegram history entries whose original action is no longer available fall back to focusing Telegram. A shell restart cannot preserve a chat action owned by the old notification server.

## Checks

```sh
python3 -m unittest discover -s tests -v
omarchy-shell island.codex presentation
omarchy-shell island.visibility.eDP-1 status  # replace eDP-1 with your output
```

Tests cover session lifecycle, direct question alerts, deduplication, stale sessions, and portable installation with existing settings and hooks. Desktop checks included paused-media visibility, hover reveal/retract, session-to-terminal routing, and invoking a saved notification action after its banner disappeared.

## Credits

- Original Island: [Guilhermerisu/island](https://github.com/Guilhermerisu/island), copyright Guilherme Pimenta, MIT.
- Salah integration reads the installed [sifenfisaha/omarchy-salah-reminder](https://github.com/sifenfisaha/omarchy-salah-reminder) widget; that plugin is not bundled.
- Original documentation is retained in [README.upstream.md](README.upstream.md); optional promotional image assets are not bundled.
