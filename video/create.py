#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
動画アップロード画面
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QFileDialog,
    QMessageBox, QProgressBar, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QPixmap
import qtawesome as qta
import os
from pathlib import Path

from models import Video, Campus
from video_utils import (
    get_video_directories, is_video_file, copy_video_file, 
    generate_thumbnail, get_video_info
)


class VideoUploadThread(QThread):
    """動画アップロード処理用スレッド"""
    
    progress_updated = Signal(int)
    status_updated = Signal(str)
    upload_completed = Signal(bool, str)
    
    def __init__(self, video_path: str, campus_id: int, sort_order: int = 0):
        super().__init__()
        self.video_path = video_path
        self.campus_id = campus_id
        self.sort_order = sort_order
    
    def run(self):
        """アップロード処理を実行"""
        try:
            self.status_updated.emit("動画ファイルをコピー中...")
            self.progress_updated.emit(20)
            
            # 動画ファイルをコピー
            copied_path = copy_video_file(self.video_path, self.campus_id)
            if not copied_path:
                self.upload_completed.emit(False, "動画ファイルのコピーに失敗しました")
                return
            
            self.status_updated.emit("サムネイルを生成中...")
            self.progress_updated.emit(50)
            
            # サムネイルを生成
            video_dir, thumbnail_dir = get_video_directories()
            video_filename = Path(copied_path).name
            thumbnail_filename = f"thumb_{Path(video_filename).stem}.jpg"
            thumbnail_path = thumbnail_dir / thumbnail_filename
            
            if not generate_thumbnail(copied_path, str(thumbnail_path)):
                self.upload_completed.emit(False, "サムネイルの生成に失敗しました")
                return
            
            self.status_updated.emit("データベースに保存中...")
            self.progress_updated.emit(80)
            
            # データベースに保存
            video = Video(
                campus_id=self.campus_id,
                file_path=copied_path,
                thumbnail_path=str(thumbnail_path),
                sort_order=self.sort_order
            )
            video.save()
            
            self.progress_updated.emit(100)
            self.status_updated.emit("アップロード完了")
            self.upload_completed.emit(True, "動画のアップロードが完了しました")
            
        except Exception as e:
            self.upload_completed.emit(False, f"アップロード中にエラーが発生しました: {e}")


