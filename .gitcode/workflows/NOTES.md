# GitCode 流水线注意事项

1. YAML 格式与语法
- 采用 GitHub Actions 风格：`on:` 定义触发器，`jobs:` 定义并行任务，`steps:` 定义步骤
- 每个 `run:` 块是独立 shell 会话，`run: |` 多行脚本块中 heredoc 内容会继承 YAML 缩进空格，写入的文件会包含前导空格导致解析失败。应改用 `printf` 命令写入配置文件（如 `.condarc`、`pip.conf`）
- YAML 缩进必须严格使用空格（2 空格为单位），禁止混用 Tab

2. 触发器与作业结构
- `on:` 支持 `push`（分支 + 标签）、`pull_request`、`workflow_dispatch`（手动触发）
- 作业之间可并行运行（如 `test-all` 和 `build` 两个 job 无 `needs` 依赖时可并行）
- 当前配置未定义制品上传/发布步骤，构建产物仅留在 runner 本地，不会自动归档

3. Action 与 Checkout
- 使用 `checkout-action@0.0.1`（GitCode 平台专用），不是 GitHub 的 `actions/checkout@v4`
- `setup-python@0.0.1` 存在但仅支持 Python 3.8.18，该版本构建的 Python 缺少共享库（`Py_ENABLE_SHARED` 为 None），PyInstaller 打包会报错，因此必须通过 Miniconda 自行安装 Python
- 代码检出到 `repo_workspace` 子目录，所有命令需 `cd repo_workspace`

4. Runner 环境限制
- `runs-on: euleros-2.10.1` 基于 RHEL 8 体系，glibc 2.28
- 非 root 用户（octopus）：无法使用 sudo（即使存在也会报权限错误），无法写入 `/etc` 目录
- yum 的 shebang 指向 `/usr/bin/python3`，但系统只有 python3.7，直接调用 yum 会报 bad interpreter；因此系统级依赖不能通过 yum 安装，必须通过 conda-forge 安装到用户环境

5. Conda 配置陷阱
- Miniconda 的 `defaults` 频道指向 `repo.anaconda.com`，CI 服务器 IP 会被 403 封禁
- 必须通过 `~/.condarc` 完全覆盖 channels 列表，并配置 `custom_multichannels.defaults` 重定向 defaults meta-channel（注意：GitCode 用 `custom_multichannels`，而非 `custom_channels`）
- `conda create -n env python=x.x.x` 不包含 pip，必须显式添加 `pip` 参数
- 使用 `printf` 写入 `.condarc` 和 `pip.conf` 避免 heredoc 缩进污染

6. 环境变量与命令执行
- 每个 `run:` 块是独立 shell 会话，`export` 不会跨步骤传递；`PATH` 和 `LD_LIBRARY_PATH` 必须在每个需要使用的步骤中重新设置
- `source activate` 在 GitCode 环境中不可靠，应使用绝对路径调用：`$HOME/miniconda/envs/py311/bin/python`
- pip 脚本可能不存在，使用 `$CONDA_PYTHON -m pip` 更可靠
- 定义变量别名（如 `CONDA_PYTHON`、`CONDA_BIN`）在每个步骤内重新声明，提高可读性和可维护性

7. 依赖兼容性
- PySide6 >= 6.10.0 需要 glibc >= 2.34（manylinux_2_34），与 EulerOS 2.10.1 的 glibc 2.28 不兼容，`requirements.txt` 中已限制 `<6.10.0`
- Qt 系统依赖（fontconfig、libxcb）无法通过 yum 安装（无 root 权限），需通过 `conda install -n py311 -y -c conda-forge fontconfig libxcb` 安装到用户 conda 环境
- 安装后需设置 `LD_LIBRARY_PATH` 包含 conda 环境的 lib 目录，确保运行时能找到这些库

8. 日志与调试
- 建议在每个关键步骤添加诊断日志：`.condarc` 内容、conda 环境列表、bin 目录内容、库文件位置
- 使用 `ls -la` 验证文件是否存在，避免静默失败
- 可使用 `::error::` 语法在步骤中标注错误信息
