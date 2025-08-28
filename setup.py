#!/usr/bin/env python
"""
setup.py - 後方互換性のためのセットアップスクリプト

最新のPythonでは pyproject.toml が推奨されますが、
古いツールとの互換性のために setup.py も提供しています。

インストール:
    pip install .
    pip install -e .  # 開発モード
"""

from setuptools import setup

# pyproject.tomlから設定を読み込む
setup()