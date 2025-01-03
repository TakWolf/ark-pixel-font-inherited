from io import StringIO

from pixel_font_knife import glyph_mapping_util

from tools.configs import path_define


def format_inherited_mapping():
    file_path = path_define.mappings_dir.joinpath('Inherited.yml')
    mapping = glyph_mapping_util.load_mapping(file_path)

    buffer = StringIO()
    for code_point, source_group in sorted(mapping.items()):
        source_code_point = source_group['zh_tr'].code_point
        buffer.write('\n')
        buffer.write(f'# {chr(code_point)} <- {chr(source_code_point)}\n')
        buffer.write(f'0x{code_point:04X}:\n')
        buffer.write(f'  zh_tr: 0x{source_code_point:04X} zh_tr\n')
    file_path.write_text(buffer.getvalue(), 'utf-8')
