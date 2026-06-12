# OpenHarmony File Browser - 设计文档

## 1. 项目概述

OpenHarmony File Browser 是一个跨平台的文件管理器，用于通过 HDC（HarmonyOS Device Connector）工具连接和管理 OpenHarmony/HarmonyOS 设备上的文件系统。项目采用 Python 3.9+ 和 PySide6（Qt6）构建，提供图形化界面进行设备连接、文件浏览、传输和预览等操作。

## 2. 架构设计

### 2.1 整体架构模式

项目采用 **分层 MVC（Model-View-Controller）架构**，结合 Qt 的信号/槽机制实现组件间通信：

```
┌─────────────────────────────────────────────────────────────────────┐
│                          入口层 (Entry Point)                        │
│  main.py → src/main.py (应用引导、依赖检查、QApplication 创建)        │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       GUI 控制层 (GUI Controller)                    │
│  MainWindow (主窗口)                                                  │
│  ├── 工具栏 (设备选择 + 文件操作按钮)                                  │
│  ├── 菜单栏 (文件/视图/帮助)                                          │
│  ├── 状态栏                                                          │
│  └── FileBrowserWidget (核心文件浏览器组件)                           │
└─────────────────────────────────────────────────────────────────────┘
          │                              │                              │
          ▼                              ▼                              ▼
┌──────────────────┐    ┌────────────────────────────┐    ┌──────────────────┐
│   设备管理层      │    │      文件浏览层             │    │   主题/语言层    │
│  DeviceManager   │    │   FileBrowserWidget        │    │  ThemeManager    │
│                  │    │   ├── FileTreeWidget       │    │  LanguageManager │
│  - HDCWrapper    │    │   ├── FileListWidget       │    │  IconManager     │
│  - MonitorThread │    │   ├── PathBarWidget        │    │                  │
│  - Qt Signals    │    │   ├── TransferDialog       │    │  - QSS 样式加载  │
└──────────────────┘    │   └── PreviewWindow        │    │  - 图标主题切换  │
          │             └────────────────────────────┘    └──────────────────┘
          ▼                              │
┌──────────────────┐                     ▼
│   HDC 通信层      │          ┌────────────────────────────┐
│   HDCWrapper     │          │       核心服务层            │
│                  │          │                            │
│  - subprocess    │          │  - FileOperations (文件操作) │
│  - HDC CLI 命令  │          │  - TransferManager (传输管理) │
│  - 输出解析      │          │  - PreviewHandler (预览处理)  │
└──────────────────┘          └────────────────────────────┘
```

### 2.2 分层说明

| 层级 | 模块 | 职责 |
|------|------|------|
| **入口层** | `main.py`, `src/main.py` | 应用启动、参数解析、依赖检查、QApplication 初始化 |
| **GUI 控制层** | `gui/main_window.py` | 主窗口容器、菜单栏/工具栏/状态栏管理、主题和语言切换入口 |
| **组件层** | `gui/widgets/` | 可复用的 UI 组件：文件树、文件列表、路径栏、对话框等 |
| **核心服务层** | `core/` | 业务逻辑：HDC 命令封装、设备管理、文件操作、传输管理、预览处理 |
| **数据模型层** | `models/` | 数据结构定义：DeviceInfo、FileInfo、枚举类型 |
| **工具层** | `utils/` | 通用工具：日志、文件类型检测、平台检测、图标管理、国际化、异步加载 |
| **配置层** | `config.py` | 应用配置：窗口尺寸、超时、传输参数、预览限制等 |
| **资源层** | `resources/` | 静态资源：SVG 图标、国际化 JSON 文件、样式表 |

## 3. 核心模块设计

### 3.1 数据模型 (models/)

#### DeviceInfo
设备信息数据类，包含设备 ID、连接状态、型号、品牌等信息。

```python
@dataclass
class DeviceInfo:
    device_id: str          # 设备序列号或 IP:PORT
    status: DeviceStatus    # 连接状态枚举
    model: str              # 设备型号
    brand: str              # 品牌
    product: str            # 产品名称
    is_wireless: bool       # 是否为无线连接
```

