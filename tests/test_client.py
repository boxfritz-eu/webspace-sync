import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
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
    mock_ftp.retrlines.side_effect = lambda cmd, callback: [callback(f) for f in ["file1.txt", "file2.txt"]]

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
