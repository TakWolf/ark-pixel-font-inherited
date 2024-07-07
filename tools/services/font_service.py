import datetime
import itertools
import math

import yaml
from loguru import logger
from pixel_font_builder import FontBuilder, WeightName, SerifStyle, SlantStyle, WidthStyle, Glyph
from pixel_font_builder.opentype import Flavor
from pixel_font_knife import glyph_file_util
from pixel_font_knife.glyph_file_util import GlyphFile, GlyphFlavorGroup

from tools import configs
from tools.configs import path_define, WidthMode, FontFormat
from tools.configs.font import FontConfig

_inherited_mapping: dict[int, list[int]] = yaml.safe_load(path_define.assets_dir.joinpath('inherited-mapping.yml').read_bytes())


def _get_glyph_name(glyph_file: GlyphFile) -> str:
    if glyph_file.code_point == -1:
        name = '.notdef'
    else:
        name = f'{glyph_file.code_point:04X}'
    if len(glyph_file.flavors) > 0:
        name = f'{name}-{glyph_file.flavors[0]}'
    return name


class DesignContext:
    @staticmethod
    def load(font_config: FontConfig) -> 'DesignContext':
        contexts = {}
        for width_mode_dir_name in itertools.chain(['common'], configs.width_modes):
            width_mode_dir = path_define.glyphs_dir.joinpath(str(font_config.font_size), width_mode_dir_name)
            contexts[width_mode_dir_name] = glyph_file_util.load_context(width_mode_dir)

        glyph_files = {}
        for width_mode in configs.width_modes:
            glyph_files[width_mode] = dict(contexts['common'])
            glyph_files[width_mode].update(contexts[width_mode])
            for target, code_points in _inherited_mapping.items():
                if target not in glyph_files[width_mode]:
                    continue
                flavor_group = glyph_files[width_mode][target]
                for code_point in code_points:
                    glyph_files[width_mode][code_point] = flavor_group

        return DesignContext(font_config, glyph_files)

    font_config: FontConfig
    glyph_files: dict[WidthMode, dict[int, GlyphFlavorGroup]]
    _alphabet_cache: dict[str, set[str]]
    _character_mapping_cache: dict[str, dict[int, str]]
    _glyph_sequence_cache: dict[str, list[GlyphFile]]
    _builder_cache: dict[str, FontBuilder]

    def __init__(
            self,
            font_config: FontConfig,
            glyph_files: dict[WidthMode, dict[int, GlyphFlavorGroup]],
    ):
        self.font_config = font_config
        self.glyph_files = glyph_files
        self._alphabet_cache = {}
        self._character_mapping_cache = {}
        self._glyph_sequence_cache = {}
        self._builder_cache = {}

    def get_alphabet(self, width_mode: WidthMode) -> set[str]:
        if width_mode in self._alphabet_cache:
            alphabet = self._alphabet_cache[width_mode]
        else:
            alphabet = set(chr(code_point) for code_point in self.glyph_files[width_mode] if code_point >= 0)
            self._alphabet_cache[width_mode] = alphabet
        return alphabet

    def _get_character_mapping(self, width_mode: WidthMode) -> dict[int, str]:
        if width_mode in self._character_mapping_cache:
            character_mapping = self._character_mapping_cache[width_mode]
        else:
            character_mapping = {}
            for code_point, flavor_group in self.glyph_files[width_mode].items():
                if code_point < 0:
                    continue
                glyph_file = flavor_group.get_file('zh_tr', fallback_default=True)
                character_mapping[code_point] = _get_glyph_name(glyph_file)
            self._character_mapping_cache[width_mode] = character_mapping
        return character_mapping

    def _get_glyph_sequence(self, width_mode: WidthMode) -> list[GlyphFile]:
        if width_mode in self._glyph_sequence_cache:
            glyph_sequence = self._glyph_sequence_cache[width_mode]
        else:
            glyph_sequence = []
            flavor_group_sequence = sorted(self.glyph_files[width_mode].values(), key=lambda x: x.code_point)
            for flavor_group in flavor_group_sequence:
                glyph_file = flavor_group.get_file('zh_tr', fallback_default=True)
                if glyph_file not in glyph_sequence:
                    glyph_sequence.append(glyph_file)
            self._glyph_sequence_cache[width_mode] = glyph_sequence
        return glyph_sequence

    def _create_builder(self, width_mode: WidthMode) -> FontBuilder:
        layout_param = self.font_config.layout_params[width_mode]

        builder = FontBuilder()
        builder.font_metric.font_size = self.font_config.font_size
        builder.font_metric.horizontal_layout.ascent = layout_param.ascent
        builder.font_metric.horizontal_layout.descent = layout_param.descent
        builder.font_metric.vertical_layout.ascent = math.ceil(layout_param.line_height / 2)
        builder.font_metric.vertical_layout.descent = math.floor(layout_param.line_height / 2)
        builder.font_metric.x_height = layout_param.x_height
        builder.font_metric.cap_height = layout_param.cap_height

        builder.meta_info.version = configs.font_version
        builder.meta_info.created_time = datetime.datetime.fromisoformat(f'{configs.font_version.replace('.', '-')}T00:00:00Z')
        builder.meta_info.modified_time = builder.meta_info.created_time
        builder.meta_info.family_name = f'Ark Pixel Inherited {self.font_config.font_size}px {width_mode.capitalize()}'
        builder.meta_info.weight_name = WeightName.REGULAR
        builder.meta_info.serif_style = SerifStyle.SANS_SERIF
        builder.meta_info.slant_style = SlantStyle.NORMAL
        builder.meta_info.width_style = WidthStyle(width_mode.capitalize())
        builder.meta_info.manufacturer = 'TakWolf'
        builder.meta_info.designer = 'TakWolf'
        builder.meta_info.description = 'Open source Pan-CJK pixel font.'
        builder.meta_info.copyright_info = "Copyright (c) 2023, TakWolf (https://takwolf.com), with Reserved Font Name 'Ark Pixel Inherited'."
        builder.meta_info.license_info = 'This Font Software is licensed under the SIL Open Font License, Version 1.1.'
        builder.meta_info.vendor_url = 'https://ark-pixel-font-inherited.takwolf.com'
        builder.meta_info.designer_url = 'https://takwolf.com'
        builder.meta_info.license_url = 'https://openfontlicense.org'

        character_mapping = self._get_character_mapping(width_mode)
        builder.character_mapping.update(character_mapping)

        glyph_sequence = self._get_glyph_sequence(width_mode)
        for glyph_file in glyph_sequence:
            horizontal_origin_y = math.floor((layout_param.ascent + layout_param.descent - glyph_file.height) / 2)
            vertical_origin_y = (self.font_config.font_size - glyph_file.height) // 2 - 1
            builder.glyphs.append(Glyph(
                name=_get_glyph_name(glyph_file),
                advance_width=glyph_file.width,
                advance_height=self.font_config.font_size,
                horizontal_origin=(0, horizontal_origin_y),
                vertical_origin_y=vertical_origin_y,
                bitmap=glyph_file.bitmap.data,
            ))

        return builder

    def _get_builder(self, width_mode: WidthMode) -> FontBuilder:
        if width_mode in self._builder_cache:
            builder = self._builder_cache[width_mode]
        else:
            builder = self._create_builder(width_mode)
            self._builder_cache[width_mode] = builder
        return builder

    def make_font(self, width_mode: WidthMode, font_format: FontFormat):
        path_define.outputs_dir.mkdir(parents=True, exist_ok=True)
        builder = self._get_builder(width_mode)
        file_path = path_define.outputs_dir.joinpath(f'ark-pixel-inherited-{self.font_config.font_size}px-{width_mode}.{font_format}')
        if font_format == 'woff2':
            builder.save_otf(file_path, flavor=Flavor.WOFF2)
        else:
            getattr(builder, f'save_{font_format}')(file_path)
        logger.info("Make font: '{}'", file_path)