#### DeviceStatus
设备连接状态枚举：`DISCONNECTED`, `CONNECTED`, `UNAUTHORIZED`, `OFFLINE`, `UNKNOWN`

#### FileInfo
文件信息数据类，包含文件名、路径、大小、权限、修改时间等。

```python
@dataclass
class FileInfo:
    name: str
    path: str
    is_dir: bool
    size: int
    permissions: str
    modified_time: datetime
    file_type: FileType
    owner: str
    group: str
    links: int
```

#### FileType
文件类型枚举：`FILE`, `DIRECTORY`, `SYMLINK`, `UNKNOWN`

### 3.2 核心业务逻辑 (core/)

#### HDCWrapper (`hdc_wrapper.py`)
**职责**：封装所有 HDC CLI 命令，提供 Python 接口。

**核心方法**：
- `list_targets()` - 列出已连接设备
- `get_device_info(device_id)` - 获取设备详细信息
- `shell_ls(device_id, path)` - 列出远程目录内容
- `shell_stat(device_id, path)` - 获取文件/目录属性
- `shell_mkdir(device_id, path)` - 创建远程目录
- `shell_rm(device_id, path)` - 删除远程文件/目录
- `shell_mv(device_id, src, dst)` - 重命名/移动远程文件
- `file_send(device_id, local, remote)` - 上传文件到设备
- `file_recv(device_id, remote, local)` - 从设备下载文件
- `shell(device_id, command)` - 执行任意 shell 命令
- `tconn(device_id)` / `tdisconn(device_id)` - 无线连接/断开

**设计特点**：
- 通过 `subprocess.run()` 执行 HDC 命令
- 解析 `ls -l` 和 `stat` 输出为 `FileInfo` 对象
- 支持超时和重试机制
- 自定义 `HDCError` 异常类

#### DeviceManager (`device_manager.py`)
**职责**：管理 OpenHarmony 设备生命周期，提供设备连接、监控和管理功能。

**核心组件**：
- `DeviceMonitorThread` - QThread 子类，每 2 秒轮询设备状态
- `DeviceManager` - QObject 子类，封装设备管理逻辑

**Qt 信号**：
- `devices_changed` - 设备列表变化
- `device_added` - 新设备连接
- `device_removed` - 设备断开
- `device_status_changed` - 设备状态变化

**功能**：
- USB 设备自动检测和监控
- 无线设备连接（TCP/IP）
- 设备信息缓存和更新

#### FileOperations (`file_operations.py`)
**职责**：高级文件操作门面类，封装 HDCWrapper 提供统一的文件操作 API。

**核心方法**：
- `list_directory(device_id, path)` - 列出目录内容
- `get_file_info(device_id, path)` - 获取文件信息
- `create_directory(device_id, path)` - 创建目录
- `delete_file(device_id, path)` - 删除文件/目录
- `rename_file(device_id, old_path, new_path)` - 重命名/移动
- `exists(device_id, path)` - 检查路径是否存在
- `is_directory(device_id, path)` - 判断是否为目录
- `path_join()`, `path_normalize()`, `path_parent()` - 路径操作

#### TransferManager (`transfer_manager.py`)
**职责**：管理并发文件传输任务，支持上传/下载进度跟踪。

**核心组件**：
- `TransferTask` - 传输任务数据类
- `TransferWorker` - QThread 子类，执行单个传输任务
- `TransferManager` - 传输任务管理器

**功能**：
- 多任务并发传输（默认 3 个工作线程）
- 实时进度、速度计算
- 传输时间戳保留
- 任务取消和暂停支持
- Qt 信号：`progress_updated`, `transfer_completed`, `transfer_failed`

#### PreviewHandler (`preview_handler.py`)
**职责**：处理文件预览，支持图片和视频。

**功能**：
- 图片预览：通过 Pillow 加载并转换为 QPixmap
- 视频预览：调用系统播放器
- 临时文件管理：下载到临时目录，预览后清理
- 文件大小限制检查

