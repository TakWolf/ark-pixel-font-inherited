from pathlib import Path

project_root_dir = Path(__file__).parent.joinpath('..', '..').resolve()

assets_dir = project_root_dir.joinpath('assets')
templates_dir = assets_dir.joinpath('templates')

cache_dir = project_root_dir.joinpath('cache')
downloads_dir = cache_dir.joinpath('downloads')
glyphs_dir = cache_dir.joinpath('glyphs')

build_dir = project_root_dir.joinpath('build')
outputs_dir = build_dir.joinpath('outputs')
releases_dir = build_dir.joinpath('releases')

docs_dir = project_root_dir.joinpath('docs')
