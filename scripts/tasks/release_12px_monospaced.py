from scripts import configs
from scripts.services import update_service, publish_service, info_service
from scripts.services.font_service import DesignContext, FontContext


def main():
    update_service.setup_glyphs()

    font_config = configs.font_configs[12]
    design_context = DesignContext.load(font_config)

    width_mode = 'monospaced'
    font_context = FontContext(design_context, width_mode)
    font_context.make_otf()
    font_context.make_woff2()
    font_context.make_ttf()
    font_context.make_bdf()
    font_context.make_pcf()
    publish_service.make_release_zips(font_config, width_mode)
    info_service.make_info_file(design_context, width_mode)
    info_service.make_alphabet_txt_file(design_context, width_mode)


if __name__ == '__main__':
    main()
