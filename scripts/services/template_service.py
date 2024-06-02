import logging
import random

import bs4
from jinja2 import Environment, FileSystemLoader

from scripts import configs
from scripts.configs import path_define
from scripts.services.font_service import DesignContext

logger = logging.getLogger('template_service')

_environment = Environment(
    trim_blocks=True,
    lstrip_blocks=True,
    loader=FileSystemLoader(path_define.templates_dir),
)

_build_random_key = random.random()


def _make_html_file(template_name: str, file_name: str, params: dict[str, object] = None):
    params = {} if params is None else dict(params)
    params['build_random_key'] = _build_random_key
    params['font_configs'] = configs.font_configs
    params['width_modes'] = configs.width_modes

    html = _environment.get_template(template_name).render(params)

    path_define.outputs_dir.mkdir(parents=True, exist_ok=True)
    file_path = path_define.outputs_dir.joinpath(file_name)
    file_path.write_text(html, 'utf-8')
    logger.info("Make html file: '%s'", file_path)


def make_alphabet_html_file(design_context: DesignContext, width_mode: str):
    _make_html_file('alphabet.html', f'alphabet-{design_context.font_config.font_size}px-{width_mode}.html', {
        'font_config': design_context.font_config,
        'width_mode': width_mode,
        'alphabet': ''.join(sorted([c for c in design_context.get_alphabet(width_mode) if ord(c) >= 128])),
    })


def _handle_demo_html_element(design_context: DesignContext, soup: bs4.BeautifulSoup, element: bs4.PageElement):
    if isinstance(element, bs4.element.Tag):
        for child_element in list(element.contents):
            _handle_demo_html_element(design_context, soup, child_element)
    elif isinstance(element, bs4.element.NavigableString):
        alphabet_monospaced = design_context.get_alphabet('monospaced')
        alphabet_proportional = design_context.get_alphabet('proportional')
        text = str(element)
        tmp_parent = soup.new_tag('div')
        last_status = None
        text_buffer = ''
        for c in text:
            if c == ' ':
                status = last_status
            elif c == '\n':
                status = 'all'
            elif c in alphabet_monospaced and c in alphabet_proportional:
                status = 'all'
            elif c in alphabet_monospaced:
                status = 'monospaced'
            elif c in alphabet_proportional:
                status = 'proportional'
            else:
                status = None
            if last_status != status:
                if text_buffer != '':
                    if last_status == 'all':
                        tmp_child = bs4.element.NavigableString(text_buffer)
                    else:
                        tmp_child = soup.new_tag('span')
                        tmp_child.string = text_buffer
                        if last_status == 'monospaced':
                            tmp_child['class'] = f'char-notdef-proportional'
                        elif last_status == 'proportional':
                            tmp_child['class'] = f'char-notdef-monospaced'
                        else:
                            tmp_child['class'] = f'char-notdef-monospaced char-notdef-proportional'
                    tmp_parent.append(tmp_child)
                    text_buffer = ''
                last_status = status
            text_buffer += c
        if text_buffer != '':
            if last_status == 'all':
                tmp_child = bs4.element.NavigableString(text_buffer)
            else:
                tmp_child = soup.new_tag('span')
                tmp_child.string = text_buffer
                if last_status == 'monospaced':
                    tmp_child['class'] = f'char-notdef-proportional'
                elif last_status == 'proportional':
                    tmp_child['class'] = f'char-notdef-monospaced'
                else:
                    tmp_child['class'] = f'char-notdef-monospaced char-notdef-proportional'
            tmp_parent.append(tmp_child)
        element.replace_with(tmp_parent)
        tmp_parent.unwrap()


def make_demo_html_file(design_context: DesignContext):
    content_html = path_define.templates_dir.joinpath('demo-content.html').read_text('utf-8')
    content_html = ''.join(line.strip() for line in content_html.split('\n'))
    soup = bs4.BeautifulSoup(content_html, 'html.parser')
    _handle_demo_html_element(design_context, soup, soup)
    content_html = str(soup)

    _make_html_file('demo.html', f'demo-{design_context.font_config.font_size}px.html', {
        'font_config': design_context.font_config,
        'content_html': content_html,
    })


def make_index_html_file():
    _make_html_file('index.html', 'index.html')


def make_playground_html_file():
    _make_html_file('playground.html', 'playground.html')
