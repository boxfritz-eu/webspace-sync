import os
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
