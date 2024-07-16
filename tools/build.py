import shutil

from tools import configs
from tools.configs import path_define
from tools.configs.font import FontConfig
from tools.services import update_service, publish_service, info_service, template_service, image_service
from tools.services.font_service import DesignContext


def main():
    if path_define.build_dir.exists():
        shutil.rmtree(path_define.build_dir)

    update_service.setup_glyphs()

    font_configs = {}

    for font_size in configs.font_sizes:
        font_config = FontConfig.load(font_size)
        font_configs[font_size] = font_config
        design_context = DesignContext.load(font_config)
        for width_mode in configs.width_modes:
            for font_format in configs.font_formats:
                design_context.make_font(width_mode, font_format)
                publish_service.make_release_zip(font_size, width_mode, font_format)
            info_service.make_font_info(design_context, width_mode)
            template_service.make_alphabet_html(design_context, width_mode)
        template_service.make_demo_html(design_context)
        image_service.make_preview_image(font_config)
    template_service.make_index_html(font_configs)
    template_service.make_playground_html(font_configs)


if __name__ == '__main__':
    main()
