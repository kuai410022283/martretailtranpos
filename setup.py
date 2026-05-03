from cx_Freeze import setup, Executable
import os
import sys

# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))

# 确保资源目录存在
resources_dir = os.path.join(project_root, "resources")
if not os.path.exists(resources_dir):
    os.makedirs(resources_dir)

# 收集所有需要包含的文件和目录
include_files = [
    ("resources", "resources"),
    ("core", "core"),
    ("modules", "modules"),
    ("shared", "shared"),
    ("plugins", "plugins"),
    ("README.md", "README.md"),
    ("requirements.txt", "requirements.txt")
]

# 排除不必要的模块
excludes = [
    "tkinter",
    "test",
    "unittest",
    "pydoc",
    "doctest",
    "PyQt5.QtWebEngineWidgets",
    "PyQt5.QtWebEngine",
    "PyQt5.QtWebKit",
    "PyQt5.QtDesigner",
    "numpy",
    "scipy",
    "matplotlib",
    "IPython"
]

# 包含必要的模块
includes = [
    "core",
    "modules",
    "shared",
    "plugins",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtWidgets",
    "sqlalchemy",
    "python_barcode",
    "qrcode",
    "PIL",
    "openpyxl",
    "reportlab",
    "apscheduler"
]

# 打包选项
options = {
    "build_exe": {
        "includes": includes,
        "excludes": excludes,
        "include_files": include_files,
        "packages": ["core", "modules", "shared", "plugins"],
        "namespace_packages": [],
        "include_msvcr": True,  # 包含 Microsoft Visual C++ 运行时
        "optimize": 2,  # 代码优化级别
        "build_exe": os.path.join(project_root, "build", "MRTPOS")
    }
}

# 可执行文件配置
executables = [
    Executable(
        script="run.py",
        base="Win32GUI" if sys.platform == "win32" else None,  # Windows 下隐藏控制台
        target_name="MRTPOS.exe",
        icon=os.path.join(resources_dir, "icons", "app.ico") if os.path.exists(os.path.join(resources_dir, "icons", "app.ico")) else None,
        shortcut_name="MartRetailTranPOS",
        shortcut_dir="ProgramMenuFolder"
    )
]

# 项目信息
setup(
    name="MartRetailTranPOS",
    version="1.0.0",
    description="超市零售进销存管理系统",
    author="",
    author_email="",
    url="",
    options=options,
    executables=executables,
    packages=["core", "modules", "shared", "plugins"],
    package_dir={
        "core": "core",
        "modules": "modules",
        "shared": "shared",
        "plugins": "plugins"
    }
)
