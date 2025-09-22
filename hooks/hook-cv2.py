# -*- coding: utf-8 -*-
"""
OpenCV-Python用のPyInstallerフック
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

# OpenCVのデータファイルを収集
datas = collect_data_files('cv2')

# OpenCVの動的ライブラリを収集
binaries = collect_dynamic_libs('cv2')

# OpenCVのサブモジュールを収集
hiddenimports = collect_submodules('cv2')

# 追加の隠しインポート
hiddenimports += [
    'cv2',
    'cv2.cv2',
    'cv2.data',
    'cv2.config',
    'cv2.version',
    'numpy',
    'numpy.core._methods',
    'numpy.lib.format',
]

# OpenCVの動的ライブラリを明示的に追加
try:
    import cv2
    cv2_path = os.path.dirname(cv2.__file__)
    dylibs_path = os.path.join(cv2_path, '.dylibs')
    
    if os.path.exists(dylibs_path):
        for dylib_file in os.listdir(dylibs_path):
            if dylib_file.endswith('.dylib'):
                dylib_path = os.path.join(dylibs_path, dylib_file)
                binaries.append((dylib_path, 'cv2/.dylibs'))
    
    # 設定ファイルを明示的に追加
    config_files = ['config.py', 'config-3.py', 'version.py']
    for config_file in config_files:
        config_path = os.path.join(cv2_path, config_file)
        if os.path.exists(config_path):
            datas.append((config_path, 'cv2'))
    
    # データディレクトリを明示的に追加
    data_dir = os.path.join(cv2_path, 'data')
    if os.path.exists(data_dir):
        datas.append((data_dir, 'cv2/data'))
        
except ImportError:
    pass
