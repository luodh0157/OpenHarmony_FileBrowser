# 图标生成工具

通用图片转 ICO/ICNS 图标工具，支持多种输入格式和自定义尺寸。

## 环境要求

```bash
pip install Pillow
```

## 支持的格式

| 类型 | 格式 |
|------|------|
| 输入 | PNG, JPG, JPEG, BMP, GIF, TIFF, WEBP, SVG |
| 输出 | ICO (Windows), ICNS (macOS) |

## 使用方式

```bash
python generate/generate_icon.py -i <输入文件> [-o <输出文件>] [选项]
```

### 基本用法

```bash
# 默认生成：同时生成 .ico 和 .icns（与输入文件同目录同名）
python generate/generate_icon.py -i app.png

# 指定输出文件（只生成指定格式）
python generate/generate_icon.py -i app.png -o app.ico
python generate/generate_icon.py -i app.png -o app.icns

# 指定输出路径
python generate/generate_icon.py -i app.png -o dist/icons/app.ico
```

### 自定义尺寸

```bash
# 生成小尺寸 ICO（适合网页 favicon）
python generate/generate_icon.py -i logo.png -o favicon.ico --sizes 16 32

# 生成高清 ICO
python generate/generate_icon.py -i icon.png -o icon.ico --sizes 16 32 48 64 128 256 512
```

### 圆角图标

```bash
# 默认圆角（20% 比例，类似 macOS 风格）
python generate/generate_icon.py -i app.png -o app.ico

# 自定义圆角半径（比例 0-1）
python generate/generate_icon.py -i app.png -o app.ico --radius 0.3

# 自定义圆角半径（固定像素）
python generate/generate_icon.py -i app.png -o app.ico --radius 16

# 无圆角（正方形）
python generate/generate_icon.py -i app.png -o app.ico --radius 0
```

### 其他格式输入

```bash
# JPG 转 ICO
python generate/generate_icon.py -i logo.jpg -o logo.ico

# WEBP 转 ICO
python generate/generate_icon.py -i icon.webp -o icon.ico

# SVG 转 ICO
python generate/generate_icon.py -i icon.svg -o icon.ico --sizes 16 32 48 64 128 256
```

## 参数说明

| 参数 | 简写 | 说明 |
|------|------|------|
| `--input` | `-i` | 输入图片文件路径（必填） |
| `--output` | `-o` | 输出图标文件路径（可选，默认生成 .ico 和 .icns） |
| `--sizes` | `-s` | 自定义图标尺寸列表（可选，空格分隔） |
| `--radius` | `-r` | 圆角半径（可选，默认 0.2 即 20% 比例，0=无圆角） |
| `--quiet` | `-q` | 静默模式，不输出日志（可选） |

## 默认行为

| 场景 | 输出 |
|------|------|
| 未指定 `-o` | 在输入文件同目录生成 `同名.ico` 和 `同名.icns` |
| 指定 `-o xxx.ico` | 仅生成 ICO 文件 |
| 指定 `-o xxx.icns` | 仅生成 ICNS 文件 |

## 默认尺寸

| 输出格式 | 默认尺寸 |
|----------|----------|
| `.ico` | 16, 32, 48, 64, 128, 256 |
| `.icns` | 16, 32, 48, 128, 256, 512, 1024 |
