#!/usr/bin/env python3
"""
Setup script for OpenHarmony File Browser.
Provides friendly help and standard setuptools commands.
"""

import sys


# 首先检查参数，在导入 setuptools 之前
if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']):
    help_text = """
OpenHarmony File Browser - Setup Script
========================================

Usage:
  python package/setup.py <command>

Prerequisites:
  pip install wheel        # bdist_wheel 需要先安装 wheel 包
  pip install setuptools   # 确保 setuptools 已安装

Quick Start:
  python package/setup.py --help          # 显示本帮助信息
  python package/setup.py sdist           # 生成源码包 (无需 wheel)
  python package/setup.py bdist_wheel     # 生成 wheel 包 (需先安装 wheel)

Common Commands:
  sdist                   生成源码分发包 (.tar.gz)
  bdist_wheel             生成 wheel 包 (.whl) - 需要安装 wheel
  sdist bdist_wheel       同时生成两种包
  build                   构建包（在 build/ 目录）
  install                 安装包（推荐使用 pip install）
  
Development:
  pip install -e .        开发模式安装（推荐）
  pip install .           正式安装
  pip uninstall openharmony-filebrowser  卸载

Publish to PyPI:
  pip install wheel twine    # 安装必需工具
  python package/setup.py sdist bdist_wheel
  twine upload dist/*

Output Location:
  所有生成的包都输出到项目根目录的 dist/ 目录

More Commands:
  python package/setup.py --help-commands    # 查看所有可用命令

Examples:
  # 安装 wheel（首次使用 bdist_wheel 前）
  pip install wheel
  
  # 生成发布包
  python package/setup.py sdist bdist_wheel
  
  # 查看包信息
  python package/setup.py --name --version
  
  # 安装到当前 Python 环境
  pip install dist/openharmony_filebrowser-1.0.0.tar.gz

Troubleshooting:
  如果 bdist_wheel 报错 "invalid command"，请先安装 wheel：
    pip install wheel

For more details, see package/README.md
"""
    print(help_text)
    sys.exit(0)


# 检查 bdist_wheel 命令是否需要 wheel 包
if len(sys.argv) > 1 and 'bdist_wheel' in sys.argv:
    try:
        import wheel
    except ImportError:
        print("\n错误: 'bdist_wheel' 命令需要 'wheel' 包，但未安装。\n")
        print("解决方案:")
        print("  pip install wheel")
        print("\n然后再运行:")
        print("  python package/setup.py bdist_wheel")
        print("\n或者使用 sdist（不需要 wheel）:")
        print("  python package/setup.py sdist")
        print("\n查看完整帮助:")
        print("  python package/setup.py --help")
        sys.exit(1)

# 参数正常，继续导入 setuptools 并执行
from setuptools import setup, find_packages


def _get_version():
    import re
    with open("src/config.py") as f:
        m = re.search(r'app_version:\s*str\s*=\s*"([^"]+)"', f.read())
        return m.group(1) if m else "0.0.0"


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="openharmony-filebrowser",
    version=_get_version(),
    author="OpenHarmony_FileBrowser Contributors",
    description="A cross-platform file browser for OpenHarmony/HarmonyOS devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitcode.com/OpenHarmony_Tools/OpenHarmony_FileBrowser",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "openharmony-filebrowser=src.main:main",
        ],
    },
    package_data={
        "": ["*.qss", "*.ico", "*.png", "*.svg", "*.json"],
    },
    include_package_data=True,
    zip_safe=False,
)