# 构建与打包指南

本目录包含 OpenHarmony File Browser 的构建和打包脚本。

## 快速开始

**如果你想：**

| 目标 | 命令 | 说明 |
|------|------|------|
| **打包成可执行文件**（推荐） | `python package/build.py` | 无需 Python 环境，适合分发 |
| **开发调试** | `pip install -e .` | 代码修改即时生效 |
| **正式安装** | `pip install .` | 安装后运行 `openharmony-filebrowser` |
| **发布到 PyPI** | `python package/setup.py sdist bdist_wheel` | 生成发布包 |

## 详细说明

### 方式一：构建独立可执行文件（推荐）

**适用场景**：分发给终端用户，无需 Python 环境

```bash
# 从项目根目录运行
python package/build.py
```

**输出位置**：`dist/OpenHarmonyFileBrowser/` 目录

**包含内容**：
- 可执行文件 `OpenHarmonyFileBrowser`
- 所有依赖库
- HDC 工具（已内置）
- 资源文件（图标、样式表、翻译）
- 默认配置文件 `config/config.json`

**注意事项**：
- ✅ `config.json` 会被打包，首次运行会自动创建日志目录
- ✅ `logs/` 目录**不会**被打包（运行时生成）
- ✅ 使用 `--clean` 参数，每次打包会清理旧的构建文件

### 方式二：开发模式安装

**适用场景**：开发者调试，代码修改即时生效

```bash
# 从项目根目录运行
pip install -e .
```

**运行方式**：
```bash
# 命令行启动
openharmony-filebrowser

# 或直接运行
python main.py
```

**卸载**：
```bash
pip uninstall openharmony-filebrowser
```

### 方式三：正式安装

**适用场景**：在 Python 环境中安装使用

```bash
# 从项目根目录运行
pip install .
```

**运行**：
```bash
openharmony-filebrowser
```

### 方式四：生成发布包

**适用场景**：发布到 PyPI 或分享源码包

```bash
# 生成源码分发包 (.tar.gz)
python package/setup.py sdist

# 生成 wheel 包 (.whl)
python package/setup.py bdist_wheel

# 同时生成两种格式
python package/setup.py sdist bdist_wheel

# 发布到 PyPI（需要 twine）
twine upload dist/*
```

**输出位置**：项目根目录的 `dist/` 目录（注意：与 PyInstaller 输出同名但内容不同）

## 文件说明

| 文件 | 用途 | 使用场景 |
|------|------|----------|
| `build.py` | PyInstaller 打包脚本 | 生成独立可执行文件 |
| `setup.py` | setuptools 安装脚本 | pip 安装或发布到 PyPI |
| `MANIFEST.in` | 资源文件清单 | 定义打包时包含的文件 |

## 环境要求

### 基础要求
- Python >= 3.9
- setuptools（Python 打包工具）

### 必需依赖
```bash
pip install PyInstaller setuptools Pillow PySide6
```

### bdist_wheel 额外依赖
如果需要生成 wheel 包（`.whl`），必须先安装 `wheel`：
```bash
pip install wheel
```

**注意**：
- ✅ `sdist` 命令不需要 wheel
- ✅ `bdist_wheel` 命令需要 wheel
- ✅ 如果运行 `bdist_wheel` 时提示 "invalid command"，请先安装 wheel

## 图标生成

**重要**：打包前需要生成应用图标

```bash
# 使用图标生成工具
python generate/generate.py -i assets/icons/app.png
```

**说明**：
- 输入：`assets/icons/app.png`（源图标）
- 输出：`assets/icons/app.ico`（Windows）和 `assets/icons/app.icns`（macOS）
- 如无图标，打包会警告但仍可继续

## 常见问题

### 1. 打包后运行报错找不到 HDC？

检查 `hdc/` 目录：
- Windows: `hdc/Windows/x64/hdc.exe`
- macOS: `hdc/Darwin/x64/hdc` 或 `hdc/Darwin/arm64/hdc`
- Linux: `hdc/Linux/x64/hdc`

### 2. 打包体积太大？

PyInstaller 会包含所有依赖，这是正常现象。如需减小体积：
- 使用 `--onefile` 模式（但启动较慢）
- 手动排除不需要的库

### 3. 打包时提示缺少图标？

运行图标生成工具：
```bash
python generate/generate.py -i assets/icons/app.png
```

### 4. bdist_wheel 报错 "invalid command 'bdist_wheel'"？

**原因**：缺少 `wheel` 包

**解决**：
```bash
pip install wheel
python package/setup.py bdist_wheel
```

**替代方案**：使用 `sdist`（不需要 wheel）
```bash
python package/setup.py sdist
```

### 5. 开发模式安装后修改代码不生效？

确保使用 `-e` 参数：
```bash
pip install -e .  # 开发模式
# 而不是
pip install .     # 正式安装
```

## 注意事项

1. **首次打包**：PyInstaller 会下载依赖，需要等待几分钟
2. **打包清理**：使用 `--clean` 参数避免残留文件
3. **配置文件**：只打包 `config.json`，日志目录运行时创建
4. **HDC 工具**：确保对应平台的 HDC 工具在正确位置
5. **平台兼容**：在对应平台打包（Windows 上打包 Windows 版本等）
