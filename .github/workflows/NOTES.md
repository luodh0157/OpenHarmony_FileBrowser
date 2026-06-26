# GitHub Actions 流水线注意事项

1. YAML 格式与语法
- 配置文件位于 `.github/workflows/` 目录下，采用标准 GitHub Actions 语法
- `on:` 定义触发器（`push`、`pull_request`、`workflow_dispatch`），`jobs:` 定义并行任务
- `runs-on:` 指定 runner OS：`ubuntu-latest`、`windows-latest`、`macos-latest`、`macos-15-intel`
- `steps:` 中每个步骤可使用 `run:` 执行 shell 命令，或使用 `uses:` 引用 action

2. 可复用工作流与作业结构
- `test.yml` 定义为可复用工作流（`on: workflow_call`），由 `build.yml` 通过 `uses: ./.github/workflows/test.yml` 调用
- `build.yml` 定义三个 job：`test`（调用 test.yml）、`build`（matrix 多平台构建）、`create-release`（仅 tag 触发时执行）
- `build` job 通过 `needs: test` 依赖测试完成后再构建
- `create-release` job 通过 `if: startsWith(github.ref, 'refs/tags/OpenHarmony_FileBrowser_V')` 仅在 tag 推送时触发
- `notify-on-failure` job 通过 `if: failure()` 在任何前置 job 失败时触发，自动创建 GitHub Issue

3. 并发控制
- 使用 `concurrency:` 避免同一分支/tag 的并发运行
- `group: ${{ github.workflow }}-${{ github.ref }}` 按工作流 + 引用分组
- `cancel-in-progress: true` 取消同一组中正在运行的旧流水线

4. Runner 环境特性
- GitHub 托管 runner 有 sudo 权限，可直接安装系统依赖
- ubuntu-latest 基于 Ubuntu 22.04+（glibc >= 2.35），macOS 和 Windows 不受 glibc 限制
- 环境变量跨步骤可通过 `$GITHUB_ENV` 文件传递：`echo "KEY=value" >> $GITHUB_ENV`
- 步骤输出通过 `$GITHUB_OUTPUT` 传递：`echo "result=value" >> $GITHUB_OUTPUT`
- 工作目录为 `$GITHUB_WORKSPACE`，代码通过 `actions/checkout@v4` 自动检出到该目录

5. Python 环境管理
- 推荐使用官方 action `actions/setup-python@v5` 安装 Python，指定 `python-version: '3.11'`
- `cache: 'pip'` + `cache-dependency-path` 启用 pip 缓存加速，可指定多个依赖文件
- setup-python 安装的 Python 自带 pip，无需额外安装
- 若需 conda 环境，可使用 `conda-incubator/setup-miniconda@v3` action（当前配置未使用）

6. 多平台 Matrix 构建
- 使用 `strategy.matrix.include` 定义四组构建目标：Windows x64、Linux x64、macOS arm64、macOS x64
- `fail-fast: false` 确保某个平台失败不影响其他平台继续构建
- `timeout-minutes: 30` 设置构建超时
- Linux 步骤通过 `if: matrix.platform == 'Linux'` 条件执行系统依赖安装
- Windows 使用 `7z a -r` 打包 zip，Linux/macOS 使用 `tar czf` 打包 tar.gz
- `shell: bash` 在 Windows 步骤中强制使用 bash 解释器

7. 依赖安装
- Qt 系统依赖在 Ubuntu runner 上通过 `sudo apt-get` 安装：libegl1、libgl1、libxcb-xinerama0、libxkbcommon-x11-0 等系列 X11 库
- GitHub runner 的网络环境访问 PyPI 和 conda 官方源通常无障碍，但国内用户可能需配置镜像加速
- PySide6 在 Ubuntu 22.04+ 上兼容 >=6.10.0（glibc >= 2.35），但 `requirements.txt` 中全局限制 `<6.10.0`，该限制在 GitHub runner 上并不必要但仍生效
- `python -m pip install` 和 `pip install` 均可正常使用

8. 制品与缓存
- 使用 `actions/upload-artifact@v4` 上传构建产物，`name` 按平台区分（如 `OpenHarmonyFileBrowser-Linux-x64`）
- `actions/download-artifact@v4` 在后续 job 中下载制品，`merge-multiple: false` 保持各平台制品独立
- `retention-days: 30` 设置制品保留期，`if-no-files-found: error` 确保制品缺失时报错
- pip 缓存通过 `setup-python` 的 `cache: 'pip'` 参数自动管理，无需额外 `actions/cache`

9. 发布与通知
- 使用 `softprops/action-gh-release@v2` 创建 GitHub Release，`generate_release_notes: true` 自动生成发布说明
- `permissions: contents: write` 为 release job 授权 GITHUB_TOKEN 写入权限
- 使用 `actions/github-script@v7` 在 CI 失败时自动创建 Issue，标注 `ci-failed` 和 `automated` 标签
- Release 发布 `draft: false`、`prerelease: false` 表示直接发布正式版

10. GLIBC 兼容性限制
- `ubuntu-latest` runner 基于 Ubuntu 24.04（glibc 2.39），构建的 Linux 产物需要 GLIBC ≥ 2.39
- 在 Ubuntu 22.04 (glibc 2.35)、Ubuntu 20.04 (glibc 2.31) 等老系统上无法运行，会报 `GLIBC_X.XX not found` 错误
- Windows 和 macOS 构建不受 GLIBC 限制
- **本地构建方案**：如果下载的产物无法运行，可下载本仓库源码，在本地执行 `python package/build.py` 打包后运行
