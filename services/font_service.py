import logging
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
    def __init__(self, glyphs_registry: dict[str, dict[int, dict[str, tuple[str, str]]]]):
        self._glyphs_registry = glyphs_registry
        self._alphabet_cacher: dict[str, set[str]] = {}
        self._character_mapping_cacher: dict[str, dict[int, str]] = {}
        self._glyph_file_paths_cacher: dict[str, dict[str, str]] = {}
        self._glyph_data_cacher: dict[str, tuple[list[list[int]], int, int]] = {}

    def get_alphabet(self, width_mode: str) -> set[str]:
        if width_mode in self._alphabet_cacher:
            alphabet = self._alphabet_cacher[width_mode]
        else:
            alphabet = set()
            for code_point in self._glyphs_registry[width_mode]:
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
            for code_point, glyph_infos in self._glyphs_registry[width_mode].items():
                if code_point < 0:
                    continue
                character_mapping[code_point] = glyph_infos.get('zh_tr', glyph_infos['default'])[0]
            self._character_mapping_cacher[width_mode] = character_mapping
        return character_mapping

    def get_glyph_file_paths(self, width_mode: str) -> dict[str, str]:
        if width_mode in self._glyph_file_paths_cacher:
            glyph_file_paths = self._glyph_file_paths_cacher[width_mode]
        else:
            glyph_file_paths = {}
            for glyph_infos in self._glyphs_registry[width_mode].values():
                glyph_name, glyph_file_path = glyph_infos.get('zh_tr', glyph_infos['default'])
                glyph_file_paths[glyph_name] = glyph_file_path
            self._glyph_file_paths_cacher[width_mode] = glyph_file_paths
        return glyph_file_paths

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

    glyphs_cellar = {}
    for width_mode_dir_name in configs.width_mode_dir_names:
        glyphs_cellar[width_mode_dir_name] = {}
        width_mode_dir = os.path.join(root_dir, width_mode_dir_name)
        for glyph_file_dir, glyph_file_name in fs_util.walk_files(width_mode_dir):
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
            if code_point not in glyphs_cellar[width_mode_dir_name]:
                glyphs_cellar[width_mode_dir_name][code_point] = {}
            if len(language_flavors) > 0:
                glyph_name = f'{glyph_name}-{language_flavors[0]}'
            else:
                language_flavors.append('default')
            for language_flavor in language_flavors:
                assert language_flavor not in glyphs_cellar[width_mode_dir_name][code_point], f"Glyph flavor already exists: '{code_point:04X}' '{width_mode_dir_name}.{language_flavor}'"
                glyphs_cellar[width_mode_dir_name][code_point][language_flavor] = glyph_name, glyph_file_path
        for code_point, glyph_infos in glyphs_cellar[width_mode_dir_name].items():
            assert 'default' in glyph_infos, f"Glyph miss default flavor: '{code_point:04X}' '{width_mode_dir_name}'"

    glyphs_registry = {}
    for width_mode in configs.width_modes:
        glyphs_registry[width_mode] = dict(glyphs_cellar['common'])
        glyphs_registry[width_mode].update(glyphs_cellar[width_mode])

        for target, code_points in _inherited_mapping.items():
            if target not in glyphs_registry[width_mode]:
                continue
            glyph_infos = glyphs_registry[width_mode][target]
            for code_point in code_points:
                glyphs_registry[width_mode][code_point] = glyph_infos

    return DesignContext(glyphs_registry)


def _create_builder(font_config: FontConfig, context: DesignContext, width_mode: str) -> FontBuilder:
    font_attrs = font_config.get_attrs(width_mode)
    builder = FontBuilder(
        font_config.size,
        font_attrs.ascent,
        font_attrs.descent,
        font_attrs.x_height,
        font_attrs.cap_height,
    )

    character_mapping = context.get_character_mapping(width_mode)
    builder.character_mapping.update(character_mapping)

    glyph_file_paths = context.get_glyph_file_paths(width_mode)
    for glyph_name, glyph_file_path in glyph_file_paths.items():
        glyph_data, glyph_width, glyph_height = context.load_glyph_data(glyph_file_path)
        offset_y = font_attrs.box_origin_y + (glyph_height - font_config.size) // 2 - glyph_height
        builder.add_glyph(Glyph(
            name=glyph_name,
            advance_width=glyph_width,
            offset=(0, offset_y),
            data=glyph_data,
        ))

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
