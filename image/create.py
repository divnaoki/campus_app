#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画像アップロード画面
"""

import os
import shutil
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QFileDialog,
    QMessageBox, QFrame, QProgressBar, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QPixmap, QPainter, QPen
import qtawesome as qta

from models import Image, Campus


class ImageUploadThread(QThread):
    """画像アップロード用のスレッド"""
    
    progress_updated = Signal(int)
    upload_completed = Signal(bool, str)
    
    def __init__(self, image_data, campus_id):
        super().__init__()
        self.image_data = image_data
        self.campus_id = campus_id
    
    def run(self):
        """画像アップロード処理を実行"""
        try:
            # 進捗を更新
            self.progress_updated.emit(50)
            
            # ファイルを読み込み
            source_path = self.image_data['source_path']
            filename = self.image_data['filename']
            image_name = self.image_data['image_name']
            
            # ファイルをバイナリデータとして読み込み
            with open(source_path, 'rb') as f:
                file_data = f.read()
            
            # データベースに保存
            image = Image(
                campus_id=self.campus_id,
                name=image_name,  # ユーザーが入力した画像名を使用
                file_data=file_data,
                sort_order=0  # 0を設定すると自動的に適切な値が計算される
            )
            image.save()
            
            # 完了
            self.progress_updated.emit(100)
            self.upload_completed.emit(True, f"画像 '{image_name}' をアップロードしました。")
            
        except Exception as e:
            self.upload_completed.emit(False, f"アップロード中にエラーが発生しました:\n{str(e)}")


class ImagePreviewWidget(QFrame):
    """画像プレビューウィジェット"""
    
    remove_requested = Signal()  # 削除要求
    
    def __init__(self, image_data):
        super().__init__()
        self.image_data = image_data
        self.setup_ui()
    
    def setup_ui(self):
        """UIをセットアップ"""
        self.setFixedSize(200, 250)
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 画像プレビュー
        self.image_label = QLabel()
        self.image_label.setFixedSize(180, 150)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 4px;
            }
        """)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True)
        
        # 画像を読み込み
        self.load_image_preview()
        
        # ファイル名
        filename_label = QLabel(self.image_data['filename'])
        filename_label.setStyleSheet("""
            QLabel {
                color: #6B7280;
                font-size: 10px;
            }
        """)
        filename_label.setWordWrap(True)
        filename_label.setMaximumHeight(20)
        
        # 削除ボタン
        remove_btn = QPushButton("削除")
        remove_btn.setIcon(qta.icon('mdi.close', color='#EF4444'))
        remove_btn.setFixedSize(60, 25)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #FEF2F2;
                color: #EF4444;
                border: 1px solid #FECACA;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
            }
        """)
        remove_btn.clicked.connect(self.remove_requested.emit)
        
        # レイアウトに追加
        layout.addWidget(self.image_label)
        layout.addWidget(filename_label)
        layout.addWidget(remove_btn)
        
        self.setLayout(layout)
    
    def load_image_preview(self):
        """画像プレビューを読み込み"""
        try:
            source_path = self.image_data['source_path']
            pixmap = QPixmap(source_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.set_placeholder_image()
        except Exception as e:
            print(f"画像プレビュー読み込みエラー: {e}")
            self.set_placeholder_image()
    
    def set_placeholder_image(self):
        """プレースホルダー画像を設定"""
        pixmap = QPixmap(180, 150)
        pixmap.fill(Qt.lightGray)
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.gray, 2))
        painter.drawRect(10, 10, 160, 130)
        painter.drawText(90, 75, "Preview")
        painter.end()
        
        self.image_label.setPixmap(pixmap)


class ImageCreateWidget(QWidget):
    """画像アップロード画面ウィジェット"""
    
    # シグナル定義
    back_to_index_requested = Signal()  # 画像一覧に戻る要求
    image_created = Signal()  # 画像作成完了
    
    def __init__(self, campus_id: int):
        super().__init__()
        self.campus_id = campus_id
        self.campus = None
        self.image_data = None
        self.upload_thread = None
        self.setup_ui()
        self.load_campus_info()
        self.setup_upload_directory()
    
    def setup_ui(self):
        """UIをセットアップ"""
        # メインレイアウト
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # ヘッダー部分
        header_layout = QHBoxLayout()
        
        # 戻るボタン
        back_button = QPushButton()
        back_button.setIcon(qta.icon('mdi.arrow-left', color='#6B7280'))
        back_button.setText("画像一覧に戻る")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                color: #6B7280;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        back_button.clicked.connect(self.back_to_index_requested.emit)
        
        # タイトル
        self.title_label = QLabel("画像アップロード")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #1F2937;")
        
        header_layout.addWidget(back_button)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        # ファイル選択エリア
        file_selection_frame = QFrame()
        file_selection_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 2px dashed #D1D5DB;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        file_selection_layout = QVBoxLayout()
        file_selection_layout.setAlignment(Qt.AlignCenter)
        
        # ファイル選択ボタン
        select_file_btn = QPushButton()
        select_file_btn.setIcon(qta.icon('mdi.upload', color='#3B82F6'))
        select_file_btn.setText("画像ファイルを選択")
        select_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        select_file_btn.clicked.connect(self.select_file)
        
        # 説明テキスト
        info_label = QLabel("1つの画像ファイルを選択してください")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                color: #6B7280;
                font-size: 14px;
                margin-top: 10px;
            }
        """)
        
        file_selection_layout.addWidget(select_file_btn)
        file_selection_layout.addWidget(info_label)
        file_selection_frame.setLayout(file_selection_layout)
        
        # 画像名入力エリア
        image_name_frame = QFrame()
        image_name_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        image_name_layout = QVBoxLayout()
        image_name_layout.setSpacing(8)
        
        # 画像名ラベル
        image_name_label = QLabel("画像名")
        image_name_label.setStyleSheet("""
            QLabel {
                color: #1F2937;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        # 画像名入力フィールド
        self.image_name_input = QLineEdit()
        self.image_name_input.setPlaceholderText("画像名を入力してください")
        self.image_name_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #FFFFFF;
                color: #1F2937;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
                outline: none;
                background-color: #FFFFFF;
                color: #1F2937;
            }
            QLineEdit:hover {
                border-color: #9CA3AF;
                background-color: #FFFFFF;
                color: #1F2937;
            }
        """)
        
        image_name_layout.addWidget(image_name_label)
        image_name_layout.addWidget(self.image_name_input)
        image_name_frame.setLayout(image_name_layout)
        
        # プレビューエリア
        preview_frame = QFrame()
        preview_frame.setStyleSheet("""
            QFrame {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(10, 10, 10, 10)
        
        # プレビュータイトル
        preview_title = QLabel("選択された画像")
        preview_title.setStyleSheet("""
            QLabel {
                color: #1F2937;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        
        # プレビューコンテナ
        self.preview_container = QWidget()
        self.preview_layout = QHBoxLayout()
        self.preview_layout.setAlignment(Qt.AlignCenter)
        self.preview_container.setLayout(self.preview_layout)
        
        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(self.preview_container)
        preview_frame.setLayout(preview_layout)
        
        # 説明入力エリア（BLOB保存のため削除）
        
        # 進捗バー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #E5E7EB;
                border-radius: 4px;
                text-align: center;
                background-color: #F9FAFB;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 3px;
            }
        """)
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # アップロードボタン
        self.upload_button = QPushButton()
        self.upload_button.setIcon(qta.icon('mdi.upload', color='#FFFFFF'))
        self.upload_button.setText("アップロード開始")
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
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
        
        button_layout.addWidget(self.upload_button)
        
        # レイアウトに追加
        main_layout.addLayout(header_layout)
        main_layout.addWidget(file_selection_frame)
        main_layout.addWidget(image_name_frame)
        main_layout.addWidget(preview_frame)
        main_layout.addWidget(self.progress_bar)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def load_campus_info(self):
        """キャンパス情報を読み込み"""
        try:
            self.campus = Campus.get_by_id(self.campus_id)
            if self.campus:
                self.title_label.setText(f"画像アップロード - {self.campus.name}")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"キャンパス情報の読み込みに失敗しました:\n{str(e)}")
    
    def setup_upload_directory(self):
        """アップロードディレクトリをセットアップ（BLOB保存のため不要）"""
        pass
    
    def select_file(self):
        """ファイル選択ダイアログを表示"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("画像ファイル (*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp)")
        file_dialog.setViewMode(QFileDialog.Detail)
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                self.add_file(file_paths[0])
    
    def add_file(self, file_path):
        """ファイルを追加"""
        try:
            # ファイル情報を取得
            path_obj = Path(file_path)
            
            self.image_data = {
                'source_path': file_path,
                'filename': path_obj.name,
                'image_name': self.image_name_input.text().strip() or path_obj.stem
            }
            
            # 画像名が空の場合はファイル名（拡張子なし）をデフォルトに設定
            if not self.image_name_input.text().strip():
                self.image_name_input.setText(path_obj.stem)
            
            self.update_preview()
            self.upload_button.setEnabled(True)
            
        except Exception as e:
            QMessageBox.warning(self, "警告", f"ファイル '{file_path}' の読み込みに失敗しました:\n{str(e)}")
    
    def get_mime_type(self, extension):
        """拡張子からMIMEタイプを取得（BLOB保存のため不要）"""
        return 'image/jpeg'
    
    def update_preview(self):
        """プレビューを更新"""
        # 既存のプレビューを削除
        while self.preview_layout.count():
            child = self.preview_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 新しいプレビューを作成
        if self.image_data:
            preview_widget = ImagePreviewWidget(self.image_data)
            preview_widget.remove_requested.connect(self.remove_image)
            self.preview_layout.addWidget(preview_widget)
    
    def remove_image(self):
        """画像を削除"""
        self.image_data = None
        self.update_preview()
        self.upload_button.setEnabled(False)
    
    def start_upload(self):
        """アップロードを開始"""
        if not self.image_data:
            QMessageBox.warning(self, "警告", "アップロードする画像がありません。")
            return
        
        # 画像名の検証
        image_name = self.image_name_input.text().strip()
        if not image_name:
            QMessageBox.warning(self, "警告", "画像名を入力してください。")
            return
        
        # 画像データを更新（画像名を反映）
        self.image_data['image_name'] = image_name
        
        # 進捗バーを表示
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.upload_button.setEnabled(False)
        
        # アップロードスレッドを開始
        self.upload_thread = ImageUploadThread(
            self.image_data, 
            self.campus_id
        )
        self.upload_thread.progress_updated.connect(self.progress_bar.setValue)
        self.upload_thread.upload_completed.connect(self.on_upload_completed)
        self.upload_thread.start()
    
    def on_upload_completed(self, success, message):
        """アップロード完了時の処理"""
        self.progress_bar.setVisible(False)
        self.upload_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "アップロード完了", message)
            self.image_created.emit()
            self.back_to_index_requested.emit()
        else:
            QMessageBox.critical(self, "アップロードエラー", message)
    
    def refresh(self):
        """画面をリフレッシュ"""
        self.image_data = None
        self.image_name_input.clear()
        self.update_preview()
        self.upload_button.setEnabled(False)
