import logging
import math
import re
from pathlib import Path

from pixel_font_builder import FontBuilder, WeightName, SerifStyle, SlantStyle, Glyph
from pixel_font_builder.opentype import Flavor

from scripts import configs
from scripts.configs import path_define, FontConfig
from scripts.utils import fs_util, bitmap_util

logger = logging.getLogger('font_service')

_inherited_mapping: dict[int, list[int]] = fs_util.read_yaml(path_define.assets_dir.joinpath('inherited-mapping.yaml'))


class GlyphFile:
    @staticmethod
    def load(file_path: Path) -> 'GlyphFile':
        tokens = re.split(r'\s+', file_path.stem, 1)

        if tokens[0] == 'notdef':
            code_point = -1
        else:
            code_point = int(tokens[0], 16)

        if len(tokens) > 1:
            language_flavors = tokens[1].lower().split(',')
        else:
            language_flavors = []

        return GlyphFile(file_path, code_point, language_flavors)

    file_path: Path
    bitmap: list[list[int]]
    width: int
    height: int
    code_point: int
    language_flavors: list[str]

    def __init__(self, file_path: Path, code_point: int, language_flavors: list[str]):
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

        root_dir = path_define.glyphs_dir.joinpath(str(font_config.font_size))
        for width_mode_dir in root_dir.iterdir():
            if not width_mode_dir.is_dir():
                continue
            width_mode_dir_name = width_mode_dir.name
            assert width_mode_dir_name == 'common' or width_mode_dir_name in configs.width_modes, f"Width mode '{width_mode_dir_name}' undefined: '{width_mode_dir}'"

            code_point_registry = {}
            for file_dir, _, file_names in width_mode_dir.walk():
                for file_name in file_names:
                    if not file_name.endswith('.png'):
                        continue
                    file_path = file_dir.joinpath(file_name)
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
                assert '' in glyph_files, f'Missing default language flavor: {font_config.font_size}px {width_mode_dir_name} {code_point:04X}'
            glyph_file_registry[width_mode_dir_name] = code_point_registry

        return DesignContext(font_config, glyph_file_registry)

    font_config: FontConfig
    _glyph_file_registry: dict[str, dict[int, dict[str, GlyphFile]]]
    _sequence_pool: dict[str, list[int]]
    _alphabet_pool: dict[str, set[str]]
    _character_mapping_pool: dict[str, dict[int, str]]
    _glyph_files_pool: dict[str, list[GlyphFile]]

    def __init__(
            self,
            font_config: FontConfig,
            glyph_file_registry: dict[str, dict[int, dict[str, GlyphFile]]],
    ):
        self.font_config = font_config
        self._glyph_file_registry = glyph_file_registry
        self._sequence_pool = {}
        self._alphabet_pool = {}
        self._character_mapping_pool = {}
        self._glyph_files_pool = {}

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
    builder.font_metric.font_size = design_context.font_config.font_size
    builder.font_metric.horizontal_layout.ascent = layout_param.ascent
    builder.font_metric.horizontal_layout.descent = layout_param.descent
    builder.font_metric.vertical_layout.ascent = math.ceil(layout_param.line_height / 2)
    builder.font_metric.vertical_layout.descent = math.floor(layout_param.line_height / 2)
    builder.font_metric.x_height = layout_param.x_height
    builder.font_metric.cap_height = layout_param.cap_height

    builder.meta_info.version = configs.font_version
    builder.meta_info.created_time = configs.font_version_time
    builder.meta_info.modified_time = configs.font_version_time
    builder.meta_info.family_name = f'Ark Pixel Inherited {design_context.font_config.font_size}px {width_mode.capitalize()}'
    builder.meta_info.weight_name = WeightName.REGULAR
    builder.meta_info.serif_style = SerifStyle.SANS_SERIF
    builder.meta_info.slant_style = SlantStyle.NORMAL
    builder.meta_info.width_mode = width_mode.capitalize()
    builder.meta_info.manufacturer = 'TakWolf'
    builder.meta_info.designer = 'TakWolf'
    builder.meta_info.description = 'Open source Pan-CJK pixel font.'
    builder.meta_info.copyright_info = "Copyright (c) 2023, TakWolf (https://takwolf.com), with Reserved Font Name 'Ark Pixel Inherited'."
    builder.meta_info.license_info = 'This Font Software is licensed under the SIL Open Font License, Version 1.1.'
    builder.meta_info.vendor_url = 'https://ark-pixel-font-inherited.takwolf.com'
    builder.meta_info.designer_url = 'https://takwolf.com'
    builder.meta_info.license_url = 'https://openfontlicense.org'

    character_mapping = design_context.get_character_mapping(width_mode)
    builder.character_mapping.update(character_mapping)

    glyph_files = design_context.get_glyph_files(width_mode)
    for glyph_file in glyph_files:
        horizontal_origin_y = math.floor((layout_param.ascent + layout_param.descent - glyph_file.height) / 2)
        vertical_origin_y = (design_context.font_config.font_size - glyph_file.height) // 2 - 1
        builder.glyphs.append(Glyph(
            name=glyph_file.glyph_name,
            advance_width=glyph_file.width,
            advance_height=design_context.font_config.font_size,
            horizontal_origin=(0, horizontal_origin_y),
            vertical_origin_y=vertical_origin_y,
            bitmap=glyph_file.bitmap,
        ))

    return builder


class FontContext:
    design_context: DesignContext
    width_mode: str
    _builder: FontBuilder

    def __init__(self, design_context: DesignContext, width_mode: str):
        self.design_context = design_context
        self.width_mode = width_mode
        self._builder = _create_builder(design_context, width_mode)

    def make_font_file(self, font_format: str):
        path_define.outputs_dir.mkdir(parents=True, exist_ok=True)
        file_path = path_define.outputs_dir.joinpath(f'ark-pixel-inherited-{self.design_context.font_config.font_size}px-{self.width_mode}.{font_format}')
        if font_format == 'woff2':
            self._builder.save_otf(file_path, flavor=Flavor.WOFF2)
        else:
            getattr(self._builder, f'save_{font_format}')(file_path)
        logger.info("Make font file: '%s'", file_path)
