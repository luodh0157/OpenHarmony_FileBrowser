# Gitee 流水线注意事项

1. YAML 格式与语法
- 采用 Gitee 自定义格式：`version: '1.0'`、`stages:` 定义阶段、`step: build@python` 指定构建类型
- 每个 step 的 `commands` 是 YAML 列表（`-` 前缀），所有命令在同一个 shell 会话中顺序执行，环境变量自动继承，无需跨步骤重新 export
- `executor: []` 表示使用默认执行器
- `caches: []` 和 `notify: []` 为 step 必填空字段

2. 触发器与阶段结构
- `triggers.trigger: auto` 表示自动触发
- `push.tags.prefix` 按标签前缀匹配触发，如 `OpenHarmony_FileBrowser_V`
- `strategy: naturally` 表示自然顺序执行
- `retry: '0'` 表示失败不重试（注意值为字符串）
- 多个 stages 按声明顺序执行；steps 之间通过 `dependsOn` 定义依赖关系

3. Runner 环境特性
- `step: build@python` 的 `pythonVersion: '3.11'` 参数提供自带 Python 环境，但该 Python 构建时不包含共享库（`Py_ENABLE_SHARED` 为 None），PyInstaller 打包会报错 "Python was built without a shared library"，因此必须手动安装 Miniforge 并用 conda 创建 Python 环境
- `pythonVersion` 参数仅为声明性质，实际 Python 环境完全由 commands 中手动安装的 Miniforge 提供
- 使用 Miniforge（conda-forge 发行版）而非 Miniconda，默认频道就是 conda-forge
- 有 root 权限：可以直接使用 `yum install` 安装系统级依赖
- 代码检出到当前工作目录，不需要 `cd repo_workspace`

4. Conda 配置方式
- 使用 `conda config --remove-key channels` 清除默认频道，再逐个添加镜像源（`--add channels`）
- 使用 `custom_channels`（注意：是 `custom_channels`，不是 `custom_multichannels`）映射 conda-forge、bioconda、pytorch 到清华镜像。`custom_channels` 映射单个频道名到镜像 URL
- 必须执行 `conda init bash` 和 `source $HOME/miniforge3/etc/profile.d/conda.sh` 初始化 shell 函数
- 初始化后可使用 `conda activate py311` 激活环境
- 建议设置 `channel_priority: strict` 和 `solver: libmamba` 提升求解速度和稳定性
- 使用 `conda clean -i -y` 清除索引缓存确保配置生效

5. pip 与 Python 包管理
- Miniforge/conda-forge 创建的 Python 环境自动包含 pip 作为依赖，`conda create -n py311 python=3.11.9 -y` 已自动安装 pip，无需显式添加 pip 参数
- `pip config set global.index-url` 命令配置 pip 镜像
- `python -m pip` 和 `pip` 命令均可正常使用（conda activate 后 pip 在 PATH 中）

6. 依赖安装
- Qt 系统依赖（mesa-libEGL、mesa-libGL、fontconfig）可直接通过 `yum install -y` 安装（有 root 权限）
- PySide6 >= 6.10.0 需要 glibc >= 2.34，Gitee runner 的 glibc 版本可能不满足，`requirements.txt` 中已限制 `<6.10.0`

7. 制品管理
- 使用 `artifacts:` 声明构建产物，`name` 定义制品名称，`path` 指定路径
- 使用 `publish@general_artifacts` 步骤上传制品，通过 `dependArtifact` 关联前置步骤的制品名称
- `dependsOn` 定义步骤依赖关系，确保制品步骤在构建完成后执行
- 构建完成后建议清理中间文件（如 `rm -rf "OpenHarmonyFileBrowser/"`）减少制品体积

8. 版本发布（release.yml）
- `variables:` 定义流水线级变量，如 `FILEBROWSER_VERSION: v1.0.0`，可在 commands 中通过 `${FILEBROWSER_VERSION}` 引用
- `publish@release_artifacts` 步骤标记版本号，`autoIncrement: true` 自动递增
- `release@gitee` 步骤执行 Gitee Release 发布，使用 `${GITEE_BRANCH}` 作为 tag 和 release name
- `upstreamArtifact` 关联制品，`assertFiles` 声明必须包含的文件名
- `prerelease: false` 和 `allowUpdate: true` 控制发布属性

9. GLIBC 兼容性限制
- Gitee runner 使用 conda-forge Python 3.11.9，其编译工具链较新，构建产物可能需要 GLIBC ≥ 2.33
- 在 Ubuntu 20.04 (glibc 2.31) 或更老系统上无法运行，会报 `GLIBC_X.XX not found` 错误
- 已知错误：`libpython3.11.so.1.0: version 'GLIBC_2.38' not found`、`libstdc++.so.6: version 'GLIBC_2.33' not found`
- **本地构建方案**：如果下载的产物无法运行，可下载本仓库源码，在本地执行 `python package/build.py` 打包后运行
