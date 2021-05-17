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


### Development

#### Create virtual environment

```
python3.9 -m venv venv
```


#### Activate it

**Unix**:

```
source venv/bin/activate
```

**Windows**:

```
source venv/Scripts/activate
```

**Note!** From here on it is assumed that the virtual environment is activated.

#### Install in developer mode

In this mode any code changes are immediately reflected in the installation.

```
pip install -e .'[dev]' --no-binary :all:
```


### Build and distribute


#### Make sure tools are up to date

```
pip install -U pip setuptools wheel
```


#### Build it

```
python setup.py bdist_wheel
```

The file for distribution will be created in `./dist` with a name like 
`dev_upload_server-0.0.1-py3-none-any.whl`.

#### Distribute and install the `*.whl`

To install the build package, run:

```
pip install dev_upload_server-0.0.1-py3-none-any.whl
```
