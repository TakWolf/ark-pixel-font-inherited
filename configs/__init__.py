import os
import random
from types import SimpleNamespace

from configs import path_define
from utils.unidata_util import UnidataDB

build_random_key = random.random()

ark_pixel_config = SimpleNamespace(
    repository_name='TakWolf/ark-pixel-font',
    source_type='branch',
    source_name='master',
)

unidata_db = UnidataDB(os.path.join(path_define.unidata_dir, 'Blocks.txt'))
