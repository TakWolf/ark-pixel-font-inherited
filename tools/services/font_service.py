from __future__ import annotations

import itertools
import math
from datetime import datetime

from loguru import logger
from pixel_font_builder import FontBuilder, WeightName, SerifStyle, SlantStyle, WidthStyle, Glyph
from pixel_font_builder.opentype import Flavor
from pixel_font_knife import glyph_file_util, glyph_mapping_util
from pixel_font_knife.glyph_file_util import GlyphFile, GlyphFlavorGroup
from pixel_font_knife.glyph_mapping_util import SourceFlavorGroup

from tools import configs
from tools.configs import path_define, FontSize, WidthMode, FontFormat
from tools.configs.font import FontConfig


class DesignContext:
    @staticmethod
    def load(font_config: FontConfig, mappings: list[dict[int, SourceFlavorGroup]]) -> DesignContext:
        contexts = {}
        for width_mode_dir_name in itertools.chain(['common'], configs.width_modes):
            context = glyph_file_util.load_context(path_define.ark_pixel_glyphs_dir.joinpath(str(font_config.font_size), width_mode_dir_name))
            for mapping in mappings:
                glyph_mapping_util.apply_mapping(context, mapping)
            contexts[width_mode_dir_name] = context

        glyph_files = {}
        for width_mode in configs.width_modes:
            glyph_files[width_mode] = dict(contexts['common'])
            glyph_files[width_mode].update(contexts[width_mode])

        return DesignContext(font_config, glyph_files)

    font_config: FontConfig
    _glyph_files: dict[WidthMode, dict[int, GlyphFlavorGroup]]
    _alphabet_cache: dict[str, set[str]]
    _character_mapping_cache: dict[str, dict[int, str]]
    _glyph_sequence_cache: dict[str, list[GlyphFile]]

    def __init__(
            self,
            font_config: FontConfig,
            glyph_files: dict[WidthMode, dict[int, GlyphFlavorGroup]],
    ):
        self.font_config = font_config
        self._glyph_files = glyph_files
        self._alphabet_cache = {}
        self._character_mapping_cache = {}
        self._glyph_sequence_cache = {}

    @property
    def font_size(self) -> FontSize:
        return self.font_config.font_size

    def get_alphabet(self, width_mode: WidthMode) -> set[str]:
        if width_mode in self._alphabet_cache:
            alphabet = self._alphabet_cache[width_mode]
        else:
            alphabet = {chr(code_point) for code_point in self._glyph_files[width_mode] if code_point >= 0}
            self._alphabet_cache[width_mode] = alphabet
        return alphabet

    def _get_character_mapping(self, width_mode: WidthMode) -> dict[int, str]:
        if width_mode in self._character_mapping_cache:
            character_mapping = self._character_mapping_cache[width_mode]
        else:
            character_mapping = glyph_file_util.get_character_mapping(self._glyph_files[width_mode], 'zh_tr')
            self._character_mapping_cache[width_mode] = character_mapping
        return character_mapping

    def _get_glyph_sequence(self, width_mode: WidthMode) -> list[GlyphFile]:
        if width_mode in self._glyph_sequence_cache:
            glyph_sequence = self._glyph_sequence_cache[width_mode]
        else:
            glyph_sequence = glyph_file_util.get_glyph_sequence(self._glyph_files[width_mode], ['zh_tr'])
            self._glyph_sequence_cache[width_mode] = glyph_sequence
        return glyph_sequence

    def _create_builder(self, width_mode: WidthMode) -> FontBuilder:
        layout_param = self.font_config.layout_params[width_mode]

        builder = FontBuilder()
        builder.font_metric.font_size = self.font_size
        builder.font_metric.horizontal_layout.ascent = layout_param.ascent
        builder.font_metric.horizontal_layout.descent = layout_param.descent
        builder.font_metric.vertical_layout.ascent = math.ceil(layout_param.line_height / 2)
        builder.font_metric.vertical_layout.descent = -math.floor(layout_param.line_height / 2)
        builder.font_metric.x_height = layout_param.x_height
        builder.font_metric.cap_height = layout_param.cap_height

        builder.meta_info.version = configs.version
        builder.meta_info.created_time = datetime.fromisoformat(f'{configs.version.replace('.', '-')}T00:00:00Z')
        builder.meta_info.modified_time = builder.meta_info.created_time
        builder.meta_info.family_name = f'Ark Pixel Inherited {self.font_size}px {width_mode.capitalize()}'
        builder.meta_info.weight_name = WeightName.REGULAR
        builder.meta_info.serif_style = SerifStyle.SANS_SERIF
        builder.meta_info.slant_style = SlantStyle.NORMAL
        builder.meta_info.width_style = WidthStyle(width_mode.capitalize())
        builder.meta_info.manufacturer = 'TakWolf'
        builder.meta_info.designer = 'TakWolf'
        builder.meta_info.description = 'Open source Pan-CJK pixel font'
        builder.meta_info.copyright_info = 'Copyright (c) 2023, TakWolf (https://takwolf.com), with Reserved Font Name "Ark Pixel Inherited"'
        builder.meta_info.license_info = 'This Font Software is licensed under the SIL Open Font License, Version 1.1'
        builder.meta_info.vendor_url = 'https://ark-pixel-font-inherited.takwolf.com'
        builder.meta_info.designer_url = 'https://takwolf.com'
        builder.meta_info.license_url = 'https://github.com/TakWolf/ark-pixel-font-inherited/blob/master/LICENSE-OFL'

        character_mapping = self._get_character_mapping(width_mode)
        builder.character_mapping.update(character_mapping)

        glyph_sequence = self._get_glyph_sequence(width_mode)
        for glyph_file in glyph_sequence:
            horizontal_offset_x = 0
            horizontal_offset_y = (layout_param.ascent + layout_param.descent - glyph_file.height) // 2
            vertical_offset_x = -math.ceil(glyph_file.width / 2)
            vertical_offset_y = (self.font_size - glyph_file.height) // 2 - 1
            builder.glyphs.append(Glyph(
                name=glyph_file.glyph_name,
                horizontal_offset=(horizontal_offset_x, horizontal_offset_y),
                advance_width=glyph_file.width,
                vertical_offset=(vertical_offset_x, vertical_offset_y),
                advance_height=self.font_size,
                bitmap=glyph_file.bitmap.data,
            ))

        return builder

    def make_fonts(self, width_mode: WidthMode, font_formats: list[FontFormat]):
        path_define.outputs_dir.mkdir(parents=True, exist_ok=True)

        if len(font_formats) > 0:
            builder = self._create_builder(width_mode)
            for font_format in font_formats:
                file_path = path_define.outputs_dir.joinpath(f'ark-pixel-inherited-{self.font_size}px-{width_mode}.{font_format}')
                if font_format == 'otf.woff':
                    builder.save_otf(file_path, flavor=Flavor.WOFF)
                elif font_format == 'otf.woff2':
                    builder.save_otf(file_path, flavor=Flavor.WOFF2)
                elif font_format == 'ttf.woff':
                    builder.save_ttf(file_path, flavor=Flavor.WOFF)
                elif font_format == 'ttf.woff2':
                    builder.save_ttf(file_path, flavor=Flavor.WOFF2)
                else:
                    getattr(builder, f'save_{font_format}')(file_path)
                logger.info("Make font: '{}'", file_path)
