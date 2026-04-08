#!/usr/bin/env python3
"""
检查所需的Python依赖包
"""

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sys
import os
from fgps._paths import CORE_ROOT, DATA_ROOT

def check_import(module_name, package_name=None):
    """检查模块是否可以导入"""
    try:
        __import__(module_name)
        print(f"✓ {module_name} - 可用")
        return True
    except ImportError as e:
        pkg = package_name or module_name
        print(f"✗ {module_name} - 缺失 (需要安装: pip install {pkg})")
        print(f"  错误: {e}")
        return False

def check_path_access(path, description):
    """检查路径访问权限"""
    try:
        if os.path.exists(path):
            if os.access(path, os.R_OK):
                print(f"✓ {description}: {path} - 可读")
                if os.access(path, os.W_OK):
                    print(f"✓ {description}: {path} - 可写")
                    return True
                else:
                    print(f"⚠ {description}: {path} - 只读")
                    return False
            else:
                print(f"✗ {description}: {path} - 无读取权限")
                return False
        else:
            print(f"✗ {description}: {path} - 路径不存在")
            return False
    except Exception as e:
        print(f"✗ {description}: {path} - 检查失败: {e}")
        return False

def main():
    print("=" * 50)
    print("FGPS Python依赖检测")
    print("=" * 50)
    
    print("\n1. Python基本信息:")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"当前工作目录: {os.getcwd()}")
    
    print("\n2. 检查必要的Python包:")
    required_packages = [
        ("json", None),
        ("os", None),
        ("sys", None),
        ("multiprocessing", None),
        ("time", None),
        ("random", None),
        ("warnings", None),
        ("psutil", "psutil"),
        ("func_timeout", "func-timeout"),
    ]
    
    missing_packages = []
    for module, package in required_packages:
        if not check_import(module, package):
            missing_packages.append(package or module)
    
    print("\n3. 检查Hilbert-Geo相关包:")
    formalgeo_modules = [
        "hilbert_geo",
        "hilbert_geo.solver",
        "hilbert_geo.tools", 
        "hilbert_geo.data"
    ]
    
    formalgeo_missing = []
    for module in formalgeo_modules:
        if not check_import(module, "hilbert-geo"):
            formalgeo_missing.append(module)
    
    print("\n4. 检查项目路径:")
    paths_to_check = [
        (str(CORE_ROOT), "core 路径"),
        (str(DATA_ROOT), "data 路径"),
    ]
    
    path_issues = []
    for path, desc in paths_to_check:
        if not check_path_access(path, desc):
            path_issues.append((path, desc))
    
    print("\n5. 检查Python路径设置:")
    current_path = os.environ.get('PYTHONPATH', '')
    print(f"PYTHONPATH: {current_path}")
    
    # 检查项目是否在Python路径中
    project_path = str(CORE_ROOT)
    if project_path in sys.path:
        print(f"✓ 项目路径已在sys.path中: {project_path}")
    else:
        print(f"⚠ 项目路径不在sys.path中: {project_path}")
        print("  尝试添加到sys.path...")
        sys.path.append(project_path)
        print(f"✓ 已添加项目路径到sys.path")
    
    print("\n6. 尝试导入项目模块:")
    try:
        sys.path.append(project_path)
        from fgps import get_args, method, strategy
        print("✓ fgps模块导入成功")
        
        from fgps.utils import create_log_archi
        print("✓ fgps.utils模块导入成功")
        
        # 测试create_log_archi函数
        test_path = "/tmp/test_fgps_log"
        try:
            create_log_archi(test_path)
            print(f"✓ create_log_archi函数测试成功 (测试路径: {test_path})")
            # 清理测试目录
            import shutil
            if os.path.exists(test_path):
                shutil.rmtree(test_path)
        except Exception as e:
            print(f"✗ create_log_archi函数测试失败: {e}")
            
    except Exception as e:
        print(f"✗ 项目模块导入失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("检测总结:")
    print("=" * 50)
    
    if missing_packages:
        print("⚠ 缺失的Python包:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("安装命令: pip install " + " ".join(missing_packages))
    
    if formalgeo_missing:
        print("⚠ Hilbert-Geo相关模块问题:")
        for module in formalgeo_missing:
            print(f"  - {module}")
        print("请检查Hilbert-Geo是否正确安装")
    
    if path_issues:
        print("⚠ 路径权限问题:")
        for path, desc in path_issues:
            print(f"  - {desc}: {path}")
    
    if not missing_packages and not formalgeo_missing and not path_issues:
        print("✓ 所有检查都通过！环境配置正常。")
    else:
        print("✗ 发现问题，请根据上述信息修复。")
    
    print("\n检测完成！")

if __name__ == "__main__":
    main()
