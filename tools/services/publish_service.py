import re
import shutil
import zipfile

from loguru import logger

from tools import configs
from tools.configs import path_define
from tools.configs.options import FontSize, WidthMode, FontFormat


def make_release_zips(font_size: FontSize, width_mode: WidthMode, font_formats: list[FontFormat]):
    path_define.releases_dir.mkdir(parents=True, exist_ok=True)

    for font_format in font_formats:
        file_path = path_define.releases_dir.joinpath(f'ark-pixel-font-inherited-{font_size}px-{width_mode}-{font_format}-v{configs.version}.zip')
        with zipfile.ZipFile(file_path, 'w') as file:
            file.write(path_define.project_root_dir.joinpath('LICENSE-OFL'), 'OFL.txt')
            font_file_name = f'ark-pixel-inherited-{font_size}px-{width_mode}.{font_format}'
            file.write(path_define.outputs_dir.joinpath(font_file_name), font_file_name)
        logger.info("Make release zip: '{}'", file_path)


def update_docs():
    path_define.docs_dir.mkdir(parents=True, exist_ok=True)

    for path_from in path_define.outputs_dir.iterdir():
        if re.match(r'info-.*px-.*\.md|preview-.*px\.png', path_from.name) is None:
            continue
        path_to = path_define.docs_dir.joinpath(path_from.name)
        shutil.copyfile(path_from, path_to)
        logger.info("Copy file: '{}' -> '{}'", path_from, path_to)
