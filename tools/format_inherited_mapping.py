from tools.configs import path_define
from tools.utils import fs_util


def main():
    file_path = path_define.assets_dir.joinpath('inherited-mapping.yaml')
    mapping: dict[int, list[int]] = fs_util.read_yaml(file_path)

    with file_path.open('w', encoding='utf-8') as file:
        for target, code_points in sorted(mapping.items()):
            code_points = set(code_points)
            if target in code_points:
                code_points.remove(target)
            file.write('\n')
            file.write(f'0x{target:04X}:  # {chr(target)}\n')
            for code_point in sorted(code_points):
                file.write(f'  - 0x{code_point:04X}  # {chr(code_point)}\n')


if __name__ == '__main__':
    main()
