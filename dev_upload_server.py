import argparse
import logging
from pathlib import Path
import secrets
import socket
import sys
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, status, UploadFile
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


def get_ip():
    """from https://stackoverflow.com/a/28950776"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    if args.no_security:
        return ""
    else:
        correct_username = secrets.compare_digest(credentials.username, username)
        correct_password = secrets.compare_digest(credentials.password, password)
        if not (correct_username and correct_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials.username


@app.post('/uploadfiles/', status_code=status.HTTP_201_CREATED)
async def file_upload(username: str = Depends(get_current_username),
                      files: List[UploadFile] = File(...)):
    names = []
    for file in files:
        path = Path(file.filename)
        stem = path.stem
        suffix = path.suffix
        if username:
            stem = f"{username}_{stem}"
        output_path = save_dir / (stem + suffix)
        with output_path.open("wb") as wh:
            wh.write(await file.read())
            await file.close()
            logger.info(f"wrote image {file.filename} of type {file.content_type} to {output_path}")
            names.append(output_path.name)

    return {"names": names}


@app.get("/")
async def main():
    content = f"""
<body>
<form action="/uploadfiles/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
<pre>
curl {"" if args.no_security else "-u username[:password]"} -F 'files[]=@/path/to/file' http://{get_ip()}:{args.port}
</pre>
</body>
    """
    return HTMLResponse(content=content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory", default="./",
                        help="directory to save uploaded files"
                             "to (DEFAULT: %(default)s)")
    parser.add_argument("-b", "--bind", default="0.0.0.0",
                        help="address to bind to (DEFAULT: %(default)s)")

    parser.add_argument("-p", "--port", type=int, default=5000, required=False,
                        help="port to serve at (DEFAULT: %(default)s)")
    security_group = parser.add_mutually_exclusive_group(required=True)
    security_group.add_argument("--no-security", action="store_true",
                                help="don't use any security")
    security_group.add_argument("-u", "--user", type=str,
                                 help="require basic auth; 'username:password'")

    args = parser.parse_args()

    save_dir = Path(args.directory).resolve()
    if not save_dir.exists() or not save_dir.is_dir():
        parser.error(f"--directory: {save_dir} is not a directory")

    parts = args.user.split(":")
    if len(parts) != 2:
        parser.error(f"--user: not in expected form: 'username:password'")
    else:
        username, password = parts

    config = uvicorn.Config(app, host=args.bind, port=args.port)
    server = uvicorn.Server(config=config)

    setup_logging()
    logger.info(f"Will be saving files to {save_dir}")

    server.run()
