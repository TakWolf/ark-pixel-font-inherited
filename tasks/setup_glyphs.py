import logging

from services import update_service

logging.basicConfig(level=logging.DEBUG)


def main():
    update_service.setup_glyphs()


if __name__ == '__main__':
    main()
