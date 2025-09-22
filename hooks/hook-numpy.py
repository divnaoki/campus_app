# -*- coding: utf-8 -*-
"""
NumPy用のPyInstallerフック
"""

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# NumPyのデータファイルを収集
datas = collect_data_files('numpy')

# NumPyの動的ライブラリを収集
binaries = collect_dynamic_libs('numpy')

# 隠しインポートを追加
hiddenimports = [
    'numpy',
    'numpy.core._methods',
    'numpy.lib.format',
    'numpy.random',
    'numpy.random._common',
    'numpy.random._bounded_integers',
    'numpy.random._mt19937',
    'numpy.random._pcg64',
    'numpy.random._philox',
    'numpy.random._sfc64',
]
