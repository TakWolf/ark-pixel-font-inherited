from pathlib import Path

project_root_dir = Path(__file__).parent.joinpath('..', '..').resolve()

assets_dir = project_root_dir.joinpath('assets')
configs_dir = assets_dir.joinpath('configs')
mappings_dir = assets_dir.joinpath('mappings')
templates_dir = assets_dir.joinpath('templates')

cache_dir = project_root_dir.joinpath('cache')
downloads_dir = cache_dir.joinpath('downloads')
ark_pixel_glyphs_dir = cache_dir.joinpath('ark-pixel-glyphs')
ark_pixel_configs_dir = cache_dir.joinpath('ark-pixel-configs')
ark_pixel_mappings_dir = cache_dir.joinpath('ark-pixel-mappings')

build_dir = project_root_dir.joinpath('build')
outputs_dir = build_dir.joinpath('outputs')
releases_dir = build_dir.joinpath('releases')

docs_dir = project_root_dir.joinpath('docs')
