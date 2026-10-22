"""Opt-in, fixed-resolution FSR 3.1 experiment using the existing Vulkan renderer.

The verified guest 720p patch avoids the live scene proxies used by older experiments.
This prepares an experiment; it does not establish rendering quality or performance.
"""

FLAG = 'GOW3_FSR3_1080P'
PATCH = 'Resolution Patch - 720p'


def startup_options(options, env):
    """Override only this launch's internal resolution, preserving the saved options."""
    if env.get(FLAG) != '1':
        return options
    return {**options, 'render_resolution': '720p'}


def environment(applied):
    """Select the fixed 720p -> 1080p path only after all patch sites matched."""
    if PATCH not in applied:
        raise ValueError('FSR 3.1 test stopped: the 720p resolution patch did not apply to '
                         'this game build. Disable the FSR experiment to play normally.')
    return {
        'GOW3_EXPERIMENTAL_UPSCALER': '1',
        'GOW3_UPSCALER': 'fsr3',
        'GOW3_UPSCALE_PRESET': '1',  # Quality: 1.5x per axis
        'GOW3_RENDER_RES': '1280x720',
        'GOW3_OUTPUT_RES': '1920x1080',
        'GOW3_JITTER': '1',
        'GOW3_OBJECT_MOTION': '1',
    }
