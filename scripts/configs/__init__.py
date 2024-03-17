from scripts.configs.font import FontConfig
from scripts.configs.deploy import GitDeployConfig

width_modes = [
    'monospaced',
    'proportional',
]

font_sizes = [10, 12, 16]

font_configs = FontConfig.load_all()

font_formats = ['otf', 'woff2', 'ttf', 'bdf']

git_deploy_config = GitDeployConfig(
    url='git@github.com:TakWolf/ark-pixel-font-inherited.git',
    remote_name='github',
    branch_name='gh-pages',
)
