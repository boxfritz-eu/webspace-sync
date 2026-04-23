# Webspace Sync

A tool to synchronize files with a remote webspace via FTP_TLS.

![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)
[![Ruff](https://github.com/boxfritz-eu/webspace-sync/actions/workflows/lint.yml/badge.svg)](https://github.com/boxfritz-eu/webspace-sync/actions/workflows/lint.yml)
[![Tests](https://github.com/boxfritz-eu/webspace-sync/actions/workflows/tests.yml/badge.svg)](https://github.com/boxfritz-eu/webspace-sync/actions/workflows/tests.yml)

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

#### Push a directory

```bash
uv run webspace_sync push ./local_dir data/remote_dir --recurse
```

This command will only upload files that are new or have a newer timestamp than the remote version.

#### Sync a directory (bidirectional)

```bash
uv run webspace_sync sync ./local_dir data/remote_dir --recurse
```

This command performs a `push` followed by a `pull`.

### Python API

You can also use the `WebspaceClient` in your Python code:

```python
from webspace_sync import WebspaceClient
from pathlib import Path

client = WebspaceClient(host="ftp.example.com", username="user", password="pass")

with client:
    client.upload(Path("local_file.txt"), "remote/dir")
    client.push(Path("./local_dir"), "remote/dir", recursive=True, callback=print)
    client.sync(Path("./local_dir"), "remote/dir", recursive=True, callback=print)
    files = client.ls("remote/dir")
    print(files)
```

## Development

### Running tests

```bash
uv run pytest
```
