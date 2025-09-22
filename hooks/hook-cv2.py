# -*- coding: utf-8 -*-
"""
OpenCV-Python用のPyInstallerフック
"""

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# OpenCVのデータファイルを収集
datas = collect_data_files('cv2')

# OpenCVの動的ライブラリを収集
binaries = collect_dynamic_libs('cv2')

# 隠しインポートを追加
hiddenimports = [
    'cv2',
    'cv2.cv2',
    'cv2.data',
    'numpy',
    'numpy.core._methods',
    'numpy.lib.format',
]
