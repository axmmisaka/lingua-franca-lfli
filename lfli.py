import argparse
import logging
import requests
import tarfile
import pathlib
import platform
import re
import os

logging.basicConfig()
logging.root.setLevel(logging.NOTSET)
logger = logging.getLogger("Main-logger")
logger.setLevel(logging.DEBUG)


class Lfli():
    def __init__(self):
        if (dir := os.getenv("LFLI_DIR")) is not None:
            self.dir = dir
        else:
            self.dir = "/home/keketang/lingua-franca-lfli/temp"

    def set_current(self, version: str):
        if version == "current":
            raise ValueError("version cannot be 'current', it is reserved")
        p = pathlib.Path(self.dir)
        if not (p / version).is_dir():
            raise FileNotFoundError(f"Version {version} not found.")
        # Only one directory should be in that directory and we use next to get it
        new_lf_bin = next((p / version).iterdir())
        current = p / "current"
        if current.exists():
            current.unlink()
        current.symlink_to(new_lf_bin, target_is_directory=True)
        logger.info(f"lf now: {current.resolve()}")

    def print_versions(self, ):
        p = pathlib.Path(self.dir)
        current: pathlib.Path | None = None
        if (curr := pathlib.Path(self.dir) / "current") and curr.is_symlink():
            current = curr.resolve().parent
        for x in p.iterdir():
            if x.is_dir() and x.name != "current":
                if current and x.samefile(current):
                    print("* ", end="")
                print(x.name)

    def install_lf_executable(self, version: str):
        def download_and_extract(url: str, destination: str | pathlib.Path):
            # https://stackoverflow.com/a/16696317
            # NOTE the stream=True parameter below
            logger.info(f"Downloading {url} to {destination}")
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                tar = tarfile.open(name=None, fileobj=r.raw)
                tar.extractall(destination, )

        def get_lf_url_and_real_version(version: str) -> tuple[str, str]:
            API_URL = "https://api.github.com/repos/lf-lang/lingua-franca/releases/"
            STABLE_LATEST_JSON_URI = "latest"
            NIGHTLY_JSON_URI = "tags/nightly"
            STABLE_TAG_JSON_FORMAT_URI = "tags/{0}"

            metadata_json_url: str
            # This kinda redundant as of now, but I'm keeping it for future use
            channel: str

            if version == "stable":
                logger.info("Using latest stable.")
                metadata_json_url = f"{API_URL}{STABLE_LATEST_JSON_URI}"
                channel = "stable"
            elif version[0] == 'v':
                logger.info(
                    "v in version string detected; Using stable; version %s.", version)
                metadata_json_url = f"{API_URL}{STABLE_TAG_JSON_FORMAT_URI.format(version)}"
                channel = "stable"
            elif version == "nightly":
                logger.info("Using nightly.")
                metadata_json_url = f"{API_URL}{NIGHTLY_JSON_URI}"
                channel = "nightly"
            elif len(version) == 8 and version.isdecimal():
                raise NotImplementedError(
                    "It appears that you supplied a nightly version number, but downloading a specific nightly version is not supported yet.")
            else:
                raise ValueError("Supplied version not valid.")

            logger.info("Using URL %s", metadata_json_url)
            r = requests.get(url=metadata_json_url)
            if not r.ok:
                raise IOError(
                    f"Response has non-200 status code: {r.status_code}. If 404, it is possible that you entered a version number that does not exist.")
            gh_response_json = r.json()

            # Get URL of the tar.gz that looks like lf-*.gar.gz

            # In older versions they are like "lfc_0.3.0.tar.gz"; in newer versions they are like "lf-cli-0.4.0.tar.gz"
            if channel == "stable":
                for asset in gh_response_json["assets"]:
                    if asset["name"].startswith("lf") and asset["name"].endswith(".tar.gz"):
                        return (asset["browser_download_url"], gh_response_json["tag_name"])
            elif channel == "nightly":
                os_name = platform.system().lower()
                os_name = os_name if os_name != "darwin" else "macos"
                arch_map = {"amd64": "x86_64",
                            "x64": "x86_64", "arm64": "aarch64"}
                arch_name = platform.machine().lower()
                if arch_name.lower() in arch_map:
                    arch_name = arch_map[arch_name]
                for asset in gh_response_json["assets"]:
                    if asset["name"].startswith("lf") and asset["name"].endswith(".tar.gz") \
                            and os_name in asset["name"].lower() and arch_name in asset["name"].lower():
                        return (asset["browser_download_url"], re.search(r"\d{8}", asset["name"])[0])
            raise ValueError("The specified url/arch could not be found")

        url, ver = get_lf_url_and_real_version(version)
        download_and_extract(url, pathlib.Path(self.dir) / ver)

    def main(self, args: argparse.Namespace):
        match args.subcommand_name:
            case "install":
                self.install_lf_executable(args.version)
            case "use":
                self.set_current(args.version)
            case "list":
                self.print_versions()
            case _:
                raise NotImplementedError("not implemented")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="lfli",
        description="Lingua Franca Language Instructor, the Lingua Franca Version Manager and Installer",
        epilog="Copyright (c) 2023, the Lingua Franca contributors."
    )

    subparser = parser.add_subparsers(dest="subcommand_name")
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
    subparsers["cache"].add_argument(
        "action", choices=["dir", "clean", "purge"])

    args = parser.parse_args()
    print(args,)

    lfli = Lfli()
    lfli.main(args)
