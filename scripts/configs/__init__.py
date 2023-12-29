import random

from scripts.configs.font_config import FontConfig
from scripts.configs.git_deploy_config import GitDeployConfig

build_random_key = random.random()

width_modes = [
    'monospaced',
    'proportional',
]

font_formats = ['otf', 'woff2', 'ttf', 'bdf']

font_configs = [FontConfig(size) for size in [10, 12, 16]]
font_size_to_config = {font_config.size: font_config for font_config in font_configs}

git_deploy_configs = [GitDeployConfig(
    url='git@github.com:TakWolf/ark-pixel-font-inherited.git',
    remote_name='github',
    branch_name='gh-pages',
)]
