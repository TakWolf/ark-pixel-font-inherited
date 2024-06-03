from scripts import configs
from scripts.configs import FontConfig
from scripts.services import update_service, publish_service, info_service
from scripts.services.font_service import DesignContext, FontContext


def main():
    font_size = 12
    width_mode = 'monospaced'

    update_service.setup_glyphs()

    font_config = FontConfig.load(font_size)
    design_context = DesignContext.load(font_config)
    font_context = FontContext(design_context, width_mode)
    for font_format in configs.font_formats:
        font_context.make_font_file(font_format)
        publish_service.make_release_zip(font_size, width_mode, font_format)
    info_service.make_info_file(design_context, width_mode)
    info_service.make_alphabet_txt_file(design_context, width_mode)


if __name__ == '__main__':
    main()
