import logging
import os
import tomllib

from configs import path_define

logging.basicConfig(level=logging.DEBUG)


def main():
    file_path = os.path.join(path_define.glyphs_dir, 'mapping.toml')
    with open(file_path, 'rb') as file:
        mapping_data = tomllib.load(file)

    mapping_infos = []
    for info in mapping_data.values():
        target = info['target']
        if not isinstance(target, int):
            target = ord(target)
            info['target'] = target
        codes = info['codes']
        for i, code in enumerate(codes):
            if not isinstance(code, int):
                code = ord(code)
                codes[i] = code
        codes.sort()
        mapping_infos.append(info)
    mapping_infos.sort(key=lambda x: x['target'])

    with open(file_path, 'w', encoding='utf-8') as file:
        for info in mapping_infos:
            target = info['target']
            codes = info['codes']
            file.write('\n')
            file.write(f'[uni{target:04X}]\n')
            file.write(f'target = 0x{target:04X}  # {chr(target)}\n')
            file.write('codes = [\n')
            for code in codes:
                file.write(f'    0x{code:04X},  # {chr(code)}\n')
            file.write(']\n')


if __name__ == '__main__':
    main()
