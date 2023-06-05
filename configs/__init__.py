import random

from configs import path_define, font_config
from configs.font_config import FontConfig
from configs.git_deploy_config import GitDeployConfig

build_random_key = random.random()

font_name = font_config.display_name_prefix
font_version = font_config.version

font_configs = [FontConfig(px) for px in [10, 12, 16]]
font_size_to_config = {font_config.px: font_config for font_config in font_configs}

width_modes = [
    'monospaced',
    'proportional',
]

width_mode_dir_names = [
    'common',
    'monospaced',
    'proportional',
]

font_formats = ['otf', 'woff2', 'ttf']

git_deploy_configs = [GitDeployConfig(
    url='git@github.com:TakWolf/ark-pixel-font-inherited.git',
    remote_name='github',
    branch_name='gh-pages',
)]
