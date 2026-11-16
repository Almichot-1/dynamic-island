import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('installer', Path(__file__).resolve().parents[1] / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTest(unittest.TestCase):
    def test_portable_install_preserves_settings_and_unrelated_hooks(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            settings = home / '.config/omarchy/island.json'
            settings.parent.mkdir(parents=True)
            settings.write_text(json.dumps({'clock24h': False, 'addons': {'weather': True}}))
            hooks = home / '.codex/hooks.json'
            hooks.parent.mkdir()
            hooks.write_text(json.dumps({'hooks': {'Stop': [{'hooks': [{'command': 'existing-hook'}]}]}}))
            installer.install(home, hooks=True)
            installer.install(home, hooks=True)
            profile = json.loads(settings.read_text())
            self.assertFalse(profile['clock24h'])
            self.assertTrue(profile['addons']['weather'])
            self.assertTrue(profile['addons']['agents'])
            stop = json.loads(hooks.read_text())['hooks']['Stop']
            self.assertEqual(len(stop), 2)
            self.assertEqual(stop[0]['hooks'][0]['command'], 'existing-hook')
            self.assertIn(str(home), stop[1]['hooks'][0]['command'])
            self.assertTrue((home / '.local/lib/island-codex-monitor.py').exists())
            self.assertFalse((home / '.config/omarchy/plugins/guilhermerisu.island/.git').exists())


if __name__ == '__main__':
    unittest.main()