### 3.3 GUI 组件 (gui/)

#### MainWindow (`main_window.py`)
**职责**：应用主窗口，集成所有 UI 组件。

**布局结构**：
```
MainWindow
├── QToolBar (工具栏)
│   ├── 设备选择下拉框
│   ├── 刷新按钮
│   ├── 上传/下载按钮
│   ├── 新建文件夹/删除/重命名按钮
│   └── 主题/语言切换按钮
├── QMenuBar (菜单栏)
│   ├── 文件菜单
│   ├── 视图菜单
│   └── 帮助菜单
├── QStatusBar (状态栏)
└── FileBrowserWidget (中央组件)
```

**特性**：
- 延迟初始化设备管理器（加快启动速度）
- 主题切换（浅色/深色）
- 语言切换（中文/英文）
- 窗口状态持久化

#### FileBrowserWidget (`file_browser.py`)
**职责**：核心文件浏览器组件，整合所有子组件。

**内部结构**：
```
FileBrowserWidget (QSplitter)
├── PathBarWidget (顶部路径导航栏)
└── QSplitter (水平分割)
    ├── FileTreeWidget (左侧目录树)
    └── FileListWidget (右侧文件列表)
```

**功能**：
- 目录导航和同步
- 文件操作（创建、删除、重命名、上传、下载）
- 拖拽上传支持
- 传输对话框和预览窗口管理
- 多选操作（Ctrl+A、Ctrl+D、Ctrl/Shift 多选）

#### FileTreeWidget (`file_tree.py`)
**职责**：目录树视图，支持懒加载。

**特性**：
- 点击展开子目录
- `expand_to_path()` 同步导航
- `directory_selected` 信号触发文件列表更新

#### FileListWidget (`file_list.py`)
**职责**：文件列表视图，5 列显示（复选框、名称、大小、修改时间、类型）。

**特性**：
- `DirectoryLoadThread` 异步加载目录
- 自定义复选框（单击 vs 双击区分）
- 多选支持：Ctrl+A 全选、Ctrl+D 取消全选、Ctrl/Shift 多选
- 文件图标按类型显示
- 双击预览图片/视频

#### PathBarWidget (`path_bar.py`)
**职责**：面包屑导航栏。

**特性**：
- 可点击的路径段
- 主页按钮
- 编辑模式切换
- 路径快速跳转

#### 对话框组件 (`dialogs.py`, `transfer_dialog.py`, `preview_window.py`)
- `RenameDialog` - 重命名对话框
- `CreateFolderDialog` - 新建文件夹对话框
- `DeleteConfirmDialog` - 删除确认对话框
- `TransferDialog` - 传输进度对话框（表格显示文件、方向、进度、大小、速度）
- `PreviewWindow` - 图片/视频预览窗口（缩放控制、系统播放器集成）

### 3.4 工具模块 (utils/)

#### Logger (`logger.py`)
- 配置 Python 日志系统
- 文件处理器（按日滚动，存储在 `logs/` 目录）
- 控制台处理器
- `get_logger()` 和 `set_log_level()` 工具函数

#### FileUtils (`file_utils.py`)
- 文件类型检测（图片、视频、音频、文档、压缩包、代码）
- 人类可读的文件大小格式化
- `is_image_file()`, `is_video_file()`, `is_previewable()` 判断函数

#### PlatformUtils (`platform_utils.py`)
- 平台检测（Windows/Linux/Darwin）
- 架构检测（x64/arm64）
- 自动检测 HDC 可执行文件路径

#### IconManager (`icon_manager.py`)
- 单例模式 SVG 图标管理器
- 按主题（light/dark）缓存图标
- 文件扩展名到图标类型的映射
- 15+ 种图标类型支持

#### LanguageManager (`language_manager.py`)
- 单例模式国际化管理器
- 从 `resources/i18n/` 加载 JSON 翻译
- 支持中文/英文切换
- 配置保存在 `config/config.json`
- `tr()` 方法支持嵌套键和模板变量

