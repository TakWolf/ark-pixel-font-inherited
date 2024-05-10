import logging
import math
import os
import re

from pixel_font_builder import FontBuilder, WeightName, SerifStyle, SlantStyle, Glyph
from pixel_font_builder.opentype import Flavor

from scripts import configs
from scripts.configs import path_define, FontConfig
from scripts.utils import fs_util, bitmap_util

logger = logging.getLogger('font_service')

_inherited_mapping: dict[int, list[int]] = fs_util.read_yaml(os.path.join(path_define.assets_dir, 'inherited-mapping.yaml'))


class GlyphFile:
    @staticmethod
    def load(file_path: str) -> 'GlyphFile':
        tokens = re.split(r'\s+', os.path.basename(file_path).removesuffix('.png'), 1)

        if tokens[0] == 'notdef':
            code_point = -1
        else:
            code_point = int(tokens[0], 16)

        if len(tokens) > 1:
            language_flavors = tokens[1].lower().split(',')
        else:
            language_flavors = []

        return GlyphFile(file_path, code_point, language_flavors)

    def __init__(self, file_path: str, code_point: int, language_flavors: list[str]):
        self.file_path = file_path
        self.bitmap, self.width, self.height = bitmap_util.load_png(file_path)
        self.code_point = code_point
        self.language_flavors = language_flavors

    @property
    def glyph_name(self) -> str:
        if self.code_point == -1:
            _glyph_name = '.notdef'
        else:
            _glyph_name = f'{self.code_point:04X}'
        if len(self.language_flavors) > 0:
            _glyph_name = f'{_glyph_name}-i'
        return _glyph_name


class DesignContext:
    @staticmethod
    def load(font_config: FontConfig) -> 'DesignContext':
        glyph_file_registry = {}

        root_dir = os.path.join(path_define.glyphs_dir, str(font_config.size))
        for width_mode_dir_name in os.listdir(root_dir):
            width_mode_dir = os.path.join(root_dir, width_mode_dir_name)
            if not os.path.isdir(width_mode_dir):
                continue
            assert width_mode_dir_name == 'common' or width_mode_dir_name in configs.width_modes, f"Width mode '{width_mode_dir_name}' undefined: '{width_mode_dir}'"

            code_point_registry = {}
            for file_dir, _, file_names in os.walk(width_mode_dir):
                for file_name in file_names:
                    if not file_name.endswith('.png'):
                        continue
                    file_path = os.path.join(file_dir, file_name)
                    glyph_file = GlyphFile.load(file_path)

                    if glyph_file.code_point not in code_point_registry:
                        language_flavor_registry = {}
                        code_point_registry[glyph_file.code_point] = language_flavor_registry
                    else:
                        language_flavor_registry = code_point_registry[glyph_file.code_point]

                    if len(glyph_file.language_flavors) > 0:
                        for language_flavor in glyph_file.language_flavors:
                            assert language_flavor not in language_flavor_registry, f"Language flavor '{language_flavor}' already exists: '{glyph_file.file_path}' -> '{language_flavor_registry[language_flavor].file_path}'"
                            language_flavor_registry[language_flavor] = glyph_file
                    else:
                        assert '' not in language_flavor_registry, f"Default language flavor already exists: '{glyph_file.file_path}' -> '{language_flavor_registry[''].file_path}'"
                        language_flavor_registry[''] = glyph_file

            for target, code_points in _inherited_mapping.items():
                if target not in code_point_registry:
                    continue
                language_flavor_registry = code_point_registry[target]
                for code_point in code_points:
                    code_point_registry[code_point] = language_flavor_registry

            for code_point, glyph_files in code_point_registry.items():
                assert '' in glyph_files, f'Missing default language flavor: {font_config.size}px {width_mode_dir_name} {code_point:04X}'
            glyph_file_registry[width_mode_dir_name] = code_point_registry

        return DesignContext(font_config, glyph_file_registry)

    def __init__(
            self,
            font_config: FontConfig,
            glyph_file_registry: dict[str, dict[int, dict[str, GlyphFile]]],
    ):
        self.font_config = font_config
        self._glyph_file_registry = glyph_file_registry
        self._sequence_pool: dict[str, list[int]] = {}
        self._alphabet_pool: dict[str, set[str]] = {}
        self._character_mapping_pool: dict[str, dict[int, str]] = {}
        self._glyph_files_pool: dict[str, list[GlyphFile]] = {}

    def _get_sequence(self, width_mode: str) -> list[int]:
        if width_mode in self._sequence_pool:
            sequence = self._sequence_pool[width_mode]
        else:
            sequence = set(self._glyph_file_registry['common'])
            sequence.update(self._glyph_file_registry[width_mode])
            sequence = list(sequence)
            sequence.sort()
            self._sequence_pool[width_mode] = sequence
        return sequence

    def get_alphabet(self, width_mode: str) -> set[str]:
        if width_mode in self._alphabet_pool:
            alphabet = self._alphabet_pool[width_mode]
        else:
            alphabet = set([chr(code_point) for code_point in self._get_sequence(width_mode) if code_point >= 0])
            self._alphabet_pool[width_mode] = alphabet
        return alphabet

    def get_character_mapping(self, width_mode: str) -> dict[int, str]:
        if width_mode in self._character_mapping_pool:
            character_mapping = self._character_mapping_pool[width_mode]
        else:
            character_mapping = {}
            for code_point in self._get_sequence(width_mode):
                if code_point < 0:
                    continue
                language_flavor_registry = self._glyph_file_registry[width_mode].get(code_point, None)
                if language_flavor_registry is None:
                    language_flavor_registry = self._glyph_file_registry['common'][code_point]
                glyph_file = language_flavor_registry.get('zh_tr', language_flavor_registry[''])
                character_mapping[code_point] = glyph_file.glyph_name
            self._character_mapping_pool[width_mode] = character_mapping
        return character_mapping

    def get_glyph_files(self, width_mode: str) -> list[GlyphFile]:
        if width_mode in self._glyph_files_pool:
            glyph_files = self._glyph_files_pool[width_mode]
        else:
            glyph_files = []
            sequence = self._get_sequence(width_mode)
            for code_point in sequence:
                language_flavor_registry = self._glyph_file_registry[width_mode].get(code_point, None)
                if language_flavor_registry is None:
                    language_flavor_registry = self._glyph_file_registry['common'][code_point]
                glyph_file = language_flavor_registry.get('zh_tr', language_flavor_registry[''])
                if glyph_file not in glyph_files:
                    glyph_files.append(glyph_file)
            self._glyph_files_pool[width_mode] = glyph_files
        return glyph_files


