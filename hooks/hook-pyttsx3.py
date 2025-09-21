from PyInstaller.utils.hooks import collect_data_files

# pyttsx3 のTextToSpeechThread.pyのデータを収集
datas = collect_data_files('pyttsx3')
