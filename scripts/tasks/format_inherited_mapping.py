import io
import os

from scripts.configs import path_define
from scripts.utils import fs_util


def main():
    file_path = os.path.join(path_define.assets_dir, 'inherited-mapping.yaml')

    mapping: dict[int, list[int]] = fs_util.read_yaml(file_path)
    output = io.StringIO()
    targets = list(mapping.keys())
    targets.sort()
    for target in targets:
        code_points = list(set(mapping[target]))
        code_points.sort()
        assert target in code_points
        output.write('\n')
        output.write(f'0x{target:04X}:  # {chr(target)}\n')
        for code_point in code_points:
            output.write(f'  - 0x{code_point:04X}  # {chr(code_point)}\n')

    fs_util.write_str(output.getvalue(), file_path)


if __name__ == '__main__':
    main()
