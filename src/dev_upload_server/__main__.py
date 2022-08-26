import argparse
import dataclasses
import html
import logging
import textwrap
from pathlib import Path
import secrets
import socket
from typing import List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Request, status, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn
import uvicorn.logging


def setup_logging():
    handler = logging.StreamHandler()
    bf = uvicorn.logging.ColourizedFormatter("{levelprefix} {name:^14s} {message}", style="{")
    handler.setFormatter(bf)
    # intercept everything at the root logger
    logging.root.handlers = [handler]
    logging.root.setLevel(logging.DEBUG)

    # remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True


logger = logging.getLogger(__name__)

app = FastAPI()

security = HTTPBasic()


@dataclasses.dataclass
class Config:
    username: str
    password: str
    use_security: bool
    save_dir: Path
    url: str


config: Config


def get_ip():
    """from https://stackoverflow.com/a/28950776"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


async def optional_security(request: Request):
    if config.use_security:
        return await security(request)
    else:
        return None


def get_current_username(credentials: Optional[HTTPBasicCredentials] = Depends(optional_security)):
    if config.use_security:
        correct_username = secrets.compare_digest(credentials.username, config.username)
        correct_password = secrets.compare_digest(credentials.password, config.password)
        if not (correct_username and correct_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials.username
    else:
        return "anonymous"


@app.post('/', status_code=status.HTTP_201_CREATED)
async def file_upload(username: str = Depends(get_current_username),
                      files: List[UploadFile] = File(...)):
    names = []
    for file in files:
        path = Path(file.filename)
        stem = path.stem
        suffix = path.suffix
        if username:
            stem = f"{username}_{stem}"
        output_path = config.save_dir / (stem + suffix)
        with output_path.open("wb") as wh:
            wh.write(await file.read())
            await file.close()
            logger.info(f"wrote file {file.filename} of type {file.content_type} to {output_path}")
            names.append(output_path.name)

    return {"names": names}


@app.get("/")
async def root():
    cli_str = " ".join(filter(None, [
        "curl",
        "-u 'username[:password]'" if config.use_security else None,
        config.url,
        "-F 'files=@/path/to/file1'",
        "[-F 'files=@/path/to/file2' ...]",
    ]))
    simple_cli_str = " ".join(filter(None, [
        r"""sed 's/\(.*\)/-F "files=@\1"/' <<EOF | tr '\n' ' ' | xargs -pr curl""",
        "-u 'username[:password]'" if config.use_security else None,
        config.url,
        "\n"
        "/path/to/file1\n"
        "/path/to/file2\n"
        "`ls *.txt`\n"
        "EOF"
    ]))
    content = f"""
<body>
<form action="/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
<pre>
{html.escape(cli_str)}
</pre>
<pre>
{html.escape(simple_cli_str)}
</pre>
</body>
    """
    return HTMLResponse(content=content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory", default="./",
                        help="directory to save uploaded files"
                             "to (DEFAULT: %(default)s)")
    parser.add_argument("-b", "--bind", default="0.0.0.0",
                        help="address to bind to (DEFAULT: %(default)s)")

    parser.add_argument("-p", "--port", type=int, default=5000, required=False,
                        help="port to serve at (DEFAULT: %(default)s)")
    security_group = parser.add_mutually_exclusive_group(required=True)
    security_group.add_argument("--no-security", dest="security",
                                action="store_false", help="don't use any security")
    security_group.add_argument("-u", "--user", type=str,
                                help="require basic auth; 'username:password'")

    args = parser.parse_args()

    save_dir = Path(args.directory).resolve()
    if not save_dir.exists() or not save_dir.is_dir():
        parser.error(f"--directory: {save_dir} is not a directory")

    if args.security:
        parts = args.user.split(":")
        if len(parts) != 2:
            parser.error(f"--user: not in expected form: 'username:password'")
            raise SystemExit(1)
        else:
            username, password = parts
    else:
        username, password = None, None

    server_config = uvicorn.Config(app, host=args.bind, port=args.port)
    server = uvicorn.Server(config=server_config)

    setup_logging()
    logger.info(f"Will be saving files to {save_dir}")
    url = f"http://{get_ip()}:{args.port}/"

    usage_str = " ".join(filter(None, [
        "cli usage:\n",
        "curl",
        f"-u '{username}:{password}'" if args.security else None,
        url,
        "-F 'files=@/path/to/file1'",
        "[-F 'files=@/path/to/file2' ...]\n",
    ]))

    simple_usage_str = " ".join(filter(None, [
        "simple cli usage:\n"
        r"""sed 's/\(.*\)/-F "files=@\1"/' <<EOF | tr '\n' ' ' | xargs -pr curl""",
        f"-u '{username}:{password}'" if args.security else None,
        url,
        "\n"
        "/path/to/file1\n"
        "/path/to/file2\n"
        "`ls *.txt`\n"
        "EOF"
    ]))
    logger.info(usage_str)
    logger.info(simple_usage_str)

    global config
    config = Config(username=username, password=password,
                    use_security=args.security, save_dir=save_dir, url=url)
    server.run()


if __name__ == "__main__":
    main()
