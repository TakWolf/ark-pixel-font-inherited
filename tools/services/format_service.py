from io import StringIO

import yaml

from tools.configs import path_define


def dump_inherited_mapping(mapping: dict[int, list[int]]) -> str:
    text = StringIO()
    for target, code_points in sorted(mapping.items()):
        code_points = set(code_points)
        if target in code_points:
            code_points.remove(target)
        text.write('\n')
        text.write(f'0x{target:04X}:  # {chr(target)}\n')
        for code_point in sorted(code_points):
            text.write(f'  - 0x{code_point:04X}  # {chr(code_point)}\n')
    return text.getvalue()


def format_inherited_mapping():
    file_path = path_define.assets_dir.joinpath('inherited-mapping.yml')
    text = dump_inherited_mapping(yaml.safe_load(file_path.read_text('utf-8')))
    file_path.write_text(text, 'utf-8')
