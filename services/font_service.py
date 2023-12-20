import logging
import math
import os

import yaml
from pixel_font_builder import FontBuilder, Glyph, StyleName, SerifMode
from pixel_font_builder.opentype import Flavor

import configs
from configs import path_define, FontConfig
from utils import fs_util, glyph_util

logger = logging.getLogger('font-service')


def _load_inherited_mapping() -> dict[int, list[int]]:
    file_path = os.path.join(path_define.glyphs_dir, 'inherited-mapping.yaml')
    with open(file_path, 'rb') as file:
        return yaml.safe_load(file)


_inherited_mapping = _load_inherited_mapping()


def _parse_glyph_file_name(glyph_file_name: str) -> tuple[int, list[str]]:
    tokens = glyph_file_name.removesuffix('.png').split(' ')
    assert 1 <= len(tokens) <= 2, f"Glyph file name '{glyph_file_name}': illegal format"
    code_point = int(tokens[0], 16)
    if len(tokens) == 2:
        language_flavors = tokens[1].lower().split(',')
    else:
        language_flavors = []
    return code_point, language_flavors


class DesignContext:
    def __init__(self, registry: dict[str, dict[int, dict[str, tuple[str, str]]]]):
        self._registry = registry
        self._sequence_cacher: dict[str, list[int]] = {}
        self._alphabet_cacher: dict[str, set[str]] = {}
        self._character_mapping_cacher: dict[str, dict[int, str]] = {}
        self._glyph_file_infos_cacher: dict[str, list[tuple[str, str]]] = {}
        self._glyph_data_cacher: dict[str, tuple[list[list[int]], int, int]] = {}

    def get_sequence(self, width_mode: str) -> list[int]:
        if width_mode in self._sequence_cacher:
            sequence = self._sequence_cacher[width_mode]
        else:
            sequence = list(self._registry[width_mode].keys())
            sequence.sort()
            self._sequence_cacher[width_mode] = sequence
        return sequence

    def get_alphabet(self, width_mode: str) -> set[str]:
        if width_mode in self._alphabet_cacher:
            alphabet = self._alphabet_cacher[width_mode]
        else:
            alphabet = set()
            for code_point in self._registry[width_mode]:
                if code_point < 0:
                    continue
                alphabet.add(chr(code_point))
            self._alphabet_cacher[width_mode] = alphabet
        return alphabet

    def get_character_mapping(self, width_mode: str) -> dict[int, str]:
        if width_mode in self._character_mapping_cacher:
            character_mapping = self._character_mapping_cacher[width_mode]
        else:
            character_mapping = {}
            for code_point, glyph_source in self._registry[width_mode].items():
                if code_point < 0:
                    continue
                character_mapping[code_point] = glyph_source.get('zh_tr', glyph_source['default'])[0]
            self._character_mapping_cacher[width_mode] = character_mapping
        return character_mapping

    def get_glyph_file_infos(self, width_mode: str) -> list[tuple[str, str]]:
        if width_mode in self._glyph_file_infos_cacher:
            glyph_file_infos = self._glyph_file_infos_cacher[width_mode]
        else:
            glyph_file_infos = []
            sequence = self.get_sequence(width_mode)
            for code_point in sequence:
                glyph_source = self._registry[width_mode][code_point]
                info = glyph_source.get('zh_tr', glyph_source['default'])
                if info not in glyph_file_infos:
                    glyph_file_infos.append(info)
            self._glyph_file_infos_cacher[width_mode] = glyph_file_infos
        return glyph_file_infos

    def load_glyph_data(self, glyph_file_path: str) -> tuple[list[list[int]], int, int]:
        if glyph_file_path in self._glyph_data_cacher:
            glyph_data, glyph_width, glyph_height = self._glyph_data_cacher[glyph_file_path]
        else:
            glyph_data, glyph_width, glyph_height = glyph_util.load_glyph_data_from_png(glyph_file_path)
            self._glyph_data_cacher[glyph_file_path] = glyph_data, glyph_width, glyph_height
            logger.info("Load glyph file: '%s'", glyph_file_path)
        return glyph_data, glyph_width, glyph_height


