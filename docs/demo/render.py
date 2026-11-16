#!/usr/bin/env python3
"""Render a silent 50-second walkthrough using sample data and packaged QML."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / 'docs'


def main():
    for tool in ('quickshell', 'ffmpeg'):
        if not shutil.which(tool):
            raise SystemExit('Missing dependency: ' + tool)
    launcher = ROOT / '.demo-render.qml'
    if launcher.exists():
        raise SystemExit('Remove the previous .demo-render.qml before rendering again.')
    with tempfile.TemporaryDirectory(prefix='dynamic-island-video-') as temporary:
        frames = Path(temporary)
        launcher.write_text('import QtQuick\nimport "docs/demo"\nDemo {}\n')
        env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                   ISLAND_DEMO_FRAMES=str(frames))
        # The independent offscreen instance never captures or changes the desktop.
        try:
            subprocess.run(['quickshell', '-p', str(launcher)], env=env, check=True, timeout=180)
        finally:
            launcher.unlink(missing_ok=True)
        pattern = str(frames / 'frame-%05d.png')
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                        '-framerate', '25', '-i', pattern, '-c:v', 'libx264',
                        '-preset', 'medium', '-crf', '23', '-pix_fmt', 'yuv420p',
                        '-threads', '2', '-movflags', '+faststart', '-an',
                        str(DOCS / 'dynamic-island-demo.mp4')], check=True)
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                        '-framerate', '25', '-i', pattern, '-filter_complex',
                        'setpts=0.5*PTS,fps=10,scale=880:-1:flags=lanczos,split[a][b];'
                        '[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3',
                        '-threads', '2', '-loop', '0',
                        str(DOCS / 'dynamic-island-preview.gif')], check=True)
        shutil.copy2(frames / 'frame-00075.png', DOCS / 'dynamic-island-poster.png')
    print('Created MP4, animated README preview, and poster under docs/.')


if __name__ == '__main__':
    main()
