import os
import datetime
from pathlib import Path
from ftplib import FTP_TLS  # nosec: B402
from typing import List, Optional


class WebspaceClient:
    """A client for interacting with a webspace via FTP_TLS.

    Attributes:
        host: The FTP server host.
        username: The FTP username.
        password: The FTP password.
        ftp: The underlying FTP_TLS object.
    """

    def __init__(self, host: str, username: str, password: str):
        """Initializes the WebspaceClient.

        Args:
            host: The FTP server host.
            username: The FTP username.
            password: The FTP password.
        """
        self.host = host
        self.username = username
        self.password = password
        self.ftp: Optional[FTP_TLS] = None

    def __enter__(self) -> "WebspaceClient":
        """Enters the runtime context related to this object.

        Returns:
            The WebspaceClient instance.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exits the runtime context related to this object.

        Args:
            exc_type: The exception type.
            exc_val: The exception value.
            exc_tb: The traceback.
        """
        self.quit()

    def connect(self) -> FTP_TLS:
        """Connects to the FTP server and logs in.

        Returns:
            The connected FTP_TLS instance.
        """
        if self.ftp is None:
            self.ftp = FTP_TLS()
            self.ftp.connect(self.host)
            self.ftp.login(self.username, self.password)
            self.ftp.prot_p()
        return self.ftp

    def quit(self) -> None:
        """Gracefully closes the FTP connection."""
        if self.ftp is not None:
            try:
                self.ftp.quit()
            except Exception:
                self.ftp.close()
            self.ftp = None

    def ensure_remote_dir(self, remote_dir: str) -> None:
        """Recursively creates directories on the remote server (mkdir -p).

        Args:
            remote_dir: The remote directory path to ensure.
        """
        ftp = self.connect()

        original_cwd = ftp.pwd()
        try:
            parts = [p for p in remote_dir.split("/") if p]
            for part in parts:
                try:
                    ftp.cwd(part)
                except Exception:
                    ftp.mkd(part)
                    ftp.cwd(part)
        finally:
            ftp.cwd(original_cwd)

    def upload(self, local_path: Path, remote_dir: str) -> None:
        """Uploads a file to the remote server.

        Args:
            local_path: The path to the local file to upload.
            remote_dir: The remote directory to upload to.

        Raises:
            FileNotFoundError: If the local file does not exist.
        """
        ftp = self.connect()

        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        self.ensure_remote_dir(remote_dir)

        original_cwd = ftp.pwd()
        try:
            ftp.cwd(remote_dir)
            with open(local_path, "rb") as f:
                ftp.storbinary(f"STOR {local_path.name}", f)
        finally:
            ftp.cwd(original_cwd)

    def download(self, remote_path: str, local_dir: Path) -> None:
        """Downloads a file from the remote server.

        Args:
            remote_path: The path to the remote file to download.
            local_dir: The local directory to download to.
        """
        ftp = self.connect()

        local_dir.mkdir(parents=True, exist_ok=True)
        filename = os.path.basename(remote_path)
        local_path = local_dir / filename

        with open(local_path, "wb") as f:
            ftp.retrbinary(f"RETR {remote_path}", f.write)

    def ls(self, remote_dir: str = ".") -> List[str]:
        """Lists files in the remote directory.

        Args:
            remote_dir: The remote directory to list. Defaults to ".".

        Returns:
            A list of filenames in the directory.
        """
        ftp = self.connect()

        files: List[str] = []
        ftp.retrlines(f"NLST {remote_dir}", files.append)
        return files

    def push(
        self,
        local_dir: Path,
        remote_dir: str,
        recursive: bool = False,
        callback=None,
    ) -> None:
        """Pushes new or updated files from local_dir to remote_dir.

        Args:
            local_dir: The local directory to push from.
            remote_dir: The remote directory to push to.
            recursive: Whether to push directories recursively. Defaults to False.
            callback: An optional callback function for logging progress.
        """
        ftp = self.connect()

        if not local_dir.is_dir():
            raise ValueError(f"Local path is not a directory: {local_dir}")

        # Get remote files and their modification times
        remote_files = {}
        try:
            for name, facts in ftp.mlsd(remote_dir):
                if facts["type"] == "file":
                    # modify: timestamp in YYYYMMDDHHMMSS format
                    remote_files[name] = facts.get("modify")
        except Exception:
            # Fallback if MLSD is not supported
            try:
                names = self.ls(remote_dir)
                for name in names:
                    try:
                        timestamp = ftp.voidcmd(f"MDTM {remote_dir}/{name}").split()[1]
                        remote_files[name] = timestamp
                    except Exception:
                        remote_files[name] = None
            except Exception:
                # remote_dir might not exist
                pass  # nosec: B110

        for entry in os.scandir(local_dir):
            if entry.is_file():
                local_mtime = int(entry.stat().st_mtime)
                # Convert local mtime to YYYYMMDDHHMMSS for comparison if needed
                # Or compare with remote if we can get a comparable format.
                # Actually, many FTP servers return UTC in MLSD.

                # Let's use a simpler approach: if it exists, compare.
                # For robustness, we might want to convert both to datetime objects.

                remote_mtime_str = remote_files.get(entry.name)
                should_upload = False

                if entry.name not in remote_files:
                    should_upload = True
                elif remote_mtime_str:
                    # MLSD format: YYYYMMDDHHMMSS[.sss]
                    try:
                        remote_dt = datetime.datetime.strptime(
                            remote_mtime_str[:14], "%Y%m%d%H%M%S"
                        ).replace(tzinfo=datetime.timezone.utc)
                        remote_mtime = remote_dt.timestamp()
                        # Local mtime is usually more precise.
                        # If local is strictly newer, upload.
                        if local_mtime > remote_mtime:
                            should_upload = True
                    except Exception:
                        # If we can't parse timestamp, assume we should upload to be safe?
                        # Or maybe not. Let's assume if we can't compare, we don't overwrite if it exists.
                        pass  # nosec: B110

                if should_upload:
                    if callback:
                        callback(f"Uploading {entry.path} to {remote_dir}")
                    self.upload(Path(entry.path), remote_dir)
                else:
                    if callback:
                        callback(f"Skipping {entry.name} (already up to date)")

            elif entry.is_dir() and recursive:
                new_remote_dir = f"{remote_dir}/{entry.name}".replace("//", "/")
                self.push(
                    Path(entry.path), new_remote_dir, recursive=True, callback=callback
                )

    def pull(
        self,
        remote_dir: str,
        local_dir: Path,
        recursive: bool = False,
        callback=None,
    ) -> None:
        """Pulls new or updated files from remote_dir to local_dir.

        Args:
            remote_dir: The remote directory to pull from.
            local_dir: The local directory to pull to.
            recursive: Whether to pull directories recursively. Defaults to False.
            callback: An optional callback function for logging progress.
        """
        ftp = self.connect()

        local_dir.mkdir(parents=True, exist_ok=True)

        try:
            entries = list(ftp.mlsd(remote_dir))
        except Exception:
            # Fallback if MLSD is not supported
            try:
                names = self.ls(remote_dir)
                entries = []
                for name in names:
                    if name in (".", ".."):
                        continue
                    # Try to determine if it's a directory
                    original_cwd = ftp.pwd()
                    is_dir = False
                    try:
                        ftp.cwd(f"{remote_dir}/{name}")
                        is_dir = True
                        ftp.cwd(original_cwd)
                    except Exception:  # nosec: B110
                        pass

                    if is_dir:
                        entries.append((name, {"type": "dir"}))
                    else:
                        modify: Optional[str] = None
                        try:
                            modify = ftp.voidcmd(f"MDTM {remote_dir}/{name}").split()[1]
                        except Exception:  # nosec: B110
                            pass
                        entries.append((name, {"type": "file", "modify": modify or ""}))
            except Exception:
                entries = []

        for name, facts in entries:
            if name in (".", ".."):
                continue

            if facts.get("type") == "file":
                local_path = local_dir / name
                remote_mtime_str = facts.get("modify")
                should_download = False

                if not local_path.exists():
                    should_download = True
                elif remote_mtime_str:
                    try:
                        remote_dt = datetime.datetime.strptime(
                            remote_mtime_str[:14], "%Y%m%d%H%M%S"
                        ).replace(tzinfo=datetime.timezone.utc)
                        remote_mtime = remote_dt.timestamp()
                        local_mtime = local_path.stat().st_mtime
                        if remote_mtime > local_mtime:
                            should_download = True
                    except Exception:  # nosec: B110
                        pass

                if should_download:
                    if callback:
                        callback(f"Downloading {remote_dir}/{name} to {local_dir}")
                    self.download(f"{remote_dir}/{name}", local_dir)
                else:
                    if callback:
                        callback(f"Skipping {name} (already up to date)")

            elif facts.get("type") == "dir" and recursive:
                new_remote_dir = f"{remote_dir}/{name}".replace("//", "/")
                new_local_dir = local_dir / name
                self.pull(
                    new_remote_dir, new_local_dir, recursive=True, callback=callback
                )
