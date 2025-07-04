import json

from loguru import logger

from tools.configs import path_define
from tools.utils import github_api


def upgrade_ark_pixel():
    repository_name = 'TakWolf/ark-pixel-font'
    source_type = 'tag'
    source_name = None

    if source_type == 'tag':
        tag_name = source_name
        if tag_name is None:
            tag_name = github_api.get_releases_latest_tag_name(repository_name)
        sha = github_api.get_tag_sha(repository_name, tag_name)
        version = tag_name
    elif source_type == 'branch':
        branch_name = source_name
        sha = github_api.get_branch_latest_commit_sha(repository_name, branch_name)
        version = branch_name
    elif source_type == 'commit':
        sha = source_name
        version = sha
    else:
        raise Exception(f"Unknown source type: '{source_type}'")

    version_info = {
        'sha': sha,
        'version': version,
        'version_url': f'https://github.com/{repository_name}/tree/{version}',
        'asset_url': f'https://github.com/{repository_name}/archive/{sha}.zip',
    }
    version_file_path = path_define.assets_dir.joinpath('ark-pixel-version.json')
    version_file_path.write_text(f'{json.dumps(version_info, indent=2, ensure_ascii=False)}\n', 'utf-8')
    logger.info("Update version file: '{}'", version_file_path)