def collect_glyph_files(font_config: FontConfig) -> DesignContext:
    root_dir = os.path.join(path_define.ark_pixel_glyphs_dir, str(font_config.size))

    cellar = {}
    for width_mode_dir_name in configs.width_mode_dir_names:
        cellar[width_mode_dir_name] = {}
        width_mode_dir = os.path.join(root_dir, width_mode_dir_name)
        for glyph_file_dir, _, glyph_file_names in os.walk(width_mode_dir):
            for glyph_file_name in glyph_file_names:
                if not glyph_file_name.endswith('.png'):
                    continue
                glyph_file_path = os.path.join(glyph_file_dir, glyph_file_name)
                if glyph_file_name == 'notdef.png':
                    code_point = -1
                    language_flavors = []
                    glyph_name = '.notdef'
                else:
                    code_point, language_flavors = _parse_glyph_file_name(glyph_file_name)
                    glyph_name = f'uni{code_point:04X}'
                if code_point not in cellar[width_mode_dir_name]:
                    cellar[width_mode_dir_name][code_point] = {}
                if len(language_flavors) > 0:
                    glyph_name = f'{glyph_name}-{language_flavors[0]}'
                else:
                    language_flavors.append('default')
                for language_flavor in language_flavors:
                    assert language_flavor not in cellar[width_mode_dir_name][code_point], f"Glyph flavor already exists: '{code_point:04X}' '{width_mode_dir_name}.{language_flavor}'"
                    cellar[width_mode_dir_name][code_point][language_flavor] = glyph_name, glyph_file_path
        for code_point, glyph_source in cellar[width_mode_dir_name].items():
            assert 'default' in glyph_source, f"Glyph miss default flavor: '{code_point:04X}' '{width_mode_dir_name}'"

    registry = {}
    for width_mode in configs.width_modes:
        registry[width_mode] = dict(cellar['common'])
        registry[width_mode].update(cellar[width_mode])

        for target, code_points in _inherited_mapping.items():
            if target not in registry[width_mode]:
                continue
            glyph_source = registry[width_mode][target]
            for code_point in code_points:
                registry[width_mode][code_point] = glyph_source

    return DesignContext(registry)


def _create_builder(font_config: FontConfig, context: DesignContext, width_mode: str) -> FontBuilder:
    builder = FontBuilder(font_config.size)

    builder.meta_infos.version = FontConfig.VERSION
    builder.meta_infos.family_name = f'{FontConfig.FAMILY_NAME} {font_config.size}px {width_mode.capitalize()}'
    builder.meta_infos.style_name = StyleName.REGULAR
    builder.meta_infos.serif_mode = SerifMode.SANS_SERIF
    builder.meta_infos.width_mode = width_mode.capitalize()
    builder.meta_infos.manufacturer = FontConfig.MANUFACTURER
    builder.meta_infos.designer = FontConfig.DESIGNER
    builder.meta_infos.description = FontConfig.DESCRIPTION
    builder.meta_infos.copyright_info = FontConfig.COPYRIGHT_INFO
    builder.meta_infos.license_info = FontConfig.LICENSE_INFO
    builder.meta_infos.vendor_url = FontConfig.VENDOR_URL
    builder.meta_infos.designer_url = FontConfig.DESIGNER_URL
    builder.meta_infos.license_url = FontConfig.LICENSE_URL

    layout_params = font_config.get_layout_params(width_mode)

    builder.horizontal_header.ascent = layout_params.ascent
    builder.horizontal_header.descent = layout_params.descent

    builder.vertical_header.ascent = layout_params.ascent
    builder.vertical_header.descent = layout_params.descent

    builder.properties.x_height = layout_params.x_height
    builder.properties.cap_height = layout_params.cap_height

    character_mapping = context.get_character_mapping(width_mode)
    builder.character_mapping.update(character_mapping)

    glyph_file_infos = context.get_glyph_file_infos(width_mode)
    for glyph_name, glyph_file_path in glyph_file_infos:
        glyph_data, glyph_width, glyph_height = context.load_glyph_data(glyph_file_path)
        horizontal_origin_y = math.floor((layout_params.ascent + layout_params.descent - glyph_height) / 2)
        vertical_origin_y = (glyph_height - font_config.size) // 2
        builder.glyphs.append(Glyph(
            name=glyph_name,
            advance_width=glyph_width,
            advance_height=font_config.size,
            horizontal_origin=(0, horizontal_origin_y),
            vertical_origin_y=vertical_origin_y,
            data=glyph_data,
        ))

    return builder


def make_font_files(font_config: FontConfig, context: DesignContext, width_mode: str):
    fs_util.make_dirs(path_define.outputs_dir)

    builder = _create_builder(font_config, context, width_mode)

    otf_file_path = os.path.join(path_define.outputs_dir, font_config.get_font_file_name(width_mode, 'otf'))
    builder.save_otf(otf_file_path)
    logger.info("Make font file: '%s'", otf_file_path)

    woff2_file_path = os.path.join(path_define.outputs_dir, font_config.get_font_file_name(width_mode, 'woff2'))
    builder.save_otf(woff2_file_path, flavor=Flavor.WOFF2)
    logger.info("Make font file: '%s'", woff2_file_path)

    ttf_file_path = os.path.join(path_define.outputs_dir, font_config.get_font_file_name(width_mode, 'ttf'))
    builder.save_ttf(ttf_file_path)
    logger.info("Make font file: '%s'", ttf_file_path)

    bdf_file_path = os.path.join(path_define.outputs_dir, font_config.get_font_file_name(width_mode, 'bdf'))
    builder.save_bdf(bdf_file_path)
    logger.info("Make font file: '%s'", bdf_file_path)