class VideoCreateWidget(QWidget):
    """動画アップロードウィジェット"""
    
    # シグナル定義
    video_created = Signal(int)  # video_id
    back_to_index_requested = Signal()
    
    def __init__(self, campus_id: int):
        super().__init__()
        self.campus_id = campus_id
        self.campus = Campus.get_by_id(campus_id)
        self.upload_thread = None
        self.setup_ui()
    
    def setup_ui(self):
        """UIをセットアップ"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # ヘッダー部分
        header_layout = QHBoxLayout()
        
        # タイトル
        title_text = f"動画アップロード - {self.campus.name if self.campus else 'Unknown'}"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1F2937;
            }
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # 戻るボタン
        back_button = QPushButton()
        back_button.setIcon(qta.icon('fa5s.arrow-left', color='#6B7280'))
        back_button.setText("一覧に戻る")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                color: #6B7280;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        back_button.clicked.connect(self.back_to_index_requested.emit)
        
        header_layout.addWidget(back_button)
        
        # メインコンテンツ
        content_group = QGroupBox("動画ファイルの選択")
        content_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        content_layout = QVBoxLayout()
        content_layout.setSpacing(15)
        
        # ファイル選択エリア
        file_layout = QHBoxLayout()
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("動画ファイルを選択してください")
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #E5E7EB;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
            }
        """)
        
        select_button = QPushButton()
        select_button.setIcon(qta.icon('fa5s.folder-open', color='white'))
        select_button.setText("ファイルを選択")
        select_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        select_button.clicked.connect(self.select_video_file)
        
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(select_button)
        
        # 動画情報表示エリア
        self.info_group = QGroupBox("動画情報")
        self.info_group.setVisible(False)
        self.info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        info_layout = QFormLayout()
        info_layout.setSpacing(10)
        
        self.duration_label = QLabel("-")
        self.resolution_label = QLabel("-")
        self.fps_label = QLabel("-")
        self.file_size_label = QLabel("-")
        
        info_layout.addRow("再生時間:", self.duration_label)
        info_layout.addRow("解像度:", self.resolution_label)
        info_layout.addRow("フレームレート:", self.fps_label)
        info_layout.addRow("ファイルサイズ:", self.file_size_label)
        
        self.info_group.setLayout(info_layout)
        
        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #E5E7EB;
                border-radius: 6px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 4px;
            }
        """)
        
        # ステータスラベル
        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #6B7280;
                font-size: 14px;
            }
        """)
        
        # アップロードボタン
        self.upload_button = QPushButton()
        self.upload_button.setIcon(qta.icon('fa5s.upload', color='white'))
        self.upload_button.setText("アップロード開始")
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 15px 30px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #9CA3AF;
            }
        """)
        self.upload_button.clicked.connect(self.start_upload)
        self.upload_button.setEnabled(False)
        
        # レイアウトに追加
        content_layout.addLayout(file_layout)
        content_layout.addWidget(self.info_group)
        content_layout.addWidget(self.progress_bar)
        content_layout.addWidget(self.status_label)
        content_layout.addWidget(self.upload_button)
        
        content_group.setLayout(content_layout)
        
        layout.addLayout(header_layout)
        layout.addWidget(content_group)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def select_video_file(self):
        """動画ファイルを選択"""
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("動画ファイル (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if is_video_file(file_path):
                self.file_path_edit.setText(file_path)
                self.load_video_info(file_path)
                self.upload_button.setEnabled(True)
            else:
                QMessageBox.warning(self, "エラー", "選択されたファイルは動画ファイルではありません。")
    
    def load_video_info(self, file_path: str):
        """動画情報を読み込み"""
        try:
            # 動画情報を取得
            info = get_video_info(file_path)
            if info:
                # 再生時間をフォーマット
                duration = info['duration']
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                duration_text = f"{minutes:02d}:{seconds:02d}"
                
                # 解像度
                resolution_text = f"{info['width']} x {info['height']}"
                
                # フレームレート
                fps_text = f"{info['fps']:.1f} fps"
                
                # ファイルサイズ
                file_size = os.path.getsize(file_path)
                if file_size < 1024 * 1024:
                    size_text = f"{file_size / 1024:.1f} KB"
                elif file_size < 1024 * 1024 * 1024:
                    size_text = f"{file_size / (1024 * 1024):.1f} MB"
                else:
                    size_text = f"{file_size / (1024 * 1024 * 1024):.1f} GB"
                
                # ラベルを更新
                self.duration_label.setText(duration_text)
                self.resolution_label.setText(resolution_text)
                self.fps_label.setText(fps_text)
                self.file_size_label.setText(size_text)
                
                self.info_group.setVisible(True)
            else:
                QMessageBox.warning(self, "エラー", "動画ファイルの情報を取得できませんでした。")
                
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"動画情報の読み込み中にエラーが発生しました: {e}")
    
    def start_upload(self):
        """アップロードを開始"""
        if not self.file_path_edit.text():
            QMessageBox.warning(self, "エラー", "動画ファイルを選択してください。")
            return
        
        # UIを無効化
        self.upload_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.progress_bar.setValue(0)
        
        # アップロードスレッドを開始
        self.upload_thread = VideoUploadThread(
            self.file_path_edit.text(),
            self.campus_id
        )
        self.upload_thread.progress_updated.connect(self.progress_bar.setValue)
        self.upload_thread.status_updated.connect(self.status_label.setText)
        self.upload_thread.upload_completed.connect(self.on_upload_completed)
        self.upload_thread.start()
    
    def on_upload_completed(self, success: bool, message: str):
        """アップロード完了時の処理"""
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.upload_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "成功", message)
            self.video_created.emit(0)  # 一覧に戻る
        else:
            QMessageBox.warning(self, "エラー", message)
