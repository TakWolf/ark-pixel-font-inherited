import json
from pathlib import Path
from typing import Any

import yaml


def read_json(path: Path) -> Any:
    return json.loads(path.read_text('utf-8'))


def write_json(data: Any, path: Path):
    path.write_text(f'{json.dumps(data, indent=2, ensure_ascii=False)}\n', 'utf-8')


def read_yaml(path: Path) -> Any:
    with path.open('rb') as file:
        return yaml.safe_load(file)
