import datetime
import os
from typing import Final

from scripts import configs
from scripts.configs import path_define
from scripts.utils import fs_util


class LayoutParam:
    def __init__(self, ascent: int, descent: int, x_height: int, cap_height: int):
        self.ascent = ascent
        self.descent = descent
        self.x_height = x_height
        self.cap_height = cap_height

    @property
    def line_height(self) -> int:
        return self.ascent - self.descent


class FontConfig:
    VERSION: Final[str] = '2024.05.12'
    VERSION_TIME: Final[datetime.datetime] = datetime.datetime.fromisoformat(f'{VERSION.replace('.', '-')}T00:00:00Z')
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

    @staticmethod
    def load_all() -> dict[int, 'FontConfig']:
        return {font_size: FontConfig.load(font_size) for font_size in configs.font_sizes}

    @staticmethod
    def load(font_size: int) -> 'FontConfig':
        file_path = os.path.join(path_define.glyphs_dir, str(font_size), 'config.toml')
        if not os.path.exists(file_path):
            return FontConfig(font_size, {})
        config_data = fs_util.read_toml(file_path)['font']
        assert font_size == config_data['size'], f"Config 'size' error: '{file_path}'"

        layout_params = {}
        for width_mode in configs.width_modes:
            layout_param_data = config_data[width_mode]
            layout_param = LayoutParam(
                layout_param_data['ascent'],
                layout_param_data['descent'],
                layout_param_data['x_height'],
                layout_param_data['cap_height'],
            )
            if width_mode == 'monospaced':
                assert layout_param.line_height == font_size, f"Config 'monospaced.line_height' error: '{file_path}'"
            else:
                assert (layout_param.line_height - font_size) % 2 == 0, f"Config 'proportional.line_height' error: '{file_path}'"
            layout_params[width_mode] = layout_param

        return FontConfig(font_size, layout_params)

    def __init__(self, font_size: int, layout_params: dict[str, LayoutParam]):
        self.font_size = font_size
        self.layout_params = layout_params

        self.demo_html_file_name = f'demo-{font_size}px.html'
        self.preview_image_file_name = f'preview-{font_size}px.png'

    @property
    def line_height(self) -> int:
        return self.layout_params['proportional'].line_height

    def get_font_file_name(self, width_mode: str, font_format: str) -> str:
        return f'{FontConfig.OUTPUTS_NAME}-{self.font_size}px-{width_mode}.{font_format}'

    def get_info_file_name(self, width_mode: str) -> str:
        return f'font-info-{self.font_size}px-{width_mode}.md'

    def get_alphabet_txt_file_name(self, width_mode: str) -> str:
        return f'alphabet-{self.font_size}px-{width_mode}.txt'

    def get_release_zip_file_name(self, width_mode: str, font_format: str) -> str:
        return f'{FontConfig.ZIP_OUTPUTS_NAME}-{self.font_size}px-{width_mode}-{font_format}-v{FontConfig.VERSION}.zip'

    def get_alphabet_html_file_name(self, width_mode: str) -> str:
        return f'alphabet-{self.font_size}px-{width_mode}.html'
