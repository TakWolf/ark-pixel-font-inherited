import logging
import zipfile

from scripts import configs
from scripts.configs import path_define, ark_pixel_config, FontConfig, GitSourceType
from scripts.utils import fs_util, github_api, download_util

logger = logging.getLogger('update_service')


def update_glyphs_version():
    if ark_pixel_config.source_type == GitSourceType.TAG:
        tag_name = ark_pixel_config.source_name
        if tag_name is None:
            tag_name = github_api.get_releases_latest_tag_name(ark_pixel_config.repository_name)
        sha = github_api.get_tag_sha(ark_pixel_config.repository_name, tag_name)
        version = tag_name
    elif ark_pixel_config.source_type == GitSourceType.BRANCH:
        branch_name = ark_pixel_config.source_name
        sha = github_api.get_branch_latest_commit_sha(ark_pixel_config.repository_name, branch_name)
        version = branch_name
    elif ark_pixel_config.source_type == GitSourceType.COMMIT:
        sha = ark_pixel_config.source_name
        version = sha
    else:
        raise Exception(f"Unknown source type: '{ark_pixel_config.source_type}'")
    version_info = {
        'sha': sha,
        'version': version,
        'version_url': f'https://github.com/{ark_pixel_config.repository_name}/tree/{version}',
        'asset_url': f'https://github.com/{ark_pixel_config.repository_name}/archive/{sha}.zip',
    }
    file_path = path_define.assets_dir.joinpath('glyphs-version.json')
    fs_util.write_json(version_info, file_path)
    logger.info("Update version file: '%s'", file_path)


def setup_glyphs():
    build_version_file_path = path_define.glyphs_dir.joinpath('version.json')
    if build_version_file_path.is_file():
        build_sha = fs_util.read_json(build_version_file_path)['sha']
    else:
        build_sha = None

    version_file_path = path_define.assets_dir.joinpath('glyphs-version.json')
    version_info = fs_util.read_json(version_file_path)
    sha = version_info['sha']
    if build_sha == sha:
        return
    logger.info('Need setup glyphs')

    download_dir = path_define.cache_dir.joinpath('ark-pixel-font')
    source_file_path = download_dir.joinpath(f'{sha}.zip')
    if not source_file_path.exists():
        asset_url = version_info['asset_url']
        logger.info("Start download: '%s'", asset_url)
        download_dir.mkdir(parents=True, exist_ok=True)
        download_util.download_file(asset_url, source_file_path)
    else:
        logger.info("Already downloaded: '%s'", source_file_path)

    source_unzip_dir = download_dir.joinpath(f'ark-pixel-font-{sha}')
    fs_util.delete_dir(source_unzip_dir)
    with zipfile.ZipFile(source_file_path) as file:
        file.extractall(download_dir)
    logger.info("Unzip: '%s'", source_unzip_dir)

    fs_util.delete_dir(path_define.glyphs_dir)
    source_glyphs_dir = source_unzip_dir.joinpath('assets', 'glyphs')
    source_glyphs_dir.rename(path_define.glyphs_dir)
    fs_util.delete_dir(source_unzip_dir)
    configs.font_configs = FontConfig.load_all()
    fs_util.write_json(version_info, build_version_file_path)
    logger.info("Update glyphs: '%s'", sha)
