"""
File tree widget for OpenHarmony File Browser.
Displays directory structure as a tree view.
"""

from typing import Optional, List
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QLabel, QStyle, QHeaderView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from src.core.file_operations import FileOperations
from src.core.hdc_wrapper import HDCWrapper
from src.models.file_info import FileInfo
from src.utils.logger import get_logger
from src.utils.language_manager import language_manager


logger = get_logger(__name__)


class FileTreeWidget(QWidget):
    """
    File tree widget showing directory structure.
    
    Features:
    - Tree view of directories
    - Async loading (placeholder for now)
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
        
        self._init_ui()
        
        logger.info("File tree widget initialized")
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel(language_manager.tr('file_tree.directories'))
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
        self.tree.setHeaderLabel(language_manager.tr('file_tree.directories'))
        # Update any "Loading..." placeholders in existing tree items
        self._update_loading_texts()
    
    def _update_loading_texts(self):
        """Update loading text in tree items."""
        loading_text = language_manager.tr('file_tree.loading')
        self._update_item_loading_texts(self.tree.invisibleRootItem(), loading_text)
    
    def _update_item_loading_texts(self, parent_item, loading_text):
        """Recursively update loading text in tree items."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if child.data(0, Qt.UserRole) is None and child.text(0) in ["Loading...", "加载中..."]:
                child.setText(0, loading_text)
            self._update_item_loading_texts(child, loading_text)
    
    def set_device(self, device_id: str, hdc: HDCWrapper):
        """
        Set device for file tree.
        
        Args:
            device_id: Device ID
            hdc: HDC wrapper instance
        """
        # Clear old device first to avoid duplicate root directories
        self.clear_device()
        
        self.device_id = device_id
        self.hdc = hdc
        self.file_ops = FileOperations(hdc, device_id)
        
        self._load_root_directory()
        
        logger.info(f"Device set for file tree: {device_id}")
    
    def clear_device(self):
        """Clear current device."""
        self.device_id = None
        self.hdc = None
        self.file_ops = None
        
        self.tree.clear()
        
        logger.info("Device cleared from file tree")
    
    def _load_root_directory(self):
        """Load root directory."""
        if not self.file_ops:
            return
        
        try:
            logger.debug("Loading root directory")
            
            root_item = QTreeWidgetItem(self.tree, ["/"])
            root_item.setData(0, Qt.UserRole, "/")
            root_item.setExpanded(False)
            root_item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
            
            self._load_directory_contents("/", root_item)
            
            logger.debug("Root directory loaded")
        
        except Exception as e:
            logger.error(f"Failed to load root directory: {e}")
    
    def _load_directory_contents(self, path: str, parent_item: QTreeWidgetItem):
        """
        Load directory contents into tree item.
        
        Args:
            path: Directory path
            parent_item: Parent tree item
        """
        if not self.file_ops:
            return
        
        try:
            files = self.file_ops.list_directory(path, show_hidden=False)
            
            directories = [f for f in files if f.is_dir]
            loading_text = language_manager.tr('file_tree.loading')
            
            for dir_info in directories:
                child_item = QTreeWidgetItem(parent_item, [dir_info.name])
                child_item.setData(0, Qt.UserRole, dir_info.path)
                child_item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
                
                placeholder = QTreeWidgetItem(child_item, [loading_text])
                placeholder.setData(0, Qt.UserRole, None)
            
            logger.debug(f"Loaded {len(directories)} directories in {path}")
        
        except Exception as e:
            logger.error(f"Failed to load directory contents {path}: {e}")
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click."""
        path = item.data(0, Qt.UserRole)
        
        if path:
            self.directory_selected.emit(path)
            logger.debug(f"Directory selected: {path}")
    
    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Handle item expansion."""
        path = item.data(0, Qt.UserRole)
        loading_text = language_manager.tr('file_tree.loading')
        
        if not path:
            return
        
        if item.childCount() > 0:
            first_child = item.child(0)
            if first_child.text(0) == loading_text:
                item.takeChild(0)
                self._load_directory_contents(path, item)
        
        logger.debug(f"Directory expanded: {path}")
    
    def refresh_directory(self, path: str):
        """
        Refresh a specific directory.
        
        Args:
            path: Directory path to refresh
        """
        items = self.tree.findItems(path.split("/")[-1] if path != "/" else "/", Qt.MatchExactly, 0)
        
        for item in items:
            item_path = item.data(0, Qt.UserRole)
            if item_path == path:
                for i in range(item.childCount()):
                    item.takeChild(i)
                
                self._load_directory_contents(path, item)
                
                logger.info(f"Directory refreshed: {path}")
                break
    
    def expand_to_path(self, path: str):
        """
        Expand tree to show specific path.
        
        Args:
            path: Path to expand to
        """
        parts = path.split("/")
        parts = [p for p in parts if p]
        
        current_path = "/"
        current_item = self.tree.topLevelItem(0)
        
        if current_item:
            current_item.setExpanded(True)
        
        for part in parts:
            if not current_item:
                break
            
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
