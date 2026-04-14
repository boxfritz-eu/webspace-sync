import argparse
import os
import sys
from pathlib import Path
from box import Box

from .client import WebspaceClient

__all__ = ["WebspaceClient"]

def load_secrets(path: str = "config/secrets.yaml") -> Box:
    """
    Loads and returns the secrets from a YAML file.
    """
    if not os.path.exists(path):
        print(f"Error: Secrets file not found at {path}", file=sys.stderr)
        sys.exit(1)
    try:
        return Box.from_yaml(filename=path)
    except Exception as e:
        print(f"Failed to load secrets from {path}: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Webspace sync tool for uploading files and listing directories"
    )
    parser.add_argument(
        "--secrets",
        "-s",
        default="config/secrets.yaml",
        help="Path to the secrets YAML file (default: config/secrets.yaml)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload a file")
    upload_parser.add_argument(
        "file",
        help="Path to the file to upload",
    )
    upload_parser.add_argument(
        "--remote-dir",
        "-d",
        default="data/raw",
        help="Remote directory to upload to (default: data/raw)",
    )

    # Ls command
    ls_parser = subparsers.add_parser("ls", help="List files in a remote directory")
    ls_parser.add_argument(
        "remote_dir",
        nargs="?",
        default=".",
        help="Remote directory to list (default: .)",
    )

    # Push command
    push_parser = subparsers.add_parser("push", help="Push new or updated files to a remote directory")
    push_parser.add_argument(
        "source",
        help="Local directory to push from",
    )
    push_parser.add_argument(
        "target",
        help="Remote directory to push to",
    )
    push_parser.add_argument(
        "--recurse",
        "-R",
        action="store_true",
        help="Push directories recursively",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    secrets = load_secrets(args.secrets)
    ftp_conf = secrets.webspace.ftp

    client = WebspaceClient(
        host=ftp_conf.host,
        username=ftp_conf.username,
        password=ftp_conf.password
    )

    try:
        with client:
            if args.command == "upload":
                client.upload(Path(args.file), args.remote_dir)
                print(f"Successfully uploaded {args.file} to {args.remote_dir}")
            elif args.command == "ls":
                files = client.ls(args.remote_dir)
                for f in files:
                    print(f)
            elif args.command == "push":
                client.push(
                    Path(args.source),
                    args.target,
                    recursive=args.recurse,
                    callback=print
                )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
