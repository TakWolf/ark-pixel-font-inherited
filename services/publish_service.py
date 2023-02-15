import logging
import os
import zipfile

import configs
from configs import path_define
from utils import fs_util

logger = logging.getLogger('publish-service')


def make_release_zips(font_config, width_mode, font_formats=None):
    if font_formats is None:
        font_formats = configs.font_formats

    fs_util.make_dirs_if_not_exists(path_define.releases_dir)
    for font_format in font_formats:
        zip_file_path = os.path.join(path_define.releases_dir, font_config.get_release_zip_file_name(width_mode, font_format))
        with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
            zip_file.write('LICENSE-OFL', 'OFL.txt')
            font_file_name = font_config.get_font_file_name(width_mode, font_format)
            font_file_path = os.path.join(path_define.outputs_dir, font_file_name)
            zip_file.write(font_file_path, font_file_name)
        logger.info(f'make {zip_file_path}')
