import os
import datetime
from pathlib import Path
from ftplib import FTP_TLS
from typing import List, Optional

class WebspaceClient:
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self.ftp: Optional[FTP_TLS] = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()

    def connect(self):
        if self.ftp is None:
            self.ftp = FTP_TLS()
            self.ftp.connect(self.host)
            self.ftp.login(self.username, self.password)
            self.ftp.prot_p()

    def quit(self):
        if self.ftp is not None:
            try:
                self.ftp.quit()
            except Exception:
                self.ftp.close()
            self.ftp = None

    def ensure_remote_dir(self, remote_dir: str) -> None:
        """
        Recursively creates directories on the remote server (mkdir -p).
        """
        if not self.ftp:
            self.connect()

        original_cwd = self.ftp.pwd()
        try:
            parts = [p for p in remote_dir.split("/") if p]
            for part in parts:
                try:
                    self.ftp.cwd(part)
                except Exception:
                    self.ftp.mkd(part)
                    self.ftp.cwd(part)
        finally:
            self.ftp.cwd(original_cwd)

    def upload(self, local_path: Path, remote_dir: str) -> None:
        """
        Uploads a file to the remote server.
        """
        if not self.ftp:
            self.connect()

        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        self.ensure_remote_dir(remote_dir)

        original_cwd = self.ftp.pwd()
        try:
            self.ftp.cwd(remote_dir)
            with open(local_path, "rb") as f:
                self.ftp.storbinary(f"STOR {local_path.name}", f)
        finally:
            self.ftp.cwd(original_cwd)

    def ls(self, remote_dir: str = ".") -> List[str]:
        """
        Lists files in the remote directory.
        """
        if not self.ftp:
            self.connect()

        files = []
        self.ftp.retrlines(f"NLST {remote_dir}", files.append)
        return files

    def push(
        self,
        local_dir: Path,
        remote_dir: str,
        recursive: bool = False,
        callback=None
    ) -> None:
        """
        Pushes new or updated files from local_dir to remote_dir.
        """
        if not self.ftp:
            self.connect()

        if not local_dir.is_dir():
            raise ValueError(f"Local path is not a directory: {local_dir}")

        # Get remote files and their modification times
        remote_files = {}
        try:
            for name, facts in self.ftp.mlsd(remote_dir):
                if facts["type"] == "file":
                    # modify: timestamp in YYYYMMDDHHMMSS format
                    remote_files[name] = facts.get("modify")
        except Exception:
            # Fallback if MLSD is not supported
            try:
                names = self.ls(remote_dir)
                for name in names:
                    try:
                        timestamp = self.ftp.voidcmd(f"MDTM {remote_dir}/{name}").split()[1]
                        remote_files[name] = timestamp
                    except Exception:
                        remote_files[name] = None
            except Exception:
                # remote_dir might not exist
                pass

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
                        remote_dt = datetime.datetime.strptime(remote_mtime_str[:14], "%Y%m%d%H%M%S").replace(tzinfo=datetime.timezone.utc)
                        remote_mtime = remote_dt.timestamp()
                        # Local mtime is usually more precise.
                        # If local is strictly newer, upload.
                        if local_mtime > remote_mtime:
                            should_upload = True
                    except Exception:
                        # If we can't parse timestamp, assume we should upload to be safe?
                        # Or maybe not. Let's assume if we can't compare, we don't overwrite if it exists.
                        pass

                if should_upload:
                    if callback:
                        callback(f"Uploading {entry.path} to {remote_dir}")
                    self.upload(Path(entry.path), remote_dir)
                else:
                    if callback:
                        callback(f"Skipping {entry.name} (already up to date)")

            elif entry.is_dir() and recursive:
                new_remote_dir = f"{remote_dir}/{entry.name}".replace("//", "/")
                self.push(Path(entry.path), new_remote_dir, recursive=True, callback=callback)
