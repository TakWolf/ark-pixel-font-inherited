import os
import tomllib

import configs
from configs import path_define


class FontAttrs:
    def __init__(self, config_data):
        self.box_origin_y_px = config_data['box_origin_y']
        self.x_height_px = config_data['x_height']
        self.cap_height_px = config_data['cap_height']


class VerticalMetrics:
    def __init__(self, ascent, descent, x_height, cap_height):
        self.ascent = ascent
        self.descent = descent
        self.x_height = x_height
        self.cap_height = cap_height


class FontConfig:
    FAMILY_NAME = 'Ark Pixel Inherited'
    OUTPUTS_FULL_NAME = 'Ark Pixel Font Inherited'
    MANUFACTURER = 'TakWolf'
    DESIGNER = 'TakWolf'
    DESCRIPTION = 'Open source Pan-CJK pixel font.'
    COPYRIGHT_INFO = "Copyright (c) 2023, TakWolf (https://takwolf.com), with Reserved Font Name 'Ark Pixel Inherited'."
    LICENSE_INFO = 'This Font Software is licensed under the SIL Open Font License, Version 1.1.'
    VENDOR_URL = 'https://ark-pixel-font-inherited.takwolf.com'
    DESIGNER_URL = 'https://takwolf.com'
    LICENSE_URL = 'https://scripts.sil.org/OFL'

    def __init__(self, px, px_to_units=100):
        self.px = px

        config_file_path = os.path.join(path_define.ark_pixel_glyphs_dir, str(px), 'config.toml')
        if not os.path.exists(config_file_path):
            return
        with open(config_file_path, 'rb') as config_file:
            config_data = tomllib.load(config_file)['font']
        assert px == config_data['size'], config_file_path

        self.line_height_px = config_data['line_height']
        assert (self.line_height_px - px) % 2 == 0, f'font_config {px}px with incorrect line_height_px {self.line_height_px}px'
        self.monospaced_attrs = FontAttrs(config_data['monospaced'])
        self.proportional_attrs = FontAttrs(config_data['proportional'])
        self.px_to_units = px_to_units

        self.demo_html_file_name = f'demo-{px}px.html'
        self.preview_image_file_name = f'preview-{px}px.png'

    def get_name_strings(self, width_mode):
        style_name = 'Regular'
        display_name = f'{FontConfig.FAMILY_NAME} {self.px}px {width_mode}'
        unique_name = f'{FontConfig.FAMILY_NAME.replace(" ", "-")}-{self.px}px-{width_mode}-{style_name}'
        return {
            'copyright': FontConfig.COPYRIGHT_INFO,
            'familyName': display_name,
            'styleName': style_name,
            'uniqueFontIdentifier': f'{unique_name};{configs.version}',
            'fullName': display_name,
            'version': configs.version,
            'psName': unique_name,
            'designer': FontConfig.DESIGNER,
            'description': FontConfig.DESCRIPTION,
            'vendorURL': FontConfig.VENDOR_URL,
            'designerURL': FontConfig.DESIGNER_URL,
            'licenseDescription': FontConfig.LICENSE_INFO,
            'licenseInfoURL': FontConfig.LICENSE_URL,
        }

    def get_units_per_em(self):
        return self.px * self.px_to_units

    def get_box_origin_y(self, width_mode):
        if width_mode == 'monospaced':
            attrs = self.monospaced_attrs
        else:  # proportional
            attrs = self.proportional_attrs
        return attrs.box_origin_y_px * self.px_to_units

    def get_vertical_metrics(self, width_mode):
        if width_mode == 'monospaced':
            line_height_px = self.px
            attrs = self.monospaced_attrs
        else:  # proportional
            line_height_px = self.line_height_px
            attrs = self.proportional_attrs
        ascent = (attrs.box_origin_y_px + int((line_height_px - self.px) / 2)) * self.px_to_units
        descent = ascent - line_height_px * self.px_to_units
        x_height = attrs.x_height_px * self.px_to_units
        cap_height = attrs.cap_height_px * self.px_to_units
        return VerticalMetrics(ascent, descent, x_height, cap_height)

    def get_font_file_name(self, width_mode, font_format):
        return f'{FontConfig.FAMILY_NAME.lower().replace(" ", "-")}-{self.px}px-{width_mode}.{font_format}'

    def get_info_file_name(self, width_mode):
        return f'font-info-{self.px}px-{width_mode}.md'

    def get_alphabet_txt_file_name(self, width_mode):
        return f'alphabet-{self.px}px-{width_mode}.txt'

    def get_release_zip_file_name(self, width_mode, font_format):
        return f'{FontConfig.OUTPUTS_FULL_NAME.lower().replace(" ", "-")}-{self.px}px-{width_mode}-{font_format}-v{configs.version}.zip'

    def get_alphabet_html_file_name(self, width_mode):
        return f'alphabet-{self.px}px-{width_mode}.html'
