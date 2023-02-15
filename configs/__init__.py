import os
import random
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader

from configs import path_define
from configs.git_deploy_config import GitDeployConfig
from utils.unidata_util import UnidataDB

build_random_key = random.random()

ark_pixel_config = SimpleNamespace(
    repository_name='TakWolf/ark-pixel-font',
    source_type='branch',
    source_name='master',
)

unidata_db = UnidataDB(os.path.join(path_define.unidata_dir, 'Blocks.txt'))

template_env = Environment(loader=FileSystemLoader(path_define.templates_dir))

git_deploy_configs = [GitDeployConfig(
    'git@github.com:TakWolf/ark-pixel-font-inherited.git',
    'github',
    'gh-pages',
)]
