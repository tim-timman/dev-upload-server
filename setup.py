import setuptools
from src import __version__, description

try:
    with open("requirements.txt", "r") as fh:
        requirements = fh.read()
except FileNotFoundError as e:
    print("Error: requirements file not found.")
    exit(1)

try:
    with open("requirements-dev.txt", "r") as fh:
        dev_requirements = fh.read()
except FileNotFoundError:
    print("Warning: dev requirements file not found.")
    dev_requirements = ""

try:
    with open("README.md", "r") as fh:
        long_description = fh.read()
except FileNotFoundError:
    print("Warning: README file not found. Long description not available.")
    long_description = ""


setuptools.setup(
    name="dev-upload-server",
    version=__version__,
    author="tim-timman",
    author_email="tim.den.vilde@gmail.com",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
    },
    classifiers=[
        "Development Status :: 3 - Alpha"
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "Private :: Do Not Upload",
    ],
    entry_points={
        "console_scripts": [
            "dev-upload-server=src.__main__:main",
        ],
    },
)
