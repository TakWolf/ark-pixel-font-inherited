import os
import time
import tomllib

from configs import path_define

display_name_prefix = 'Ark Pixel Inherited'
unique_name_prefix = 'Ark-Pixel-Inherited'
font_file_name_prefix = 'ark-pixel-inherited'
release_zip_file_name_prefix = 'ark-pixel-font-inherited'
style_name = 'Regular'
version = f'{time.strftime("%Y.%m.%d")}'
copyright_string = "Copyright (c) 2023, TakWolf (https://takwolf.com), with Reserved Font Name 'Ark Pixel Inherited'."
designer = 'TakWolf'
description = 'Open source Pan-CJK pixel font.'
vendor_url = 'https://ark-pixel-font-inherited.takwolf.com'
designer_url = 'https://takwolf.com'
license_description = 'This Font Software is licensed under the SIL Open Font License, Version 1.1.'
license_info_url = 'https://scripts.sil.org/OFL'


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
        display_name = f'{display_name_prefix} {self.px}px {width_mode}'
        unique_name = f'{unique_name_prefix}-{self.px}px-{width_mode}-{style_name}'
        return {
            'copyright': copyright_string,
            'familyName': display_name,
            'styleName': style_name,
            'uniqueFontIdentifier': f'{unique_name};{version}',
            'fullName': display_name,
            'version': version,
            'psName': unique_name,
            'designer': designer,
            'description': description,
            'vendorURL': vendor_url,
            'designerURL': designer_url,
            'licenseDescription': license_description,
            'licenseInfoURL': license_info_url,
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
        return f'{font_file_name_prefix}-{self.px}px-{width_mode}.{font_format}'

    def get_info_file_name(self, width_mode):
        return f'font-info-{self.px}px-{width_mode}.md'

    def get_alphabet_txt_file_name(self, width_mode):
        return f'alphabet-{self.px}px-{width_mode}.txt'

    def get_release_zip_file_name(self, width_mode, font_format):
        return f'{release_zip_file_name_prefix}-{self.px}px-{width_mode}-{font_format}-v{version}.zip'

    def get_alphabet_html_file_name(self, width_mode):
        return f'alphabet-{self.px}px-{width_mode}.html'
