import random
import time

from configs.font_config import FontConfig
from configs.git_deploy_config import GitDeployConfig

build_random_key = random.random()

version = f'{time.strftime("%Y.%m.%d")}'

font_configs = [FontConfig(size) for size in [10, 12, 16]]
font_size_to_config: dict[int, FontConfig] = {font_config.size: font_config for font_config in font_configs}

width_modes = [
    'monospaced',
    'proportional',
]

width_mode_dir_names = [
    'common',
    'monospaced',
    'proportional',
]

font_formats = ['otf', 'woff2', 'ttf', 'bdf']

git_deploy_configs = [GitDeployConfig(
    url='git@github.com:TakWolf/ark-pixel-font-inherited.git',
    remote_name='github',
    branch_name='gh-pages',
)]
