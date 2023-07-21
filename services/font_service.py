import logging
import os

import yaml
from pixel_font_builder import FontBuilder, Glyph, StyleName, SerifMode

import configs
from configs import path_define, FontConfig
from utils import fs_util, glyph_util

logger = logging.getLogger('font-service')


def _load_inherited_mapping() -> dict[int, list[int]]:
    file_path = os.path.join(path_define.glyphs_dir, 'inherited-mapping.yaml')
    with open(file_path, 'rb') as file:
        return yaml.safe_load(file)


_inherited_mapping = _load_inherited_mapping()


def _parse_glyph_file_name(glyph_file_name: str) -> tuple[str, list[str]]:
    tokens = glyph_file_name.removesuffix('.png').split(' ')
    assert 1 <= len(tokens) <= 2, f"Glyph file name '{glyph_file_name}': illegal format"
    hex_name = tokens[0].upper()
    if len(tokens) == 2:
        language_flavors = tokens[1].lower().split(',')
    else:
        language_flavors = list[str]()
    return hex_name, language_flavors


class DesignContext:
    def __init__(
            self,
            character_mapping_group: dict[str, dict[int, str]],
            glyph_file_paths_group: dict[str, dict[str, str]],
    ):
        self._character_mapping_group = character_mapping_group
        self._glyph_file_paths_group = glyph_file_paths_group
        self._glyph_data_pool = dict[str, tuple[list[list[int]], int, int]]()

    def get_character_mapping(self, width_mode: str) -> dict[int, str]:
        return self._character_mapping_group[width_mode]

    def get_alphabet(self, width_mode: str) -> list[str]:
        character_mapping = self.get_character_mapping(width_mode)
        alphabet = [chr(code_point) for code_point in character_mapping]
        alphabet.sort()
        return alphabet

    def get_glyph_file_paths(self, width_mode: str) -> dict[str, str]:
        return self._glyph_file_paths_group[width_mode]

    def load_glyph_data(self, glyph_file_path: str) -> tuple[list[list[int]], int, int]:
        if glyph_file_path in self._glyph_data_pool:
            glyph_data, glyph_width, glyph_height = self._glyph_data_pool[glyph_file_path]
        else:
            glyph_data, glyph_width, glyph_height = glyph_util.load_glyph_data_from_png(glyph_file_path)
            self._glyph_data_pool[glyph_file_path] = glyph_data, glyph_width, glyph_height
            logger.info("Load glyph file: '%s'", glyph_file_path)
        return glyph_data, glyph_width, glyph_height


def collect_glyph_files(font_config: FontConfig) -> DesignContext:
    character_mapping_group = dict[str, dict[int, str]]()
    glyph_file_paths_group = dict[str, dict[str, str]]()
    for width_mode in configs.width_modes:
        character_mapping_group[width_mode] = {}
        glyph_file_paths_group[width_mode] = {}

    root_dir = os.path.join(path_define.ark_pixel_glyphs_dir, str(font_config.size))
    glyph_file_paths_cellar = dict[str, dict[str, dict[str, str]]]()
    for width_mode_dir_name in configs.width_mode_dir_names:
        glyph_file_paths_cellar[width_mode_dir_name] = {
            'default': {},
            'zh_tr': {},
        }

        width_mode_dir = os.path.join(root_dir, width_mode_dir_name)
        for glyph_file_dir, glyph_file_name in fs_util.walk_files(width_mode_dir):
            if not glyph_file_name.endswith('.png'):
                continue
            glyph_file_path = os.path.join(glyph_file_dir, glyph_file_name)
            if glyph_file_name == 'notdef.png':
                glyph_file_paths_cellar[width_mode_dir_name]['default']['.notdef'] = glyph_file_path
            else:
                hex_name, language_flavors = _parse_glyph_file_name(glyph_file_name)
                code_point = int(hex_name, 16)
                glyph_name = f'uni{code_point:04X}'
                if len(language_flavors) > 0:
                    if 'zh_tr' in language_flavors:
                        assert glyph_name not in glyph_file_paths_cellar[width_mode_dir_name]['zh_tr'], f"Glyph name '{glyph_name}' already exists in language flavor 'zh_tr'"
                        glyph_file_paths_cellar[width_mode_dir_name]['zh_tr'][glyph_name] = glyph_file_path
                else:
                    assert glyph_name not in glyph_file_paths_cellar[width_mode_dir_name]['default'], f"Glyph name '{glyph_name}' already exists"
                    glyph_file_paths_cellar[width_mode_dir_name]['default'][glyph_name] = glyph_file_path
                if width_mode_dir_name == 'common' or width_mode_dir_name == 'monospaced':
                    character_mapping_group['monospaced'][code_point] = glyph_name
                if width_mode_dir_name == 'common' or width_mode_dir_name == 'proportional':
                    character_mapping_group['proportional'][code_point] = glyph_name
    for width_mode in configs.width_modes:
        glyph_file_paths_group[width_mode].update(glyph_file_paths_cellar['common']['default'])
        glyph_file_paths_group[width_mode].update(glyph_file_paths_cellar['common']['zh_tr'])
        glyph_file_paths_group[width_mode].update(glyph_file_paths_cellar[width_mode]['default'])
        glyph_file_paths_group[width_mode].update(glyph_file_paths_cellar[width_mode]['zh_tr'])

    for width_mode, character_mapping in character_mapping_group.items():
        for target, code_points in _inherited_mapping.items():
            if target not in character_mapping:
                continue
            glyph_name = character_mapping[target]
            for code_point in code_points:
                character_mapping[code_point] = glyph_name

    return DesignContext(character_mapping_group, glyph_file_paths_group)


def _create_builder(font_config: FontConfig, context: DesignContext, width_mode: str) -> FontBuilder:
    font_attrs = font_config.get_attrs(width_mode)
    builder = FontBuilder(
        font_config.size,
        font_attrs.ascent,
        font_attrs.descent,
        font_attrs.x_height,
        font_attrs.cap_height,
    )

    builder.character_mapping.update(context.get_character_mapping(width_mode))
    for glyph_name, glyph_file_path in context.get_glyph_file_paths(width_mode).items():
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
    otf_builder = builder.to_otf_builder()
    otf_file_path = os.path.join(path_define.outputs_dir, font_config.get_font_file_name(width_mode, 'otf'))
    otf_builder.save(otf_file_path)
    logger.info("Make font file: '%s'", otf_file_path)
    otf_builder.font.flavor = 'woff2'
    woff2_file_path = os.path.join(path_define.outputs_dir, font_config.get_font_file_name(width_mode, 'woff2'))
    otf_builder.save(woff2_file_path)
    logger.info("Make font file: '%s'", woff2_file_path)
    ttf_file_path = os.path.join(path_define.outputs_dir, font_config.get_font_file_name(width_mode, 'ttf'))
    builder.save_ttf(ttf_file_path)
    logger.info("Make font file: '%s'", ttf_file_path)
    bdf_file_path = os.path.join(path_define.outputs_dir, font_config.get_font_file_name(width_mode, 'bdf'))
    builder.save_bdf(bdf_file_path)
    logger.info("Make font file: '%s'", bdf_file_path)
