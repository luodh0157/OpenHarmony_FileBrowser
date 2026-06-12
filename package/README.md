# 构建与打包指南

本目录包含 OpenHarmony File Browser 的构建和打包脚本。

## 文件说明

| 文件 | 用途 |
|------|------|
| `build.py` | 使用 PyInstaller 打包为独立可执行文件（无需 Python 环境） |
| `setup.py` | 使用 setuptools 打包为 Python 安装包（需 pip 安装） |
| `MANIFEST.in` | 定义打包时需要包含的资源文件清单 |

## 环境要求

- Python >= 3.9
- 依赖包：`pip install PyInstaller setuptools Pillow PySide6`

## 使用方式

### 方式一：构建独立可执行文件（推荐）

```bash
# 从项目根目录运行
python package/build.py
```

**输出**：`dist/OpenHarmonyFileBrowser/` 目录，包含可直接运行的可执行文件。

**特点**：
- 无需安装 Python 环境
- 包含所有依赖和资源文件
- 适合分发给终端用户

### 方式二：安装为 Python 包

```bash
# 开发模式安装（修改代码即时生效）
pip install -e .

# 或正式安装
pip install .
```

**运行**：安装后可通过命令行直接启动：
```bash
openharmony-filebrowser
```

**特点**：
- 适合开发者调试
- 可通过 `pip uninstall` 卸载
- 需要 Python 环境

### 方式三：生成发布包

```bash
# 生成源码分发包（.tar.gz）
python package/setup.py sdist

# 生成 wheel 包
python package/setup.py bdist_wheel

# 发布到 PyPI
python package/setup.py sdist bdist_wheel
twine upload dist/*
```

## 图标生成

构建前如需生成应用图标：

```bash
python generate_icon.py
```

图标源文件位于 `resources/icons/app.png`，输出 `.ico`（Windows）和 `.icns`（macOS）到 `assets/icons/`。

## 注意事项

1. 首次构建时 PyInstaller 会下载并解压依赖，可能需要一些时间
2. Windows 平台需确保 HDC 工具放置在 `hdc/Windows/` 目录下
3. macOS 平台需确保 HDC 工具放置在 `hdc/Darwin/` 目录下
4. Linux 平台需确保 HDC 工具放置在 `hdc/Linux/` 目录下
