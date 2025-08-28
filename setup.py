"""
Setup script for jra-van-client package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="jra-van-client",
    version="0.1.0",
    author="JRA-VAN Client Developer",
    author_email="",
    description="JRA-VAN DataLabから競馬データを円滑に取得するためのPythonパッケージ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/jra-van-client",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "jra-van=main_jra_van:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.bat", "*.md"],
    },
)