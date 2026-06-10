"""
综合验证脚本 - 验证所有修复的功能
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_all_imports():
    """测试所有必要的导入"""
    print("\n=== 测试 1: 综合导入验证 ===")
    
    imports_to_test = [
        ("src.gui.widgets.file_list", "FileListWidget"),
        ("src.gui.widgets.file_browser", "FileBrowserWidget"),
        ("src.core.file_operations", "FileOperations"),
        ("PySide6.QtWidgets", "QMessageBox"),
    ]
    
    all_success = True
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            class_obj = getattr(module, class_name)
            print(f"✓ {module_name}.{class_name} 导入成功")
        except Exception as e:
            print(f"✗ {module_name}.{class_name} 导入失败: {e}")
            all_success = False
    
    return all_success

def test_qmessagebox_import():
    """验证 QMessageBox 导入修复"""
    print("\n=== 测试 2: QMessageBox 导入修复验证 ===")
    
    try:
        from src.gui.widgets.file_browser import FileBrowserWidget
        import inspect
        
        # 检查 file_browser.py 的导入语句
        source = inspect.getsource(FileBrowserWidget)
        if 'QMessageBox' in source:
            print("✓ QMessageBox 在 file_browser.py 中已导入")
        else:
            print("✗ QMessageBox 未在 file_browser.py 中导入")
            return False
        
        # 尝试导入验证
        from PySide6.QtWidgets import QMessageBox
        print("✓ QMessageBox 可以正常导入")
        
        return True
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        return False

def test_file_operations_methods():
    """验证 FileOperations 方法名修复"""
    print("\n=== 测试 3: FileOperations 方法名修复验证 ===")
    
    try:
        from src.core.file_operations import FileOperations
        
        # 正确的方法名
        correct_methods = {
            'get_parent_directory': '获取父目录',
            'join_path': '连接路径',
            'rename_file': '重命名文件',
        }
        
        all_correct = True
        for method_name, description in correct_methods.items():
            if hasattr(FileOperations, method_name):
                print(f"✓ {method_name}() 方法存在 - {description}")
            else:
                print(f"✗ {method_name}() 方法不存在 - {description}")
                all_correct = False
        
        # 错误的方法名（应该不存在）
        wrong_methods = {
            'get_parent_path': '旧的错误方法名',
            'rename': '旧的错误方法名',
        }
        
        print("\n--- 验证旧方法名已不存在 ---")
        for method_name, description in wrong_methods.items():
            if hasattr(FileOperations, method_name):
                print(f"⚠ {method_name}() 仍存在（可能是旧版本）- {description}")
            else:
                print(f"✓ {method_name}() 不存在（正确）- {description}")
        
        return all_correct
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        return False

def test_file_browser_rename_method():
    """验证 file_browser.py 的 _rename 方法修复"""
    print("\n=== 测试 4: _rename() 方法修复验证 ===")
    
    try:
        from src.gui.widgets.file_browser import FileBrowserWidget
        import inspect
        
        # 获取 _rename 方法的源代码
        source = inspect.getsource(FileBrowserWidget._rename)
        
        # 检查是否使用了正确的方法名
        checks = {
            'get_parent_directory': '调用 get_parent_directory()',
            'rename_file': '调用 rename_file()',
        }
        
        wrong_calls = {
            'get_parent_path': '错误调用 get_parent_path()',
            '.rename(': '错误调用 .rename()',
        }
        
        all_correct = True
        
        print("--- 检查正确的方法调用 ---")
        for check_str, description in checks.items():
            if check_str in source:
                print(f"✓ {description}: {check_str}")
            else:
                print(f"✗ {description} 缺失: {check_str}")
                all_correct = False
        
        print("\n--- 检查错误的方法调用已移除 ---")
        for wrong_str, description in wrong_calls.items():
            if wrong_str in source:
                print(f"✗ {description} 仍存在: {wrong_str}")
                all_correct = False
            else:
                print(f"✓ {description} 已移除: {wrong_str}")
        
        return all_correct
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ctrl_a_fix():
    """验证 Ctrl+A 修复"""
    print("\n=== 测试 5: Ctrl+A 修复验证 ===")
    
    try:
        from src.gui.widgets.file_list import FileListWidget
        import inspect
        
        # 检查关键方法
        required_methods = [
            'eventFilter',
            '_handle_select_all_shortcut',
            '_handle_deselect_all_shortcut',
        ]
        
        all_exist = True
        for method in required_methods:
            if hasattr(FileListWidget, method):
                print(f"✓ {method}() 方法存在")
            else:
                print(f"✗ {method}() 方法不存在")
                all_exist = False
        
        # 检查 eventFilter 实现逻辑
        if hasattr(FileListWidget, 'eventFilter'):
            source = inspect.getsource(FileListWidget.eventFilter)
            
            checks = {
                'QEvent.KeyPress': '检查键盘事件',
                'Qt.Key_A': '检查 A 键',
                'Qt.ControlModifier': '检查 Ctrl 修饰键',
            }
            
            print("\n--- eventFilter 实现验证 ---")
            for check_str, description in checks.items():
                if check_str in source:
                    print(f"✓ {description}: {check_str}")
                else:
                    print(f"✗ {description} 缺失: {check_str}")
                    all_exist = False
        
        return all_exist
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        return False

def main():
    """运行所有验证测试"""
    print("="*60)
    print("OpenHarmony File Browser - 综合修复验证")
    print("="*60)
    
    tests = [
        ("综合导入验证", test_all_imports),
        ("QMessageBox导入", test_qmessagebox_import),
        ("FileOperations方法名", test_file_operations_methods),
        ("_rename方法修复", test_file_browser_rename_method),
        ("Ctrl+A修复", test_ctrl_a_fix),
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
        print("\n✓ 所有修复验证通过！")
        print("\n已修复的功能：")
        print("  1. Ctrl+A 全选功能 - 修复复选框同步问题")
        print("  2. QMessageBox 导入 - 修复删除确认对话框")
        print("  3. 文件重命名功能 - 修复方法名不匹配")
        print("\n建议进行实际测试：")
        print("  - 启动应用: python main.py --debug")
        print("  - 连接设备测试各项功能")
        return 0
    else:
        print(f"\n✗ {failed} 个测试失败，需要检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())