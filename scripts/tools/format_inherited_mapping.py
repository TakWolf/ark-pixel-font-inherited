from io import StringIO

from scripts.configs import path_define
from scripts.utils import fs_util


def main():
    file_path = path_define.assets_dir.joinpath('inherited-mapping.yaml')

    mapping: dict[int, list[int]] = fs_util.read_yaml(file_path)
    output = StringIO()
    targets = list(mapping)
    targets.sort()
    for target in targets:
        code_points = list(set(mapping[target]))
        code_points.sort()
        assert target in code_points
        output.write('\n')
        output.write(f'0x{target:04X}:  # {chr(target)}\n')
        for code_point in code_points:
            output.write(f'  - 0x{code_point:04X}  # {chr(code_point)}\n')

    file_path.write_text(output.getvalue(), 'utf-8')


if __name__ == '__main__':
    main()
