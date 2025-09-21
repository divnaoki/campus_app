from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# pyttsx3 のデータファイルを収集
datas = collect_data_files('pyttsx3')

# pyttsx3 のサブモジュールを収集
hiddenimports = collect_submodules('pyttsx3')