#### AsyncLoader (`async_loader.py`)
- `DirectoryLoadThread` - QThread 子类
- 异步加载目录内容，防止 UI 阻塞
- 支持取消操作

### 3.5 主题和样式 (gui/styles/)

#### ThemeManager (`theme_manager.py`)
- 管理浅色/深色主题切换
- 加载 QSS 样式表
- 与 IconManager 协调实现主题感知图标
- 用户偏好持久化

#### QSS 样式表
- `main.qss` - 浅色主题主样式表（388 行）
- `modern_light.qss` - 现代浅色主题
- `modern_dark.qss` - 现代深色主题
- `main_v2.qss` - 备用样式表

## 4. 关键交互流程

### 4.1 设备连接流程
```
MainWindow._init_device_manager_later()
  → DeviceManager(auto_start_monitoring=False)
  → DeviceManager.refresh_devices()
    → HDCWrapper.list_targets()
      → subprocess.run(["hdc", "list", "targets"])
    → HDCWrapper.get_device_info()
      → subprocess.run(["hdc", "-t", device_id, "shell", "param", "get", ...])
  → devices_changed 信号发射
  → MainWindow._update_device_combo()
```

### 4.2 文件浏览流程
```
用户点击 FileTree 中的目录
  → directory_selected 信号
  → FileBrowserWidget._on_directory_selected(path)
    → FileListWidget.load_directory(path)
      → DirectoryLoadThread (异步)
        → FileOperations.list_directory(path)
          → HDCWrapper.shell_ls(device_id, path)
            → subprocess.run(["hdc", "-t", device_id, "shell", "ls", "-l", path])
            → _parse_ls_line() → FileInfo 对象列表
      → loaded 信号 → _display_files()
```

### 4.3 文件上传流程
```
用户点击工具栏上传按钮
  → FileBrowserWidget._upload_file()
    → QFileDialog.getOpenFileNames() 或 getExistingDirectory()
    → TransferManager.add_upload_task()
    → TransferDialog.show()
    → TransferManager.start_transfers()
      → TransferWorker (QThread) 每个任务一个线程
        → HDCWrapper.file_send(device_id, local, remote)
          → subprocess.run(["hdc", "-t", device_id, "file", "send", "-a", local, remote])
      → progress_updated 信号 → TransferDialog.update_progress()
      → transfer_completed 信号 → TransferDialog.task_completed()
```

### 4.4 主题/语言切换流程
```
用户点击 视图 > 主题
  → ThemeManager.toggle_theme()
    → apply_stylesheet() (加载 QSS)
    → icon_manager.set_theme() (清除图标缓存)
    → theme_changed 信号
      → MainWindow._on_theme_changed() (更新菜单图标)

用户点击 视图 > 语言
  → LanguageManager.toggle_language()
    → load_translations() (加载 en.json 或 zh.json)
    → save_preference()
    → language_changed 信号
      → MainWindow._on_language_changed()
        → _update_ui_language()
        → file_browser.update_language()
          → tree/list/path_bar/transfer_dialog/preview_window.update_language()
```

## 5. 设计模式应用

| 模式 | 应用场景 |
|------|----------|
| **MVC** | 模型（FileInfo、DeviceInfo）与视图（GUI 组件）和控制器（FileOperations、DeviceManager）分离 |
| **观察者（Qt 信号/槽）** | 所有组件间通信使用 Qt 信号：devices_changed、directory_selected、transfer_progress 等 |
| **单例** | icon_manager、language_manager、config 为模块级单例 |
| **门面** | HDCWrapper 抽象所有 HDC CLI 命令；FileOperations 提供高级文件操作 API |
| **策略** | 主题切换（浅色/深色 QSS）、语言切换（en/zh JSON） |
| **工作线程** | DeviceMonitorThread、TransferWorker、DirectoryLoadThread 继承 QThread 实现后台操作 |
| **工厂** | get_hdc_executable() 创建平台特定的 HDC 路径；get_file_type() 确定文件类别 |
| **构建器** | TransferTask 数据类带默认值；DeviceInfo 和 FileInfo 数据类 |

