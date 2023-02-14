import logging

from services import update_service

logging.basicConfig(level=logging.DEBUG)


def main():
    update_service.download_glyphs_source()
    update_service.update_glyphs()


if __name__ == '__main__':
    main()
