from scripts.services import update_service


def main():
    update_service.update_glyphs_version()
    update_service.setup_glyphs()


if __name__ == '__main__':
    main()
