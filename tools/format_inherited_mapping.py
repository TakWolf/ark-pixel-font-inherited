from io import StringIO

from tools.configs import path_define
from tools.utils import fs_util


def main():
    file_path = path_define.assets_dir.joinpath('inherited-mapping.yaml')

    mapping: dict[int, list[int]] = fs_util.read_yaml(file_path)
    output = StringIO()
    for target, code_points in sorted(mapping.items()):
        code_points = sorted(set(code_points))
        assert target in code_points
        output.write('\n')
        output.write(f'0x{target:04X}:  # {chr(target)}\n')
        for code_point in code_points:
            output.write(f'  - 0x{code_point:04X}  # {chr(code_point)}\n')

    file_path.write_text(output.getvalue(), 'utf-8')


if __name__ == '__main__':
    main()
