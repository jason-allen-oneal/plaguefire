# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Plaguefire
Dynamically locates the textual and rich packages to ensure cross-platform compatibility.
"""

import os
import sys
import sysconfig
from pathlib import Path

def find_package_path(package_name):
    """
    Find the installation path of a package.
    Tries multiple strategies to locate the package in site-packages.
    """
    # Strategy 1: Check sysconfig purelib path
    purelib = sysconfig.get_paths().get('purelib')
    if purelib and (Path(purelib) / package_name).exists():
        return str(Path(purelib) / package_name)
    
    # Strategy 2: Check site.getsitepackages() paths
    try:
        import site
        for site_path in site.getsitepackages():
            package_path = Path(site_path) / package_name
            if package_path.exists():
                return str(package_path)
    except Exception:
        pass
    
    # Strategy 3: Import the package and get its location
    try:
        module = __import__(package_name)
        module_file = getattr(module, '__file__', None)
        if module_file:
            return str(Path(module_file).parent)
    except Exception:
        pass
    
    return None

# Locate textual and rich packages
textual_path = find_package_path('textual')
rich_path = find_package_path('rich')

if textual_path is None:
    raise RuntimeError('Could not locate textual package in site-packages')
if rich_path is None:
    raise RuntimeError('Could not locate rich package in site-packages')

print(f"Found textual at: {textual_path}")
print(f"Found rich at: {rich_path}")

# PyInstaller Analysis
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (textual_path, 'textual'),
        (rich_path, 'rich'),
        ('data', 'data'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'textual',
        'rich',
        'pygame',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='plaguefire',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
