from tools.configs.source import GithubSourceConfig, GitSourceType

font_version = '2024.05.12'

font_sizes = [10, 12, 16]

width_modes = [
    'monospaced',
    'proportional',
]

font_formats = ['otf', 'woff2', 'ttf', 'bdf', 'pcf']

ark_pixel_config = GithubSourceConfig(
    repository_name='TakWolf/ark-pixel-font',
    source_type=GitSourceType.TAG,
    source_name=None,
)
