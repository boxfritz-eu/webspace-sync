import pytest
from unittest.mock import patch
from webspace_sync.client import WebspaceClient


@pytest.fixture
def mock_ftp():
    with patch("webspace_sync.client.FTP_TLS") as mock:
        yield mock.return_value


def test_client_connect(mock_ftp):
    client = WebspaceClient("host", "user", "pass")
    client.connect()

    mock_ftp.connect.assert_called_once_with("host")
    mock_ftp.login.assert_called_once_with("user", "pass")
    mock_ftp.prot_p.assert_called_once()


def test_client_ls(mock_ftp):
    mock_ftp.retrlines.side_effect = lambda cmd, callback: [
        callback(f) for f in ["file1.txt", "file2.txt"]
    ]

    client = WebspaceClient("host", "user", "pass")
    files = client.ls("some_dir")

    assert files == ["file1.txt", "file2.txt"]
    mock_ftp.retrlines.assert_called_once()
    assert "NLST some_dir" in mock_ftp.retrlines.call_args[0][0]


def test_client_ensure_remote_dir(mock_ftp):
    mock_ftp.pwd.return_value = "/"
    # Simulate directory exists first then doesn't
    mock_ftp.cwd.side_effect = [None, Exception("Not found"), None, None]

    client = WebspaceClient("host", "user", "pass")
    client.ensure_remote_dir("a/b")

    assert mock_ftp.mkd.call_count == 1
    mock_ftp.mkd.assert_called_with("b")
    # Check it returns to original cwd
    mock_ftp.cwd.assert_any_call("/")


def test_client_upload(mock_ftp, tmp_path):
    mock_ftp.pwd.return_value = "/"
    local_file = tmp_path / "test.txt"
    local_file.write_text("hello")

    client = WebspaceClient("host", "user", "pass")
    client.upload(local_file, "remote/path")

    mock_ftp.storbinary.assert_called_once()
    assert "STOR test.txt" in mock_ftp.storbinary.call_args[0][0]
    mock_ftp.cwd.assert_any_call("remote/path")


def test_client_push_new_file(mock_ftp, tmp_path):
    mock_ftp.pwd.return_value = "/"
    mock_ftp.mlsd.return_value = []  # No remote files

    local_dir = tmp_path / "local"
    local_dir.mkdir()
    (local_dir / "new.txt").write_text("content")

    client = WebspaceClient("host", "user", "pass")
    client.push(local_dir, "remote")

    mock_ftp.storbinary.assert_called_once()
    assert "STOR new.txt" in mock_ftp.storbinary.call_args[0][0]


def test_client_push_existing_file_newer(mock_ftp, tmp_path):
    mock_ftp.pwd.return_value = "/"
    # Remote file is from 2020
    mock_ftp.mlsd.return_value = [
        ("old.txt", {"type": "file", "modify": "20200101000000"})
    ]

    local_dir = tmp_path / "local"
    local_dir.mkdir()
    local_file = local_dir / "old.txt"
    local_file.write_text("newer content")
    # Ensure local mtime is newer than 2020

    client = WebspaceClient("host", "user", "pass")
    client.push(local_dir, "remote")

    mock_ftp.storbinary.assert_called_once()


def test_client_push_existing_file_older(mock_ftp, tmp_path):
    mock_ftp.pwd.return_value = "/"
    # Remote file is from 2030 (future)
    mock_ftp.mlsd.return_value = [
        ("future.txt", {"type": "file", "modify": "20300101000000"})
    ]

    local_dir = tmp_path / "local"
    local_dir.mkdir()
    local_file = local_dir / "future.txt"
    local_file.write_text("older content")

    client = WebspaceClient("host", "user", "pass")
    client.push(local_dir, "remote")

    mock_ftp.storbinary.assert_not_called()


