from pixel_font_knife import glyph_mapping_util

from tools.configs import path_define, options


def format_mappings():
    for file_path in path_define.mappings_dir.iterdir():
        if file_path.suffix != '.yml':
            continue

        mapping = glyph_mapping_util.load_mapping(file_path)
        glyph_mapping_util.save_mapping(mapping, file_path, options.language_flavors)
