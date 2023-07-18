import json
import logging
import os
import shutil
import zipfile

import requests

import configs
from configs import path_define, ark_pixel_config, FontConfig
from configs.ark_pixel_config import SourceType
from utils import fs_util

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
    logger.info(f"Update version file: '{file_path}'")


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

    download_dir = os.path.join(path_define.cache_dir, 'ark-pixel-font', version_info['sha'])
    source_file_path = os.path.join(download_dir, 'source.zip')
    if not os.path.exists(source_file_path):
        asset_url = version_info["asset_url"]
        logger.info(f"Start download: '{asset_url}'")
        fs_util.make_dirs(download_dir)
        _download_file(asset_url, source_file_path)
    else:
        logger.info(f"Already downloaded: '{source_file_path}'")

    source_unzip_dir = source_file_path.removesuffix('.zip')
    fs_util.delete_dir(source_unzip_dir)
    with zipfile.ZipFile(source_file_path) as file:
        file.extractall(source_unzip_dir)
    logger.info(f"Unzip: '{source_unzip_dir}'")

    fs_util.delete_dir(path_define.ark_pixel_glyphs_dir)
    fs_util.make_dirs(path_define.ark_pixel_glyphs_dir)
    for font_config in configs.font_configs:
        source_glyphs_from_dir = os.path.join(source_unzip_dir, f'ark-pixel-font-{sha}', 'assets', 'glyphs', str(font_config.size))
        source_glyphs_to_dir = os.path.join(path_define.ark_pixel_glyphs_dir, str(font_config.size))
        shutil.copytree(source_glyphs_from_dir, source_glyphs_to_dir)

        config_file_from_path = os.path.join(path_define.ark_pixel_glyphs_dir, str(font_config.size), 'config.toml')
        config_file_to_path = os.path.join(path_define.patch_glyphs_dir, str(font_config.size), 'config.toml')
        os.remove(config_file_to_path)
        os.rename(config_file_from_path, config_file_to_path)
    fs_util.delete_dir(source_unzip_dir)
    configs.font_configs = [FontConfig(font_config.size) for font_config in configs.font_configs]
    configs.font_size_to_config = {font_config.size: font_config for font_config in configs.font_configs}
    _save_json_file(version_info, current_version_file_path)
    logger.info(f"Update glyphs: '{sha}'")