def test_client_push_recursive(mock_ftp, tmp_path):
    mock_ftp.pwd.return_value = "/"
    mock_ftp.mlsd.side_effect = [[], []]  # Empty for both dirs

    local_dir = tmp_path / "local"
    local_dir.mkdir()
    sub_dir = local_dir / "sub"
    sub_dir.mkdir()
    (sub_dir / "subfile.txt").write_text("content")

    client = WebspaceClient("host", "user", "pass")
    client.push(local_dir, "remote", recursive=True)

    mock_ftp.storbinary.assert_called_once()
    assert "STOR subfile.txt" in mock_ftp.storbinary.call_args[0][0]
    mock_ftp.cwd.assert_any_call("remote/sub")


def test_client_download(mock_ftp, tmp_path):
    client = WebspaceClient("host", "user", "pass")
    client.download("remote/path/file.txt", tmp_path)

    mock_ftp.retrbinary.assert_called_once()
    assert "RETR remote/path/file.txt" in mock_ftp.retrbinary.call_args[0][0]
    assert (tmp_path / "file.txt").exists()


def test_client_pull_new_file(mock_ftp, tmp_path):
    mock_ftp.mlsd.return_value = [
        ("new.txt", {"type": "file", "modify": "20200101000000"})
    ]

    local_dir = tmp_path / "local"
    # Local dir doesn't exist yet, pull should create it

    client = WebspaceClient("host", "user", "pass")
    client.pull("remote", local_dir)

    mock_ftp.retrbinary.assert_called_once()
    assert "RETR remote/new.txt" in mock_ftp.retrbinary.call_args[0][0]
    assert (local_dir / "new.txt").exists()


def test_client_pull_existing_file_newer(mock_ftp, tmp_path):
    # Remote file is from 2030 (future)
    mock_ftp.mlsd.return_value = [
        ("file.txt", {"type": "file", "modify": "20300101000000"})
    ]

    local_dir = tmp_path / "local"
    local_dir.mkdir()
    local_file = local_dir / "file.txt"
    local_file.write_text("old content")
    # Local mtime will be "now", which is before 2030

    client = WebspaceClient("host", "user", "pass")
    client.pull("remote", local_dir)

    mock_ftp.retrbinary.assert_called_once()


def test_client_pull_existing_file_older(mock_ftp, tmp_path):
    # Remote file is from 2020
    mock_ftp.mlsd.return_value = [
        ("file.txt", {"type": "file", "modify": "20200101000000"})
    ]

    local_dir = tmp_path / "local"
    local_dir.mkdir()
    local_file = local_dir / "file.txt"
    local_file.write_text("new content")
    # Local mtime is "now", which is after 2020

    client = WebspaceClient("host", "user", "pass")
    client.pull("remote", local_dir)

    mock_ftp.retrbinary.assert_not_called()


def test_client_pull_recursive(mock_ftp, tmp_path):
    mock_ftp.mlsd.side_effect = [
        [("sub", {"type": "dir"})],
        [("subfile.txt", {"type": "file", "modify": "20200101000000"})],
    ]

    local_dir = tmp_path / "local"

    client = WebspaceClient("host", "user", "pass")
    client.pull("remote", local_dir, recursive=True)

    mock_ftp.retrbinary.assert_called_once()
    assert "RETR remote/sub/subfile.txt" in mock_ftp.retrbinary.call_args[0][0]
    assert (local_dir / "sub" / "subfile.txt").exists()


def test_client_sync(mock_ftp, tmp_path):
    mock_ftp.mlsd.return_value = []
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    (local_dir / "file.txt").write_text("content")

    client = WebspaceClient("host", "user", "pass")
    with (
        patch.object(client, "push") as mock_push,
        patch.object(client, "pull") as mock_pull,
    ):
        client.sync(local_dir, "remote")

        mock_push.assert_called_once_with(
            local_dir, "remote", recursive=False, callback=None
        )
        mock_pull.assert_called_once_with(
            "remote", local_dir, recursive=False, callback=None
        )
