import json
import logging
import os
import shutil
import zipfile

import requests

from configs import path_define, ark_pixel_config
from utils import fs_util

logger = logging.getLogger('update-service')


def _get_github_releases_latest_tag_name(repository_name):
    url = f'https://api.github.com/repos/{repository_name}/releases/latest'
    response = requests.get(url)
    assert response.ok, url
    return response.json()['tag_name']


def _get_github_tag_sha(repository_name, tag_name):
    url = f'https://api.github.com/repos/{repository_name}/tags'
    response = requests.get(url)
    assert response.ok, url
    tag_infos = response.json()
    for tag_info in tag_infos:
        if tag_info['name'] == tag_name:
            return tag_info['commit']['sha']
    raise Exception(f"Tag info not found: '{tag_name}'")


def _get_github_branch_latest_commit_sha(repository_name, branch_name):
    url = f'https://api.github.com/repos/{repository_name}/branches/{branch_name}'
    response = requests.get(url)
    assert response.ok, url
    return response.json()['commit']['sha']


def _download_file(url, file_path):
    response = requests.get(url, stream=True)
    assert response.ok, url
    tmp_file_path = f'{file_path}.download'
    with open(tmp_file_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=512):
            if chunk is not None:
                file.write(chunk)
    os.rename(tmp_file_path, file_path)


def update_glyphs_version():
    if ark_pixel_config.source_type == 'tag':
        tag_name = ark_pixel_config.source_name
        if tag_name is None:
            tag_name = _get_github_releases_latest_tag_name(ark_pixel_config.repository_name)
        sha = _get_github_tag_sha(ark_pixel_config.repository_name, tag_name)
        version = tag_name
    elif ark_pixel_config.source_type == 'branch':
        branch_name = ark_pixel_config.source_name
        sha = _get_github_branch_latest_commit_sha(ark_pixel_config.repository_name, branch_name)
        version = branch_name
    elif ark_pixel_config.source_type == 'commit':
        sha = ark_pixel_config.source_name
        version = sha
    else:
        raise Exception(f"Unknown source type: '{ark_pixel_config.source_type}'")
    version_url = f'https://github.com/{ark_pixel_config.repository_name}/tree/{version}'
    asset_url = f'https://github.com/{ark_pixel_config.repository_name}/archive/{sha}.zip'
    version_info = {
        'sha': sha,
        'version': version,
        'version_url': version_url,
        'asset_url': asset_url,
    }
    version_info_file_path = os.path.join(path_define.glyphs_dir, 'version.json')
    with open(version_info_file_path, 'w', encoding='utf-8') as file:
        file.write(json.dumps(version_info, indent=2, ensure_ascii=False))
        file.write('\n')
    logger.info(f"Made version info file: '{version_info_file_path}'")


def setup_glyphs():
    version_info_file_path = os.path.join(path_define.glyphs_dir, 'version.json')
    with open(version_info_file_path, 'r', encoding='utf-8') as file:
        version_info = json.loads(file.read())

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
    with zipfile.ZipFile(source_file_path) as zip_file:
        zip_file.extractall(source_unzip_dir)
    logger.info(f"Unzipped: '{source_unzip_dir}'")

    fs_util.delete_dir(path_define.ark_pixel_glyphs_dir)
    sha = version_info['sha']
    source_glyphs_dir = os.path.join(source_unzip_dir, f'ark-pixel-font-{sha}', 'assets', 'glyphs')
    shutil.copytree(source_glyphs_dir, path_define.ark_pixel_glyphs_dir)
    fs_util.delete_dir(source_unzip_dir)
    logger.info(f"Updated font glyphs: '{sha}'")
