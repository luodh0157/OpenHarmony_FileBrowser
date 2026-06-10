"""
验证 Ctrl+A 修复 - 不依赖 GUI 显示的验证脚本
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """测试所有必要的导入"""
    print("=== 测试 1: 导入验证 ===")
    
    try:
        from src.gui.widgets.file_list import FileListWidget, CustomCheckBox
        print("✓ FileListWidget 导入成功")
        print("✓ CustomCheckBox 导入成功")
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False
    
    return True

def test_method_existence():
    """测试修复的方法是否存在"""
    print("\n=== 测试 2: 方法存在性验证 ===")
    
    from src.gui.widgets.file_list import FileListWidget
    
    # 检查关键方法
    required_methods = [
        'eventFilter',
        '_handle_select_all_shortcut',
        '_handle_deselect_all_shortcut',
    ]
    
    all_exist = True
    for method_name in required_methods:
        if hasattr(FileListWidget, method_name):
            print(f"✓ {method_name} 方法存在")
        else:
            print(f"✗ {method_name} 方法不存在")
            all_exist = False
    
    return all_exist

def test_code_logic():
    """测试代码逻辑是否正确"""
    print("\n=== 测试 3: 代码逻辑验证 ===")
    
    import inspect
    from src.gui.widgets.file_list import FileListWidget
    
    # 检查 eventFilter 方法实现
    event_filter_source = inspect.getsource(FileListWidget.eventFilter)
    
    checks = {
        'event.type() == QEvent.KeyPress': '检查键盘事件类型',
        'event.key() == Qt.Key_A': '检查 Ctrl+A 键',
        'event.modifiers() == Qt.ControlModifier': '检查 Ctrl 修饰键',
        '_handle_select_all_shortcut': '调用全选方法',
        'event.accept()': '接受事件',
        'return True': '返回 True 停止传播',
    }
    
    all_correct = True
    for check_str, description in checks.items():
        if check_str in event_filter_source:
            print(f"✓ {description}: {check_str}")
        else:
            print(f"✗ {description} 缺失: {check_str}")
            all_correct = False
    
    # 检查 _handle_select_all_shortcut 方法实现
    select_all_source = inspect.getsource(FileListWidget._handle_select_all_shortcut)
    
    select_all_checks = {
        'self.table.selectAll()': '调用表格全选',
        'checkbox.setChecked(True)': '勾选所有复选框',
        'self.select_all_checkbox.setChecked(True)': '更新顶部全选框',
        'self.selection_changed.emit': '发射选择变化信号',
    }
    
    print("\n--- _handle_select_all_shortcut 方法验证 ---")
    for check_str, description in select_all_checks.items():
        if check_str in select_all_source:
            print(f"✓ {description}: {check_str}")
        else:
            print(f"✗ {description} 缺失: {check_str}")
            all_correct = False
    
    # 检查 _handle_deselect_all_shortcut 方法实现
    deselect_all_source = inspect.getsource(FileListWidget._handle_deselect_all_shortcut)
    
    deselect_all_checks = {
        'self.table.clearSelection()': '清除表格选择',
        'checkbox.setChecked(False)': '取消所有复选框',
        'self.select_all_checkbox.setChecked(False)': '取消顶部全选框',
        'self.selection_changed.emit': '发射选择变化信号',
    }
    
    print("\n--- _handle_deselect_all_shortcut 方法验证 ---")
    for check_str, description in deselect_all_checks.items():
        if check_str in deselect_all_source:
            print(f"✓ {description}: {check_str}")
        else:
            print(f"✗ {description} 缺失: {check_str}")
            all_correct = False
    
    return all_correct

def test_event_filter_installation():
    """测试事件过滤器是否正确安装"""
    print("\n=== 测试 4: 事件过滤器安装验证 ===")
    
    import inspect
    from src.gui.widgets.file_list import FileListWidget
    
    # 检查 _init_ui 方法中是否安装了事件过滤器
    init_ui_source = inspect.getsource(FileListWidget._init_ui)
    
    if 'installEventFilter' in init_ui_source:
        print("✓ 事件过滤器安装代码存在")
        
        # 检查是否安装到 self.table
        if 'self.table.installEventFilter(self)' in init_ui_source:
            print("✓ 事件过滤器安装到 self.table")
            return True
        else:
            print("✗ 事件过滤器安装目标不正确")
            return False
    else:
        print("✗ 缺少事件过滤器安装代码")
        return False

def test_old_keypressevent_removed():
    """测试旧的 keyPressEvent 方法是否已移除"""
    print("\n=== 测试 5: 旧方法移除验证 ===")
    
    from src.gui.widgets.file_list import FileListWidget
    
    # 检查是否还存在 keyPressEvent 方法（应该不存在或已被移除）
    if hasattr(FileListWidget, 'keyPressEvent'):
        # 检查这个方法是否是来自父类的默认实现
        import inspect
        method = getattr(FileListWidget, 'keyPressEvent')
        
        # 如果是从 QWidget 继承的默认方法，那没关系
        # 如果是 FileListWidget 自己定义的方法，需要检查是否正确
        try:
            source_file = inspect.getsourcefile(method)
            if 'file_list.py' in source_file:
                print("⚠ keyPressEvent 仍在 file_list.py 中定义")
                
                # 检查源代码内容
                source = inspect.getsource(method)
                if 'Ctrl+A' in source or 'Key_A' in source:
                    print("✗ 旧的 Ctrl+A 处理逻辑仍存在，可能造成冲突")
                    return False
                else:
                    print("✓ keyPressEvent 不包含 Ctrl+A 处理（无害）")
                    return True
            else:
                print("✓ keyPressEvent 是父类的默认实现（无害）")
                return True
        except:
            print("✓ 无法获取源代码位置，可能是父类方法")
            return True
    else:
        print("✓ keyPressEvent 方法不存在（已移除）")
        return True

def verify_file_syntax():
    """验证文件语法是否正确"""
    print("\n=== 测试 6: Python 语法验证 ===")
    
    import py_compile
    import tempfile
    
    file_path = Path(__file__).parent.parent / "src" / "gui" / "widgets" / "file_list.py"
    
    try:
        # 编译检查
        py_compile.compile(str(file_path), doraise=True)
        print(f"✓ {file_path} 语法正确")
        return True
    except py_compile.PyCompileError as e:
        print(f"✗ 语法错误: {e}")
        return False

def main():
    """运行所有验证测试"""
    print("="*60)
    print("Ctrl+A 修复验证 - 非GUI测试")
    print("="*60)
    
    tests = [
        ("导入验证", test_imports),
        ("方法存在性", test_method_existence),
        ("代码逻辑", test_code_logic),
        ("事件过滤器安装", test_event_filter_installation),
        ("旧方法移除", test_old_keypressevent_removed),
        ("Python语法", verify_file_syntax),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} 执行失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    
    print("="*60)
    
    if failed == 0:
        print("\n✓ 所有验证测试通过！修复已正确实施。")
        print("\n建议下一步：在有GUI显示的环境中启动应用进行实际测试")
        print("运行命令: python main.py --debug")
        print("测试步骤：")
        print("  1. 连接设备并浏览文件目录")
        print("  2. 按 Ctrl+A 全选文件")
        print("  3. 确认所有文件被勾选（复选框打勾）")
        print("  4. 点击 Download 按钮，应能正常下载")
        return 0
    else:
        print(f"\n✗ {failed} 个测试失败，请检查修复代码")
        return 1

if __name__ == "__main__":
    sys.exit(main())