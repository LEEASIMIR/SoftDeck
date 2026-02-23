import sys


def main() -> int:
    from src.app import SteamDeckSoftApp

    app = SteamDeckSoftApp(sys.argv)

    if app.already_running:
        print("SteamDeckSoft is already running.")
        return 1

    try:
        exit_code = app.exec()
    finally:
        app.cleanup()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