## 6. 依赖关系

### 运行时依赖
| 库 | 版本 | 用途 |
|----|------|------|
| PySide6 | >=6.5.0 | Qt6 Python 绑定 - 整个 GUI 框架 |
| Pillow | >=10.0.0 | 图像处理 - 图片预览 |

### 开发依赖
| 库 | 版本 | 用途 |
|----|------|------|
| pytest | >=7.0.0 | 单元测试框架 |
| pytest-qt | >=4.2.0 | Qt 测试夹具 |
| black | >=23.0.0 | 代码格式化 |
| flake8 | >=6.0.0 | 代码检查 |
| pyinstaller | >=6.0.0 | 可执行文件打包 |

### 外部工具
| 工具 | 用途 |
|------|------|
| HDC | OpenHarmony/HarmonyOS 设备通信 CLI 工具 |

## 7. 配置说明

### 应用配置 (config.py)
```python
@dataclass
class Config:
    app_name: str = "OpenHarmony File Browser"
    app_version: str = "0.1.0"
    window_width: int = 1200
    window_height: int = 800
    window_min_width: int = 800
    window_min_height: int = 600
    log_level: str = "INFO"
    hdc_timeout: int = 30
    hdc_max_retries: int = 3
    transfer_max_workers: int = 3
    transfer_chunk_size: int = 1024 * 1024
    preview_max_size: int = 10 * 1024 * 1024
    default_remote_path: str = "/"
    show_upload_hint: bool = True
```

### 用户偏好配置
存储在项目目录 `config/config.json`：
- 主题偏好（light/dark）
- 语言偏好（en/zh）
- 窗口尺寸
- 其他配置参数

## 8. 项目目录结构

