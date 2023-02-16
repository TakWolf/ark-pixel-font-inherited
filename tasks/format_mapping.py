import logging
import os
import tomllib

from configs import path_define

logging.basicConfig(level=logging.DEBUG)


def main():
    mapping_file_path = os.path.join(path_define.glyphs_dir, 'mapping.toml')
    with open(mapping_file_path, 'rb') as file:
        mapping_infos = list(tomllib.load(file).items())
        mapping_infos.sort()
    with open(mapping_file_path, 'w', encoding='utf-8') as file:
        for _, info in mapping_infos:
            source = info['source']
            target = info['target']
            codes = info['codes']
            file.write('\n')
            file.write(f'[uni{source:04X}]\n')
            file.write(f'source = 0x{source:04X}  # {chr(source)}\n')
            file.write(f'target = 0x{target:04X}  # {chr(target)}\n')
            file.write('codes = [\n')
            for code in codes:
                file.write(f'    0x{code:04X},  # {chr(code)}\n')
            file.write(']\n')


if __name__ == '__main__':
    main()
