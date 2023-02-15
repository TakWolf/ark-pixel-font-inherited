import logging

import configs
from configs import path_define
from services import design_service
from utils import fs_util

logging.basicConfig(level=logging.DEBUG)


def main():
    fs_util.delete_dir(path_define.build_dir)

    for font_config in configs.font_configs:
        design_service.classify_patch_glyph_files(font_config)
        design_service.verify_patch_glyph_files(font_config)
        alphabet_group, glyph_file_paths_group = design_service.collect_glyph_files(font_config)
        for width_mode in configs.width_modes:
            alphabet = alphabet_group[width_mode]
            glyph_file_paths = glyph_file_paths_group[width_mode]


if __name__ == '__main__':
    main()
