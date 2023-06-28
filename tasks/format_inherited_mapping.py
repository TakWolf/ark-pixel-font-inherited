import logging
import os

import yaml

from configs import path_define

logging.basicConfig(level=logging.DEBUG)


def main():
    old_file_path = os.path.join(path_define.glyphs_dir, 'inherited-mapping.yaml')
    with open(old_file_path, 'rb') as file:
        mapping: dict[int, list[int]] = yaml.safe_load(file)

    new_file_path = os.path.join(path_define.glyphs_dir, 'inherited-mapping-new.yaml')
    with open(new_file_path, 'w', encoding='utf-8') as file:
        targets = list(mapping.keys())
        targets.sort()
        for target in targets:
            code_points = list(set(mapping[target]))
            code_points.sort()
            assert target in code_points
            file.write('\n')
            file.write(f'0x{target:04X}:  # {chr(target)}\n')
            for code_point in code_points:
                file.write(f'- 0x{code_point:04X}  # {chr(code_point)}\n')

    os.remove(old_file_path)
    os.rename(new_file_path, old_file_path)


if __name__ == '__main__':
    main()
