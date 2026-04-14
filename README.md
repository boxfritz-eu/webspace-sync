# Webspace Sync

A tool to synchronize files with a remote webspace via FTP_TLS.

## Installation

```bash
uv sync
```

## Configuration

Create a `config/secrets.yaml` file with your FTP credentials:

```yaml
webspace:
  ftp:
    host: ftp.example.com
    username: your_username
    password: your_password
```

## Usage

### Command Line Interface

You can run the tool using `uv run webspace_sync`.

#### Upload a file

```bash
uv run webspace_sync upload path/to/local/file.json --remote-dir data/raw
```

#### List remote files

```bash
uv run webspace_sync ls data/raw
```

### Python API

You can also use the `WebspaceClient` in your Python code:

```python
from webspace_sync import WebspaceClient
from pathlib import Path

client = WebspaceClient(host="ftp.example.com", username="user", password="pass")

with client:
    client.upload(Path("local_file.txt"), "remote/dir")
    files = client.ls("remote/dir")
    print(files)
```

## Development

### Running tests

```bash
uv run pytest
```
