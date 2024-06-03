import datetime

from scripts.configs.deploy import GitDeployConfig
from scripts.configs.font import FontConfig
from scripts.configs.source import GithubSourceConfig, GitSourceType

font_version = '2024.05.12'

font_version_time = datetime.datetime.fromisoformat(f'{font_version.replace('.', '-')}T00:00:00Z')

font_sizes = [10, 12, 16]

font_formats = ['otf', 'woff2', 'ttf', 'bdf', 'pcf']

width_modes = [
    'monospaced',
    'proportional',
]

ark_pixel_config = GithubSourceConfig(
    repository_name='TakWolf/ark-pixel-font',
    source_type=GitSourceType.TAG,
    source_name=None,
)

git_deploy_configs = [GitDeployConfig(
    url='git@github.com:TakWolf/ark-pixel-font-inherited.git',
    remote_name='github',
    branch_name='gh-pages',
)]
