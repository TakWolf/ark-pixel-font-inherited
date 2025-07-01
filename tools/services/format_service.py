from pixel_font_knife import glyph_mapping_util

from tools.configs import path_define


def format_inherited_mapping():
    file_path = path_define.mappings_dir.joinpath('Inherited.yml')
    mapping = glyph_mapping_util.load_mapping(file_path)
    glyph_mapping_util.save_mapping(mapping, file_path)