def _create_builder(design_context: DesignContext, width_mode: str) -> FontBuilder:
    layout_param = design_context.font_config.layout_params[width_mode]

    builder = FontBuilder()
    builder.font_metric.font_size = design_context.font_config.size
    builder.font_metric.horizontal_layout.ascent = layout_param.ascent
    builder.font_metric.horizontal_layout.descent = layout_param.descent
    builder.font_metric.vertical_layout.ascent = math.ceil(layout_param.line_height / 2)
    builder.font_metric.vertical_layout.descent = math.floor(layout_param.line_height / 2)
    builder.font_metric.x_height = layout_param.x_height
    builder.font_metric.cap_height = layout_param.cap_height

    builder.meta_info.version = FontConfig.VERSION
    builder.meta_info.created_time = FontConfig.VERSION_TIME
    builder.meta_info.modified_time = FontConfig.VERSION_TIME
    builder.meta_info.family_name = f'{FontConfig.FAMILY_NAME} {design_context.font_config.size}px {width_mode.capitalize()}'
    builder.meta_info.weight_name = WeightName.REGULAR
    builder.meta_info.serif_style = SerifStyle.SANS_SERIF
    builder.meta_info.slant_style = SlantStyle.NORMAL
    builder.meta_info.width_mode = width_mode.capitalize()
    builder.meta_info.manufacturer = FontConfig.MANUFACTURER
    builder.meta_info.designer = FontConfig.DESIGNER
    builder.meta_info.description = FontConfig.DESCRIPTION
    builder.meta_info.copyright_info = FontConfig.COPYRIGHT_INFO
    builder.meta_info.license_info = FontConfig.LICENSE_INFO
    builder.meta_info.vendor_url = FontConfig.VENDOR_URL
    builder.meta_info.designer_url = FontConfig.DESIGNER_URL
    builder.meta_info.license_url = FontConfig.LICENSE_URL

    character_mapping = design_context.get_character_mapping(width_mode)
    builder.character_mapping.update(character_mapping)

    glyph_files = design_context.get_glyph_files(width_mode)
    for glyph_file in glyph_files:
        horizontal_origin_y = math.floor((layout_param.ascent + layout_param.descent - glyph_file.height) / 2)
        vertical_origin_y = (design_context.font_config.size - glyph_file.height) // 2 - 1
        builder.glyphs.append(Glyph(
            name=glyph_file.glyph_name,
            advance_width=glyph_file.width,
            advance_height=design_context.font_config.size,
            horizontal_origin=(0, horizontal_origin_y),
            vertical_origin_y=vertical_origin_y,
            bitmap=glyph_file.bitmap,
        ))

    return builder


class FontContext:
    def __init__(self, design_context: DesignContext, width_mode: str):
        self.design_context = design_context
        self.width_mode = width_mode
        self._builder = _create_builder(design_context, width_mode)

    def make_otf(self):
        fs_util.make_dir(path_define.outputs_dir)
        file_path = os.path.join(path_define.outputs_dir, self.design_context.font_config.get_font_file_name(self.width_mode, 'otf'))
        self._builder.save_otf(file_path)
        logger.info("Make font file: '%s'", file_path)

    def make_woff2(self):
        fs_util.make_dir(path_define.outputs_dir)
        file_path = os.path.join(path_define.outputs_dir, self.design_context.font_config.get_font_file_name(self.width_mode, 'woff2'))
        self._builder.save_otf(file_path, flavor=Flavor.WOFF2)
        logger.info("Make font file: '%s'", file_path)

    def make_ttf(self):
        fs_util.make_dir(path_define.outputs_dir)
        file_path = os.path.join(path_define.outputs_dir, self.design_context.font_config.get_font_file_name(self.width_mode, 'ttf'))
        self._builder.save_ttf(file_path)
        logger.info("Make font file: '%s'", file_path)

    def make_bdf(self):
        fs_util.make_dir(path_define.outputs_dir)
        file_path = os.path.join(path_define.outputs_dir, self.design_context.font_config.get_font_file_name(self.width_mode, 'bdf'))
        self._builder.save_bdf(file_path)
        logger.info("Make font file: '%s'", file_path)

    def make_pcf(self):
        fs_util.make_dir(path_define.outputs_dir)
        file_path = os.path.join(path_define.outputs_dir, self.design_context.font_config.get_font_file_name(self.width_mode, 'pcf'))
        self._builder.save_pcf(file_path)
        logger.info("Make font file: '%s'", file_path)
