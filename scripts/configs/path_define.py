import os

project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

assets_dir = os.path.join(project_root_dir, 'assets')
templates_dir = os.path.join(assets_dir, 'templates')
www_static_dir = os.path.join(assets_dir, 'www-static')

build_dir = os.path.join(project_root_dir, 'build')
cache_dir = os.path.join(build_dir, 'cache')
glyphs_dir = os.path.join(build_dir, 'glyphs')
outputs_dir = os.path.join(build_dir, 'outputs')
releases_dir = os.path.join(build_dir, 'releases')
www_dir = os.path.join(build_dir, 'www')

docs_dir = os.path.join(project_root_dir, 'docs')
