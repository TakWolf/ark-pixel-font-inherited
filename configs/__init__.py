import os
import random
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader

from configs import path_define, font_config
from configs.font_config import FontConfig
from configs.git_deploy_config import GitDeployConfig
from utils.unidata_util import UnidataDB

build_random_key = random.random()

ark_pixel_config = SimpleNamespace(
    repository_name='TakWolf/ark-pixel-font',
    source_type='branch',
    source_name='master',
)

font_name = font_config.display_name_prefix
font_version = font_config.version

font_configs = [FontConfig(px) for px in [10, 12, 16]]
font_config_map = {font_config.px: font_config for font_config in font_configs}

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

unidata_db = UnidataDB(os.path.join(path_define.unidata_dir, 'Blocks.txt'))

template_env = Environment(loader=FileSystemLoader(path_define.templates_dir))

git_deploy_configs = [GitDeployConfig(
    'git@github.com:TakWolf/ark-pixel-font-inherited.git',
    'github',
    'gh-pages',
)]
