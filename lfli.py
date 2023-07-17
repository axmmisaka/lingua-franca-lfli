import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="lfli",
        description="Lingua Franca Language Instructor, the Lingua Franca Version Manager and Installer",
        epilog="Copyright (c) 2023, the Lingua Franca contributors."
    )

    subparser = parser.add_subparsers()
    subparsers: dict[str, argparse.ArgumentParser] = {
        "install": subparser.add_parser("install"),
        "uninstall": subparser.add_parser("uninstall"),
        "use": subparser.add_parser("use"),
        "cache": subparser.add_parser("cache"),
        "list": subparser.add_parser("list"),
        "list-remote": subparser.add_parser("list-remote"),
    }
    subparsers["install"].add_argument("version", default="stable", nargs="?")
    subparsers["uninstall"].add_argument("version")
    subparsers["use"].add_argument("version", default="stable", nargs="?")
    subparsers["cache"].add_argument("action", choices=["dir", "purge"])

    args = parser.parse_args()
    print(args)

