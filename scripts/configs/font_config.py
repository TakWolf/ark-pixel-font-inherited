import datetime
import os
import tomllib
from typing import Final

from scripts import configs
from scripts.configs import path_define


class LayoutParam:
    def __init__(self, config_data: dict):
        self.ascent: int = config_data['ascent']
        self.descent: int = config_data['descent']
        self.x_height: int = config_data['x_height']
        self.cap_height: int = config_data['cap_height']

    @property
    def line_height(self) -> int:
        return self.ascent - self.descent


class FontConfig:
    VERSION: Final[str] = datetime.datetime.now(datetime.UTC).strftime("%Y.%m.%d")
    FAMILY_NAME: Final[str] = 'Ark Pixel Inherited'
    OUTPUTS_NAME: Final[str] = 'ark-pixel-inherited'
    ZIP_OUTPUTS_NAME: Final[str] = 'ark-pixel-font-inherited'
    MANUFACTURER: Final[str] = 'TakWolf'
    DESIGNER: Final[str] = 'TakWolf'
    DESCRIPTION: Final[str] = 'Open source Pan-CJK pixel font.'
    COPYRIGHT_INFO: Final[str] = "Copyright (c) 2023, TakWolf (https://takwolf.com), with Reserved Font Name 'Ark Pixel Inherited'."
    LICENSE_INFO: Final[str] = 'This Font Software is licensed under the SIL Open Font License, Version 1.1.'
    VENDOR_URL: Final[str] = 'https://ark-pixel-font-inherited.takwolf.com'
    DESIGNER_URL: Final[str] = 'https://takwolf.com'
    LICENSE_URL: Final[str] = 'https://openfontlicense.org'

    def __init__(self, size: int):
        config_file_path = os.path.join(path_define.ark_pixel_glyphs_dir, str(size), 'config.toml')
        if not os.path.exists(config_file_path):
            self.size = size
            return
        with open(config_file_path, 'rb') as file:
            config_data: dict = tomllib.load(file)['font']

        self.size: int = config_data['size']
        assert self.size == size, f'Font Config size not equals: expect {size} but actually {self.size}'

        self._width_mode_to_layout_param: dict[str, LayoutParam] = {}
        for width_mode in configs.width_modes:
            layout_param = LayoutParam(config_data[width_mode])
            assert (layout_param.line_height - self.size) % 2 == 0, f"Font Layout Params {self.size} {width_mode}: the difference between 'line_height' and 'size' must be a multiple of 2"
            self._width_mode_to_layout_param[width_mode] = layout_param

        self.demo_html_file_name = f'demo-{self.size}px.html'
        self.preview_image_file_name = f'preview-{self.size}px.png'

    @property
    def line_height(self) -> int:
        return self._width_mode_to_layout_param['proportional'].line_height

    def get_layout_param(self, width_mode: str) -> LayoutParam:
        return self._width_mode_to_layout_param[width_mode]

    def get_font_file_name(self, width_mode: str, font_format: str) -> str:
        return f'{FontConfig.OUTPUTS_NAME}-{self.size}px-{width_mode}.{font_format}'

    def get_info_file_name(self, width_mode: str) -> str:
        return f'font-info-{self.size}px-{width_mode}.md'

    def get_alphabet_txt_file_name(self, width_mode: str) -> str:
        return f'alphabet-{self.size}px-{width_mode}.txt'

    def get_release_zip_file_name(self, width_mode: str, font_format: str) -> str:
        return f'{FontConfig.ZIP_OUTPUTS_NAME}-{self.size}px-{width_mode}-{font_format}-v{FontConfig.VERSION}.zip'

    def get_alphabet_html_file_name(self, width_mode: str) -> str:
        return f'alphabet-{self.size}px-{width_mode}.html'
