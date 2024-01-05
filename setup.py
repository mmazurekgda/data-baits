# flake8: noqa
from setuptools import find_packages, setup
from typing import List
import os
import re


# inspired by https://github.com/kubeflow/pipelines/blob/master/sdk/python/setup.py
def get_requirements(requirements_file: str) -> List[str]:
    """Read requirements from requirements.in."""

    file_path = os.path.join(os.path.dirname(__file__), requirements_file)
    with open(file_path, "r") as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if not line.startswith("#") and line]
    return lines


# inspired by https://github.com/kubeflow/pipelines/blob/master/sdk/python/setup.py
def find_version(*file_path_parts: str) -> str:
    """Get version from kfp.__init__.__version__."""

    file_path = os.path.join(os.path.dirname(__file__), *file_path_parts)

    with open(file_path, "r") as f:
        version_file_text = f.read()
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]",
        version_file_text,
        re.M,
    )
    if version_match:
        return version_match.group(1)

    raise RuntimeError(f"Unable to find version string in file: {file_path}.")


setup(
    name="data-baits",
    version=find_version("data_baits", "__init__.py"),
    description="",
    long_description="",
    url="https://github.com/mmazurekgda/data-baits",
    author="Michał Mazurek",
    license="GPLv3+",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    packages=find_packages(exclude=["*.test"]),
    install_requires=get_requirements("requirements.in"),
)
