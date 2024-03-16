import io
import os

from scripts.configs import path_define
from scripts.utils import fs_util


def main():
    old_file_path = os.path.join(path_define.glyphs_dir, 'inherited-mapping.yaml')
    mapping: dict[int, list[int]] = fs_util.read_yaml(old_file_path)

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

    new_file_path = os.path.join(path_define.glyphs_dir, 'inherited-mapping-new.yaml')
    fs_util.write_str(output.getvalue(), new_file_path)

    os.remove(old_file_path)
    os.rename(new_file_path, old_file_path)


if __name__ == '__main__':
    main()
