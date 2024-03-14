import json
import logging
import os
import zipfile

import requests

from scripts import configs
from scripts.configs import path_define, ark_pixel_config, FontConfig
from scripts.configs.ark_pixel_config import SourceType
from scripts.utils import fs_util

logger = logging.getLogger('update-service')


def _get_github_releases_latest_tag_name(repository_name: str) -> str:
    url = f'https://api.github.com/repos/{repository_name}/releases/latest'
    response = requests.get(url)
    assert response.ok, url
    return response.json()['tag_name']


def _get_github_tag_sha(repository_name: str, tag_name: str) -> str:
    url = f'https://api.github.com/repos/{repository_name}/tags'
    response = requests.get(url)
    assert response.ok, url
    tag_infos = response.json()
    for tag_info in tag_infos:
        if tag_info['name'] == tag_name:
            return tag_info['commit']['sha']
    raise Exception(f"Tag info not found: '{tag_name}'")


def _get_github_branch_latest_commit_sha(repository_name: str, branch_name: str) -> str:
    url = f'https://api.github.com/repos/{repository_name}/branches/{branch_name}'
    response = requests.get(url)
    assert response.ok, url
    return response.json()['commit']['sha']


def _download_file(url: str, file_path: str):
    response = requests.get(url, stream=True)
    assert response.ok, url
    tmp_file_path = f'{file_path}.download'
    with open(tmp_file_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=512):
            if chunk is not None:
                file.write(chunk)
    os.rename(tmp_file_path, file_path)


def _save_json_file(data: dict, file_path: str):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(json.dumps(data, indent=2, ensure_ascii=False))
        file.write('\n')


def _load_json_file(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.loads(file.read())


def update_glyphs_version():
    if ark_pixel_config.source_type == SourceType.TAG:
        tag_name = ark_pixel_config.source_name
        if tag_name is None:
            tag_name = _get_github_releases_latest_tag_name(ark_pixel_config.repository_name)
        sha = _get_github_tag_sha(ark_pixel_config.repository_name, tag_name)
        version = tag_name
    elif ark_pixel_config.source_type == SourceType.BRANCH:
        branch_name = ark_pixel_config.source_name
        sha = _get_github_branch_latest_commit_sha(ark_pixel_config.repository_name, branch_name)
        version = branch_name
    elif ark_pixel_config.source_type == SourceType.COMMIT:
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
    file_path = os.path.join(path_define.glyphs_dir, 'version.json')
    _save_json_file(version_info, file_path)
    logger.info("Update version file: '%s'", file_path)


def setup_glyphs():
    current_version_file_path = os.path.join(path_define.ark_pixel_glyphs_dir, 'version.json')
    if os.path.isfile(current_version_file_path):
        current_sha = _load_json_file(current_version_file_path)['sha']
    else:
        current_sha = None

    version_file_path = os.path.join(path_define.glyphs_dir, 'version.json')
    version_info = _load_json_file(version_file_path)
    sha = version_info['sha']
    if current_sha == sha:
        return
    logger.info('Need setup glyphs')

    download_dir = os.path.join(path_define.cache_dir, 'ark-pixel-font')
    source_file_path = os.path.join(download_dir, f'{sha}.zip')
    if not os.path.exists(source_file_path):
        asset_url = version_info["asset_url"]
        logger.info("Start download: '%s'", asset_url)
        fs_util.make_dir(download_dir)
        _download_file(asset_url, source_file_path)
    else:
        logger.info("Already downloaded: '%s'", source_file_path)

    source_unzip_dir = os.path.join(download_dir, f'ark-pixel-font-{sha}')
    fs_util.delete_dir(source_unzip_dir)
    with zipfile.ZipFile(source_file_path) as file:
        file.extractall(download_dir)
    logger.info("Unzip: '%s'", source_unzip_dir)

    fs_util.delete_dir(path_define.ark_pixel_glyphs_dir)
    source_glyphs_dir = os.path.join(source_unzip_dir, 'assets', 'glyphs')
    os.rename(source_glyphs_dir, path_define.ark_pixel_glyphs_dir)
    fs_util.delete_dir(source_unzip_dir)
    configs.font_configs = [FontConfig(font_config.size) for font_config in configs.font_configs]
    configs.font_size_to_config = {font_config.size: font_config for font_config in configs.font_configs}
    _save_json_file(version_info, current_version_file_path)
    logger.info("Update glyphs: '%s'", sha)
