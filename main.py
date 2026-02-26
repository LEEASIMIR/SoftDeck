import sys


def main() -> int:
    from src.app import SteamDeckSoftApp

    app = SteamDeckSoftApp(sys.argv)

    try:
        exit_code = app.exec()
    finally:
        app.cleanup()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
