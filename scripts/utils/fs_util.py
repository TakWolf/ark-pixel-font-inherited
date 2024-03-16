import json
import os
import shutil
import tomllib

import yaml


def make_dir(path: str | bytes | os.PathLike[str] | os.PathLike[bytes]):
    if os.path.exists(path):
        if not os.path.isdir(path):
            raise Exception(f"Path exists but not a directory: '{path}'")
    else:
        os.makedirs(path)


def delete_dir(path: str | bytes | os.PathLike[str] | os.PathLike[bytes]):
    if os.path.exists(path):
        if not os.path.isdir(path):
            raise Exception(f"Path not a directory: '{path}'")
        shutil.rmtree(path)


def read_str(path: str | bytes | os.PathLike[str] | os.PathLike[bytes]) -> str:
    with open(path, 'r', encoding='utf-8') as file:
        return file.read()


def write_str(text: str, path: str | bytes | os.PathLike[str] | os.PathLike[bytes]):
    with open(path, 'w', encoding='utf-8') as file:
        file.write(text)


def read_json(path: str | bytes | os.PathLike[str] | os.PathLike[bytes]) -> dict:
    return json.loads(read_str(path))


def write_json(data: dict, path: str | bytes | os.PathLike[str] | os.PathLike[bytes]):
    write_str(json.dumps(data, indent=2, ensure_ascii=False), path)


def read_toml(path: str | bytes | os.PathLike[str] | os.PathLike[bytes]) -> dict:
    return tomllib.loads(read_str(path))


def read_yaml(path: str | bytes | os.PathLike[str] | os.PathLike[bytes]) -> dict:
    return yaml.safe_load(read_str(path))
