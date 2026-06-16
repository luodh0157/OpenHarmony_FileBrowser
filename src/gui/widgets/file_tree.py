"""
File tree widget for OpenHarmony File Browser.
Displays directory structure as a tree view with async loading.
"""

from typing import Optional, List, Dict
from PySide6.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
    QVBoxLayout,
    QStyle,
    QHeaderView,
)
from PySide6.QtCore import Qt, Signal, QTimer

from src.core.file_operations import FileOperations
from src.core.hdc_wrapper import HDCWrapper
from src.models.file_info import FileInfo
from src.utils.logger import get_logger
from src.utils.language_manager import language_manager
from src.utils.tree_loader import TreeLoadThread

logger = get_logger(__name__)

LOADING_ROLE = Qt.UserRole + 1


class FileTreeWidget(QWidget):
    """
    File tree widget showing directory structure.

    Features:
    - Tree view of directories
    - Async directory loading (non-blocking)
    - Directory expansion
    - Path navigation
    """

    directory_selected = Signal(str)

    def __init__(self):
        """Initialize file tree widget."""
        super().__init__()

        self.file_ops: Optional[FileOperations] = None
        self.hdc: Optional[HDCWrapper] = None
        self.device_id: Optional[str] = None

        self._load_threads: Dict[str, TreeLoadThread] = {}

        self._init_ui()

        logger.info("File tree widget initialized")

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel(language_manager.tr("file_tree.directories"))
        self.tree.setMinimumWidth(150)

        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree.setHorizontalScrollMode(QTreeWidget.ScrollPerPixel)

        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)

        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemExpanded.connect(self._on_item_expanded)

        layout.addWidget(self.tree)

    def update_language(self):
        """Update all UI texts when language changes."""
        self.tree.setHeaderLabel(language_manager.tr("file_tree.directories"))
        self._update_loading_texts()

    def _update_loading_texts(self):
        """Update loading text in tree items."""
        loading_text = language_manager.tr("file_tree.loading")
        self._update_item_loading_texts(self.tree.invisibleRootItem(), loading_text)

    def _update_item_loading_texts(self, parent_item, loading_text):
        """Recursively update loading text in tree items."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if child.data(0, Qt.UserRole) is None and child.text(0) in [
                "Loading...",
                "加载中...",
            ]:
                child.setText(0, loading_text)
            self._update_item_loading_texts(child, loading_text)

    def set_device(self, device_id: str, hdc: HDCWrapper):
        """Set device for file tree."""
        self.clear_device()

        self.device_id = device_id
        self.hdc = hdc
        self.file_ops = FileOperations(hdc, device_id)

        self._load_root_directory()

        logger.info(f"Device set for file tree: {device_id}")

    def clear_device(self):
        """Clear current device."""
        self._cancel_all_loads()
        self._load_threads.clear()

        if self.file_ops:
            self.file_ops.clear_cache()

        self.device_id = None
        self.hdc = None
        self.file_ops = None

        self.tree.clear()

        logger.info("Device cleared from file tree")

    def _cancel_all_loads(self):
        """Cancel all pending load threads."""
        for path, thread in self._load_threads.items():
            try:
                if thread.isRunning():
                    thread.cancel()
                    thread.wait(200)
            except RuntimeError:
                pass

    def _load_root_directory(self):
        """Load root directory with lazy loading."""
        if not self.file_ops:
            return

        try:
            root_item = QTreeWidgetItem(self.tree, ["/"])
            root_item.setData(0, Qt.UserRole, "/")
            root_item.setExpanded(False)
            root_item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))

            loading_text = language_manager.tr("file_tree.loading")
            placeholder = QTreeWidgetItem(root_item, [loading_text])
            placeholder.setData(0, Qt.UserRole, None)

            logger.debug("Root directory loaded (lazy)")

        except Exception as e:
            logger.error(f"Failed to load root directory: {e}")

    def _add_placeholder(self, parent_item: QTreeWidgetItem):
        """Add a loading placeholder to a tree item."""
        loading_text = language_manager.tr("file_tree.loading")
        placeholder = QTreeWidgetItem(parent_item, [loading_text])
        placeholder.setData(0, Qt.UserRole, None)

    def _populate_directories(
        self, parent_item: QTreeWidgetItem, directories: List[FileInfo]
    ):
        """Add directory items to a parent tree item."""
        loading_text = language_manager.tr("file_tree.loading")

        for dir_info in directories:
            child_item = QTreeWidgetItem(parent_item, [dir_info.name])
            child_item.setData(0, Qt.UserRole, dir_info.path)
            child_item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))

            placeholder = QTreeWidgetItem(child_item, [loading_text])
            placeholder.setData(0, Qt.UserRole, None)

        logger.debug(
            f"Populated {len(directories)} directories under: {parent_item.text(0)}"
        )

    def _load_directory_contents_async(
        self, path: str, parent_item: QTreeWidgetItem, delay_ms: int = 0
    ):
        """
        Load directory contents asynchronously (non-blocking).

        Args:
            path: Directory path
            parent_item: Parent tree item
            delay_ms: Optional delay to let file_list populate cache first
        """
        if not self.file_ops:
            return

        if delay_ms > 0:
            QTimer.singleShot(
                delay_ms, lambda: self._do_load_directory(path, parent_item)
            )
        else:
            self._do_load_directory(path, parent_item)

    def _do_load_directory(self, path: str, parent_item: QTreeWidgetItem):
        """Actually perform the directory load."""
        if not self.file_ops:
            return

        cached_dirs = self.file_ops.cache.get_child_dirs(path)
        if cached_dirs:
            self._populate_directories(parent_item, cached_dirs)
            logger.debug(f"Using cached directory contents for: {path}")
            return

        if path in self._load_threads:
            try:
                if self._load_threads[path].isRunning():
                    logger.debug(f"Load already in progress for: {path}")
                    return
            except RuntimeError:
                pass

        thread = TreeLoadThread(self.file_ops, path)
        thread.loaded.connect(
            lambda dirs, item=parent_item, p=path: self._on_tree_loaded(p, item, dirs)
        )
        thread.error.connect(lambda err, p=path: self._on_tree_error(p, err))

        self._load_threads[path] = thread
        thread.start()

    def _on_tree_loaded(
        self, path: str, parent_item: QTreeWidgetItem, directories: List[FileInfo]
    ):
        """Handle async tree load completion."""
        self._load_threads.pop(path, None)
        self._populate_directories(parent_item, directories)

    def _on_tree_error(self, path: str, error_msg: str):
        """Handle async tree load error."""
        self._load_threads.pop(path, None)
        logger.error(f"Failed to load tree directory {path}: {error_msg}")

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click."""
        path = item.data(0, Qt.UserRole)

        if path:
            self.directory_selected.emit(path)
            logger.debug(f"Directory selected: {path}")

    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Handle item expansion - load children asynchronously with cache delay."""
        path = item.data(0, Qt.UserRole)
        loading_text = language_manager.tr("file_tree.loading")

        if not path:
            return

        if item.childCount() > 0:
            first_child = item.child(0)
            if first_child.text(0) == loading_text:
                item.takeChild(0)
                # Delay 100ms to let file_list populate cache first
                self._load_directory_contents_async(path, item, delay_ms=100)

        logger.debug(f"Directory expanded: {path}")

    def refresh_directory(self, path: str):
        """Refresh a specific directory."""
        items = self.tree.findItems(
            path.split("/")[-1] if path != "/" else "/", Qt.MatchExactly, 0
        )

        for item in items:
            item_path = item.data(0, Qt.UserRole)
            if item_path == path:
                while item.childCount() > 0:
                    item.takeChild(0)

                self._load_directory_contents_async(path, item, delay_ms=100)

                logger.info(f"Directory refreshed: {path}")
                break

    def expand_to_path(self, path: str):
        """
        Expand tree to show specific path (async, non-blocking).

        Only expands items that are already loaded. For unloaded items,
        triggers async load with a delay to let file_list populate cache first.
        """
        parts = path.split("/")
        parts = [p for p in parts if p]

        current_item = self.tree.topLevelItem(0)
        if not current_item:
            return

        current_path = "/"
        loading_text = language_manager.tr("file_tree.loading")

        for part in parts:
            if not current_item:
                break

            first_child = (
                current_item.child(0) if current_item.childCount() > 0 else None
            )

            if first_child and first_child.text(0) == loading_text:
                current_item.takeChild(0)
                target_path = (
                    f"{current_path}/{part}" if current_path != "/" else f"/{part}"
                )
                # fmt: off
                remaining = parts[parts.index(part):]
                # fmt: on
                # Delay to let file_list populate cache first
                self._load_and_expand(
                    current_item, target_path, remaining, delay_ms=150
                )
                return

            found = False
            for i in range(current_item.childCount()):
                child = current_item.child(i)
                if child.text(0) == part:
                    child.setExpanded(True)
                    current_item = child
                    current_path = f"{current_path}/{part}"
                    found = True
                    break

            if not found:
                break

        if current_item:
            self.tree.setCurrentItem(current_item)
            self.directory_selected.emit(path)

    def _load_and_expand(
        self,
        parent_item: QTreeWidgetItem,
        target_path: str,
        remaining_parts: List[str],
        delay_ms: int = 150,
    ):
        """
        Load directory contents asynchronously, then continue expanding to target path.

        Args:
            parent_item: Current tree item to load children under
            target_path: Final path we want to expand to
            remaining_parts: Remaining path parts to traverse
            delay_ms: Delay before querying to let file_list populate cache
        """
        if not self.file_ops:
            return

        def on_loaded(directories):
            self._populate_directories(parent_item, directories)

            if not remaining_parts:
                self.directory_selected.emit(target_path)
                return

            next_part = remaining_parts[0]
            current_path = target_path.rsplit("/", 1)[0] or "/"

            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                if child.text(0) == next_part:
                    child.setExpanded(True)
                    self._expand_remaining(
                        child, current_path, next_part, remaining_parts[1:]
                    )
                    break

        def on_error(err):
            logger.error(f"Failed to load {target_path}: {err}")
            self.directory_selected.emit(target_path)

        cached_dirs = self.file_ops.cache.get_child_dirs(
            target_path.rsplit("/", 1)[0] or "/"
        )
        if cached_dirs:
            on_loaded(cached_dirs)
            return

        if delay_ms > 0:
            QTimer.singleShot(
                delay_ms,
                lambda: self._start_tree_load(
                    target_path.rsplit("/", 1)[0] or "/", on_loaded, on_error
                ),
            )
        else:
            self._start_tree_load(
                target_path.rsplit("/", 1)[0] or "/", on_loaded, on_error
            )

    def _start_tree_load(self, path, on_loaded, on_error):
        """Start a tree load thread for the given path."""
        cached_dirs = self.file_ops.cache.get_child_dirs(path)
        if cached_dirs:
            on_loaded(cached_dirs)
            return

        if path in self._load_threads:
            try:
                if self._load_threads[path].isRunning():
                    return
            except RuntimeError:
                pass

        thread = TreeLoadThread(self.file_ops, path)
        thread.loaded.connect(
            lambda dirs: self._on_tree_thread_loaded(path, dirs, on_loaded)
        )
        thread.error.connect(
            lambda err: self._on_tree_thread_error(path, err, on_error)
        )

        self._load_threads[path] = thread
        thread.start()

    def _on_tree_thread_loaded(self, path, directories, on_loaded):
        """Handle tree thread completion and clean up."""
        self._load_threads.pop(path, None)
        on_loaded(directories)

    def _on_tree_thread_error(self, path, error_msg, on_error):
        """Handle tree thread error and clean up."""
        self._load_threads.pop(path, None)
        on_error(error_msg)

    def _expand_remaining(self, current_item, current_path, part, remaining_parts):
        """Continue expanding remaining path parts."""
        new_path = f"{current_path}/{part}" if current_path != "/" else f"/{part}"
        loading_text = language_manager.tr("file_tree.loading")

        if not remaining_parts:
            self.tree.setCurrentItem(current_item)
            self.directory_selected.emit(new_path)
            return

        first_child = current_item.child(0) if current_item.childCount() > 0 else None
        if first_child and first_child.text(0) == loading_text:
            current_item.takeChild(0)
            next_part = remaining_parts[0]
            target_path = f"{new_path}/{next_part}"
            self._load_and_expand(
                current_item, target_path, remaining_parts, delay_ms=150
            )
            return

        for next_part in remaining_parts:
            found = False
            for i in range(current_item.childCount()):
                child = current_item.child(i)
                if child.text(0) == next_part:
                    child.setExpanded(True)
                    current_item = child
                    new_path = f"{new_path}/{next_part}"
                    found = True
                    break

            if not found:
                break

        self.tree.setCurrentItem(current_item)
        self.directory_selected.emit(new_path)
