import logging
import re
import shutil
import zipfile

from tools import configs
from tools.configs import path_define

logger = logging.getLogger(__name__)


def make_release_zip(font_size: int, width_mode: str, font_format: str):
    path_define.releases_dir.mkdir(parents=True, exist_ok=True)
    file_path = path_define.releases_dir.joinpath(f'ark-pixel-font-inherited-{font_size}px-{width_mode}-{font_format}-v{configs.font_version}.zip')
    with zipfile.ZipFile(file_path, 'w') as file:
        file.write(path_define.project_root_dir.joinpath('LICENSE-OFL'), 'OFL.txt')
        font_file_name = f'ark-pixel-inherited-{font_size}px-{width_mode}.{font_format}'
        file.write(path_define.outputs_dir.joinpath(font_file_name), font_file_name)
    logger.info("Make release zip: '%s'", file_path)


def update_docs():
    for file_dir, _, file_names in path_define.outputs_dir.walk():
        for file_name in file_names:
            if re.match(r'font-info-.*px-.*\.md|preview-.*px\.png', file_name) is None:
                continue
            path_from = file_dir.joinpath(file_name)
            path_to = path_define.docs_dir.joinpath(path_from.relative_to(path_define.outputs_dir))
            path_to.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path_from, path_to)
            logger.info("Copy file: '%s' -> '%s'", path_from, path_to)
