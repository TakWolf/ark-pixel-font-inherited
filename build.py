from scripts import configs
from scripts.configs import path_define
from scripts.services import update_service, publish_service, info_service, template_service, image_service
from scripts.services.font_service import DesignContext, FontContext
from scripts.utils import fs_util


def main():
    fs_util.delete_dir(path_define.outputs_dir)
    fs_util.delete_dir(path_define.releases_dir)

    update_service.setup_glyphs()

    for font_config in configs.font_configs.values():
        design_context = DesignContext.load(font_config)
        for width_mode in configs.width_modes:
            font_context = FontContext(design_context, width_mode)
            font_context.make_otf()
            font_context.make_woff2()
            font_context.make_ttf()
            font_context.make_bdf()
            font_context.make_pcf()
            publish_service.make_release_zips(font_config, width_mode)
            info_service.make_info_file(design_context, width_mode)
            info_service.make_alphabet_txt_file(design_context, width_mode)
            template_service.make_alphabet_html_file(design_context, width_mode)
        template_service.make_demo_html_file(design_context)
        image_service.make_preview_image_file(font_config)
    template_service.make_index_html_file()
    template_service.make_playground_html_file()


if __name__ == '__main__':
    main()