```
OpenHarmony_FileBrowser/
├── main.py                          # 顶层入口点
├── package/                         # 构建和打包脚本
│   ├── build.py                     # PyInstaller 打包脚本
│   ├── setup.py                     # Python 包安装配置
│   ├── MANIFEST.in                  # 资源文件清单
│   └── README.md                    # 构建说明
├── generate/                        # 图标生成工具
│   ├── generate.py                  # 图标生成脚本
│   └ README.md                      # 使用说明
├── config/                          # 配置目录
│   ├── config.json                  # 配置文件（提交到 git）
│   └── logs/                        # 日志目录（运行时生成）
├── requirements.txt                 # 运行时依赖
├── requirements-dev.txt             # 开发依赖
├── LICENSE                          # Apache 2.0 许可证
├── README.md                        # 项目说明文档
├── DESIGN.md                        # 设计文档（本文件）
├── .gitignore                       # Git排除规则
│
├── hdc/                             # HDC 工具二进制文件
│   ├── Darwin/
│   │   ├── x64/hdc, libusb_shared.dylib
│   │   └── arm64/hdc, libusb_shared.dylib
│   ├── Linux/
│   │   └── x64/hdc, libusb_shared.so
│   └── Windows/
│       └── x64/hdc.exe
│
├── src/                             # 源代码根目录
│   ├── __init__.py                  # 包初始化 (版本: 0.1.0)
│   ├── main.py                      # 应用主入口点
│   ├── config.py                    # 应用配置
│   │
│   ├── core/                        # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── hdc_wrapper.py           # HDC CLI 封装 (629 行)
│   │   ├── device_manager.py        # 设备连接/监控 (322 行)
│   │   ├── file_operations.py       # 文件 CRUD 操作 (308 行)
│   │   ├── transfer_manager.py      # 文件传输及进度 (469 行)
│   │   └── preview_handler.py       # 图片/视频预览 (209 行)
│   │
│   ├── gui/                         # GUI 组件 (PySide6/Qt)
│   │   ├── __init__.py
│   │   ├── main_window.py           # 主应用窗口 (464 行)
│   │   │
│   │   ├── widgets/                 # 可复用 UI 组件
│   │   │   ├── __init__.py
│   │   │   ├── file_browser.py      # 主文件浏览器组件 (694 行)
│   │   │   ├── file_tree.py         # 目录树视图 (247 行)
│   │   │   ├── file_list.py         # 文件列表/表格视图 (528 行)
│   │   │   ├── path_bar.py          # 面包屑导航栏 (186 行)
│   │   │   ├── device_panel.py      # 设备选择器 (117 行)
│   │   │   ├── dialogs.py           # 重命名/创建/删除对话框 (220 行)
│   │   │   ├── transfer_dialog.py   # 传输进度对话框 (380 行)
│   │   │   └── preview_window.py    # 图片/视频预览窗口 (364 行)
│   │   │
│   │   └── styles/                  # 主题和样式
│   │       ├── __init__.py
│   │       ├── theme_manager.py     # 浅色/深色主题管理 (163 行)
│   │       ├── main.qss             # 浅色主题样式表 (388 行)
│   │       ├── modern_light.qss     # 现代浅色主题
│   │       ├── modern_dark.qss      # 现代深色主题
│   │       └── main_v2.qss          # 备用样式表
│   │
│   ├── models/                      # 数据模型
│   │   ├── __init__.py
│   │   ├── device.py                # DeviceInfo, DeviceStatus (74 行)
│   │   └── file_info.py             # FileInfo, FileType (86 行)
│   │
│   ├── utils/                       # 工具模块
│   │   ├── __init__.py
│   │   ├── logger.py                # 日志配置 (69 行)
│   │   ├── file_utils.py            # 文件类型检测、格式化 (178 行)
│   │   ├── platform_utils.py        # 平台/架构检测、HDC 路径 (95 行)
│   │   ├── icon_manager.py          # SVG 图标管理，主题感知 (153 行)
│   │   ├── language_manager.py      # 国际化 英文/中文 (167 行)
│   │   └── async_loader.py          # 后台目录加载 (76 行)
│   │
│   └── resources/                   # 静态资源
│       ├── icons/
│       │   ├── light/*.svg          # 浅色主题 SVG 图标 (15 个)
│       │   └── dark/*.svg           # 深色主题 SVG 图标 (15 个)
│       └── i18n/
│           ├── en.json              # 英文翻译 (203 行)
│           └── zh.json              # 中文翻译 (203 行)
│
├── tests/                           # 测试套件
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/                        # 单元测试
│   │   ├── test_config.py
│   │   ├── test_device_model.py
│   │   ├── test_file_info_model.py
│   │   ├── test_file_operations.py
│   │   ├── test_file_utils.py
│   │   ├── test_gui_widgets.py
│   │   ├── test_language_manager.py
│   │   ├── test_platform_utils.py
│   │   ├── test_preview_handler.py
│   │   └── test_transfer_manager.py
│   └── integration/                 # 集成测试
│       └── test_integration.py
```

## 9. 扩展性设计

### 9.1 新增文件类型预览
在 `file_utils.py` 中添加新的文件类型检测逻辑，在 `preview_handler.py` 中添加对应的预览处理。

### 9.2 新增主题
在 `gui/styles/` 目录下添加新的 QSS 文件，并在 `theme_manager.py` 中注册。

### 9.3 新增语言支持
在 `resources/i18n/` 目录下添加新的 JSON 翻译文件，并在 `language_manager.py` 中注册。

### 9.4 新增设备连接方式
在 `device_manager.py` 中扩展连接逻辑，支持新的连接协议。

## 10. 安全考虑

- HDC 工具路径自动检测，避免硬编码路径
- 临时文件预览后自动清理
- 日志文件按日滚动，避免无限增长
- 用户偏好配置存储在用户目录，避免权限问题

## 11. 性能优化

- 异步目录加载（DirectoryLoadThread）防止 UI 阻塞
- 图标缓存（IconManager）减少重复加载
- 延迟初始化设备管理器加快启动速度
- 传输任务并发执行（默认 3 个工作线程）
- 设备状态轮询间隔可配置（默认 2 秒）