from tools import configs
from tools.configs.font import FontConfig
from tools.services import update_service, template_service
from tools.services.font_service import DesignContext, FontContext


def main():
    update_service.setup_glyphs()

    font_configs = FontConfig.load_all()
    for font_config in font_configs.values():
        design_context = DesignContext.load(font_config)
        for width_mode in configs.width_modes:
            font_context = FontContext(design_context, width_mode)
            font_context.make_font('woff2')
            template_service.make_alphabet_html(design_context, width_mode)
        template_service.make_demo_html(design_context)
    template_service.make_index_html(font_configs)
    template_service.make_playground_html(font_configs)


if __name__ == '__main__':
    main()
