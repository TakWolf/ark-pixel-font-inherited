import yaml

from tools.configs import path_define
from tools.services import format_service


def check_inherited_mapping():
    file_path = path_define.assets_dir.joinpath('inherited-mapping.yml')
    text = file_path.read_text('utf-8')
    assert text == format_service.dump_inherited_mapping(yaml.safe_load(text)), f"unformatted 'inherited-mapping.yml'"
