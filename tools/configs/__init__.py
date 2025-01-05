from typing import Literal, get_args

from tools.configs import path_define

version = '2025.01.06'

type FontSize = Literal[10, 12, 16]
font_sizes = list[FontSize](get_args(FontSize.__value__))

type WidthMode = Literal[
    'monospaced',
    'proportional',
]
width_modes = list[WidthMode](get_args(WidthMode.__value__))

type FontFormat = Literal['otf', 'ttf', 'woff2', 'bdf', 'pcf']
font_formats = list[FontFormat](get_args(FontFormat.__value__))

type Attachment = Literal[
    'release',
    'info',
    'alphabet',
    'html',
    'image',
]
attachments = list[Attachment](get_args(Attachment.__value__))

mapping_file_paths = [
    path_define.ark_pixel_mappings_dir.joinpath('2700-27BF Dingbats.yml'),
    path_define.ark_pixel_mappings_dir.joinpath('2E80-2EFF CJK Radicals Supplement.yml'),
    path_define.ark_pixel_mappings_dir.joinpath('2F00-2FDF Kangxi Radicals.yml'),
    path_define.mappings_dir.joinpath('Inherited.yml'),
]
