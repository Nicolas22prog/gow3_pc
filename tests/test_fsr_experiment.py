"""Regression checks for opt-in, patch validation and restoring normal launches."""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from contextlib import ExitStack, redirect_stdout, redirect_stderr
from io import StringIO
from types import SimpleNamespace

from paths import ROOT
import fsr_experiment as fsr
import graphics_options as graphics
import patches

sys.path.insert(0, str(ROOT / 'launcher'))
import gow3_launcher_win as launcher


class FsrExperimentTest(unittest.TestCase):
    def test_only_explicit_launcher_opt_in_enables_the_profile(self):
        # Old settings and inherited diagnostic flags must not opt a player in.
        with mock.patch.dict(os.environ, {fsr.FLAG: '1'}):
            for value in (False, None, '1', 'false'):
                settings = {**launcher.APP_DEFAULTS, 'experimental_upscaler': True,
                            'fsr3_1080p_test': value}
                self.assertEqual(launcher.game_environment(settings)[fsr.FLAG], '0')
            settings['fsr3_1080p_test'] = True
            self.assertEqual(launcher.game_environment(settings)[fsr.FLAG], '1')
            settings['fsr3_1080p_test'] = False
            self.assertEqual(launcher.game_environment(settings)[fsr.FLAG], '0')

    def test_test_resolution_does_not_replace_the_saved_or_normal_resolution(self):
        with tempfile.TemporaryDirectory() as folder:
            config, state = Path(folder) / 'gow3.ini', Path(folder) / 'state.json'
            saved = 'render_resolution=1440p\nengine_fps=60\nfps_limit=30\n'
            config.write_text(saved, encoding='utf-8')
            options, _ = graphics.prepare(config, state)
            experiment = fsr.startup_options(options, {fsr.FLAG: '1'})
            selected = graphics.patch_names([graphics.TEXTURE_FIX], experiment)
            self.assertIn(fsr.PATCH, selected)
            self.assertNotIn(graphics.TEXTURE_FIX, selected)
            self.assertEqual(config.read_text(encoding='utf-8'), saved)
            normal = fsr.startup_options(options, {fsr.FLAG: '0'})
            self.assertEqual(normal['render_resolution'], '1440p')
            self.assertEqual(normal['engine_fps'], '60')

    def test_requested_or_skipped_patch_does_not_enable_fixed_render_targets(self):
        with self.assertRaisesRegex(ValueError, '720p resolution patch did not apply'):
            fsr.environment(['Bug Fix - Startup Black Screen'])
        with self.assertRaises(ValueError):
            fsr.environment([])

    def test_verified_patch_selects_fixed_720p_to_1080p_not_live_proxy_scaling(self):
        env = fsr.environment([fsr.PATCH])
        self.assertEqual(env['GOW3_UPSCALER'], 'fsr3')
        self.assertEqual(env['GOW3_UPSCALE_PRESET'], '1')
        self.assertEqual(env['GOW3_RENDER_RES'], '1280x720')
        self.assertEqual(env['GOW3_OUTPUT_RES'], '1920x1080')
        self.assertEqual(env['GOW3_EXPERIMENTAL_UPSCALER'], '1')

    def test_runner_requires_current_patch_report_before_enabling_fsr(self):
        # Exercise run.py's ordering without game content or executing a GPU binary.
        spec = importlib.util.spec_from_file_location('fsr_test_runner', ROOT / 'run.py')
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        for applied in ([], [fsr.PATCH]):
            with self.subTest(applied=applied), tempfile.TemporaryDirectory() as folder:
                data = Path(folder)
                game = data / 'game'
                game.mkdir()
                (game / 'eboot.bin').touch()
                probe = data / 'probe'
                probe.touch()
                (data / 'gow3.ini').write_text('render_resolution=native\nengine_fps=60\n')
                captured = {}

                def script(name, *args, **kwargs):
                    if name == 'mods.py':
                        return str(game)
                    if name == 'patches.py':
                        self.assertIn(fsr.PATCH, os.environ['GOW3_PATCHES'])
                        self.assertNotEqual(os.environ.get('GOW3_RENDER_RES'), '1280x720')
                        (data / 'out' / 'patch_status.json').write_text(json.dumps({'applied': applied}))

                def stop_before_gpu(*args):
                    captured.update(os.environ)
                    raise RuntimeError('test reached GPU launch boundary')

                original_cwd = Path.cwd()
                try:
                    with ExitStack() as stack:
                        stack.enter_context(mock.patch.dict(os.environ, {
                            fsr.FLAG: '1', 'GOW3_GAME_DIR': str(game), 'GOW3_DATA_DIR': str(data),
                            'GOW3_PROBE': str(probe),
                        }, clear=True))
                        stack.enter_context(mock.patch.object(sys, 'argv', ['run.py']))
                        stack.enter_context(mock.patch.object(runner, 'run_script', side_effect=script))
                        stack.enter_context(mock.patch.object(runner.subprocess, 'run',
                                                             return_value=SimpleNamespace(returncode=0, stdout='')))
                        stack.enter_context(mock.patch.object(runner, 'glyph_mounts', side_effect=stop_before_gpu))
                        stack.enter_context(mock.patch.object(patches, 'game_profile_for', return_value=(
                            ['CUSA01623'], ROOT / 'patches' / 'God_of_War_III_Remastered.xml', '01.02', 'GoW3')))
                        stack.enter_context(redirect_stdout(StringIO()))
                        stack.enter_context(redirect_stderr(StringIO()))
                        with self.assertRaises(RuntimeError if applied else SystemExit):
                            runner.main()
                finally:
                    os.chdir(original_cwd)
                if applied:
                    self.assertEqual(captured['GOW3_UPSCALER'], 'fsr3')
                    self.assertEqual(captured['GOW3_RENDER_RES'], '1280x720')
                else:
                    self.assertFalse(captured)


if __name__ == '__main__':
    unittest.main()
