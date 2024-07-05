from typing import Literal, get_args

font_version = '2024.05.12'

type FontSize = Literal[10, 12, 16]
font_sizes = list[FontSize](get_args(FontSize.__value__))

type WidthMode = Literal[
    'monospaced',
    'proportional',
]
width_modes = list[WidthMode](get_args(WidthMode.__value__))

type FontFormat = Literal['otf', 'woff2', 'ttf', 'bdf', 'pcf']
font_formats = list[FontFormat](get_args(FontFormat.__value__))
