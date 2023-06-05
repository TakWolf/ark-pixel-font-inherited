import logging

import configs
from configs import path_define
from services import design_service, font_service, publish_service, info_service, template_service, image_service
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
            font_service.make_fonts(font_config, width_mode, alphabet, glyph_file_paths)
            info_service.make_info_file(font_config, width_mode, alphabet)
            info_service.make_alphabet_txt_file(font_config, width_mode, alphabet)
            publish_service.make_release_zips(font_config, width_mode)
            template_service.make_alphabet_html_file(font_config, width_mode, alphabet)
        template_service.make_demo_html_file(font_config, alphabet_group)
        image_service.make_preview_image_file(font_config)
    template_service.make_index_html_file()
    template_service.make_playground_html_file()


if __name__ == '__main__':
    main()
