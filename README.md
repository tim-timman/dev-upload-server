# dev-upload-server

### Usage
```
usage: dev-upload-server [-h] [-d DIRECTORY] [-b BIND] [-p PORT] (--no-security | -u USER)

optional arguments:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        directory to save uploaded filesto (DEFAULT: ./)
  -b BIND, --bind BIND  address to bind to (DEFAULT: 0.0.0.0)
  -p PORT, --port PORT  port to serve at (DEFAULT: 5000)
  --no-security         don't use any security
  -u USER, --user USER  require basic auth; 'username:password'
```

## Development

### Environment Setup

Create a local virtualenv at the root of the repo:
```shell
python3.9 -m venv venv
venv/bin/pip install -U pip setuptools wheel
```
This will create a virtualenv at `venv/` and update dependencies.

> **Note:** on Windows the `venv/bin` directory is named `venv/Scripts`.
> Substitute where appropriate.

Activate the virtualenv:
```shell
source venv/bin/activate
```
> **Note:** from now on all commands are assumed to be run
> within the activated virtualenv.

Install the project in editable mode with dependencies and dev dependencies:
```shell
pip install -e '.[dev]'
```

When installed in the editable manner above, any code changes are immediately
reflected in the code. The only exception is if an entrypoint is changed.

### Building the package

The package is configured to be built with [Flit][flit] for simplicity.

```
flit build 
```

[flit]: https://flit.pypa.io/en/latest/
