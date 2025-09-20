from PyInstaller.utils.hooks import collect_data_files

# qtawesome のフォントなどのデータを収集
datas = collect_data_files('qtawesome')
