import logging
import os

from PIL import Image, ImageFont, ImageDraw

from configs import path_define
from utils import fs_util

logger = logging.getLogger('image-service')


def _load_font(font_config, width_mode, scale=1):
    file_path = os.path.join(path_define.outputs_dir, font_config.get_font_file_name(width_mode, 'woff2'))
    return ImageFont.truetype(file_path, font_config.size * scale)


def _draw_text(
        image,
        xy,
        text,
        font,
        text_color=(0, 0, 0, 255),
        shadow_color=None,
        line_height=None,
        line_gap=0,
        is_horizontal_centered=False,
        is_vertical_centered=False,
):
    draw = ImageDraw.Draw(image)
    x, y = xy
    default_line_height = sum(font.getmetrics())
    if line_height is None:
        line_height = default_line_height
    y += (line_height - default_line_height) / 2
    spacing = line_height + line_gap - font.getsize('A')[1]
    if is_horizontal_centered:
        x -= draw.textbbox((0, 0), text, font=font)[2] / 2
    if is_vertical_centered:
        y -= line_height / 2
    if shadow_color is not None:
        draw.text((x + 1, y + 1), text, fill=shadow_color, font=font, spacing=spacing)
    draw.text((x, y), text, fill=text_color, font=font, spacing=spacing)


def make_preview_image_file(font_config):
    font = _load_font(font_config, 'proportional')

    image = Image.new('RGBA', (font_config.size * 35, font_config.size * 2 + font_config.line_height * 8), (255, 255, 255, 255))
    _draw_text(image, (font_config.size, font_config.size), '方舟像素字体 - 传承字形 / Ark Pixel Font - Inherited', font)
    _draw_text(image, (font_config.size, font_config.size + font_config.line_height), '我们每天度过的称之为日常的生活，其实是一个个奇迹的连续也说不定。', font)
    _draw_text(image, (font_config.size, font_config.size + font_config.line_height * 2), '我們每天度過的稱之為日常的生活，其實是一個個奇跡的連續也說不定。', font)
    _draw_text(image, (font_config.size, font_config.size + font_config.line_height * 3), '日々、私たちが過ごしている日常は、実は奇跡の連続なのかもしれない。', font)
    _draw_text(image, (font_config.size, font_config.size + font_config.line_height * 4), 'THE QUICK BROWN FOX JUMPS OVER A LAZY DOG.', font)
    _draw_text(image, (font_config.size, font_config.size + font_config.line_height * 5), 'the quick brown fox jumps over a lazy dog.', font)
    _draw_text(image, (font_config.size, font_config.size + font_config.line_height * 6), '0123456789', font)
    _draw_text(image, (font_config.size, font_config.size + font_config.line_height * 7), '★☆☺☹♠♡♢♣♤♥♦♧☀☼♩♪♫♬☂☁⚓✈⚔☯', font)
    image = image.resize((image.width * 2, image.height * 2), Image.NEAREST)

    fs_util.make_dirs(path_define.outputs_dir)
    file_path = os.path.join(path_define.outputs_dir, font_config.preview_image_file_name)
    image.save(file_path)
    logger.info(f"Made preview image file: '{file_path}'")
