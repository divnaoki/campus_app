#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画像編集画面
"""

import os
import shutil
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QFileDialog,
    QMessageBox, QFrame, QSpinBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter, QPen
import qtawesome as qta

from models import Image, Campus


class ImageEditWidget(QWidget):
    """画像編集画面ウィジェット"""
    
    # シグナル定義
    back_to_index_requested = Signal()  # 画像一覧に戻る要求
    image_updated = Signal()  # 画像更新完了
    image_deleted = Signal()  # 画像削除完了
    
    def __init__(self, image_id: int):
        super().__init__()
        self.image_id = image_id
        self.image = None
        self.campus = None
        self.original_file_path = None
        self.setup_ui()
        self.load_image_info()
    
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
        self.title_label = QLabel("画像編集")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #1F2937;")
        
        # 削除ボタン
        delete_button = QPushButton()
        delete_button.setIcon(qta.icon('mdi.delete', color='#EF4444'))
        delete_button.setText("画像を削除")
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #FEF2F2;
                color: #EF4444;
                border: 1px solid #FECACA;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
            }
        """)
        delete_button.clicked.connect(self.delete_image)
        
        header_layout.addWidget(back_button)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(delete_button)
        
        # メインコンテンツエリア
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # 左側：画像プレビューエリア
        preview_frame = QFrame()
        preview_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        preview_frame.setFixedWidth(400)
        
        preview_layout = QVBoxLayout()
        
        # プレビュータイトル
        preview_title = QLabel("画像プレビュー")
        preview_title.setStyleSheet("""
            QLabel {
                color: #1F2937;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        
        # 画像プレビュー
        self.image_preview = QLabel()
        self.image_preview.setFixedSize(350, 300)
        self.image_preview.setStyleSheet("""
            QLabel {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 4px;
            }
        """)
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setScaledContents(True)
        
        # ファイル情報
        self.file_info_label = QLabel()
        self.file_info_label.setStyleSheet("""
            QLabel {
                color: #6B7280;
                font-size: 12px;
                margin-top: 10px;
            }
        """)
        self.file_info_label.setWordWrap(True)
        
        # ファイル変更ボタン
        change_file_btn = QPushButton()
        change_file_btn.setIcon(qta.icon('mdi.file-image', color='#3B82F6'))
        change_file_btn.setText("ファイルを変更")
        change_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        change_file_btn.clicked.connect(self.change_image_file)
        
        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(self.image_preview)
        preview_layout.addWidget(self.file_info_label)
        preview_layout.addWidget(change_file_btn)
        preview_layout.addStretch()
        
        preview_frame.setLayout(preview_layout)
        
        # 右側：編集フォームエリア
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        
        # フォームタイトル
        form_title = QLabel("画像情報編集")
        form_title.setStyleSheet("""
            QLabel {
                color: #1F2937;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        
        # ファイル名
        filename_layout = QHBoxLayout()
        filename_label = QLabel("ファイル名:")
        filename_label.setFixedWidth(100)
        filename_label.setStyleSheet("color: #374151; font-weight: bold;")
        
        self.filename_input = QLineEdit()
        self.filename_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
            }
        """)
        
        filename_layout.addWidget(filename_label)
        filename_layout.addWidget(self.filename_input)
        
        # 並び順
        sort_layout = QHBoxLayout()
        sort_label = QLabel("並び順:")
        sort_label.setFixedWidth(100)
        sort_label.setStyleSheet("color: #374151; font-weight: bold;")
        
        self.sort_input = QSpinBox()
        self.sort_input.setRange(0, 9999)
        self.sort_input.setStyleSheet("""
            QSpinBox {
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QSpinBox:focus {
                border-color: #3B82F6;
            }
        """)
        
        sort_layout.addWidget(sort_label)
        sort_layout.addWidget(self.sort_input)
        sort_layout.addStretch()
        
        # 説明（削除 - 設計書にない）
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 保存ボタン
        save_button = QPushButton()
        save_button.setIcon(qta.icon('mdi.content-save', color='#FFFFFF'))
        save_button.setText("変更を保存")
        save_button.setStyleSheet("""
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
        """)
        save_button.clicked.connect(self.save_changes)
        
        button_layout.addWidget(save_button)
        
        # フォームレイアウトに追加
        form_layout.addWidget(form_title)
        form_layout.addLayout(filename_layout)
        form_layout.addLayout(sort_layout)
        form_layout.addStretch()
        form_layout.addLayout(button_layout)
        
        form_frame.setLayout(form_layout)
        
        # コンテンツレイアウトに追加
        content_layout.addWidget(preview_frame)
        content_layout.addWidget(form_frame)
        
        # メインレイアウトに追加
        main_layout.addLayout(header_layout)
        main_layout.addLayout(content_layout)
        
        self.setLayout(main_layout)
    
    def load_image_info(self):
        """画像情報を読み込み"""
        try:
            self.image = Image.get_by_id(self.image_id)
            if not self.image:
                QMessageBox.critical(self, "エラー", "画像が見つかりません。")
                self.back_to_index_requested.emit()
                return
            
            # キャンパス情報を取得
            self.campus = Campus.get_by_id(self.image.campus_id)
            if self.campus:
                self.title_label.setText(f"画像編集 - {self.campus.name}")
            
            # フォームに値を設定
            self.filename_input.setText(self.image.name)
            self.sort_input.setValue(self.image.sort_order)
            
            # 画像プレビューを読み込み
            self.load_image_preview()
            
            # 元のファイルパスを保存（BLOB保存のため不要）
            self.original_file_path = None
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"画像情報の読み込みに失敗しました:\n{str(e)}")
    
    def load_image_preview(self):
        """画像プレビューを読み込み"""
        try:
            if self.image.file_data and len(self.image.file_data) > 0:
                pixmap = QPixmap()
                if pixmap.loadFromData(self.image.file_data):
                    # アスペクト比を保ってリサイズ
                    scaled_pixmap = pixmap.scaled(
                        self.image_preview.size(), 
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    self.image_preview.setPixmap(scaled_pixmap)
                    
                    # ファイル情報を更新
                    self.update_file_info()
                else:
                    self.set_placeholder_image()
            else:
                self.set_placeholder_image()
        except Exception as e:
            print(f"画像プレビュー読み込みエラー: {e}")
            self.set_placeholder_image()
    
    def set_placeholder_image(self):
        """プレースホルダー画像を設定"""
        pixmap = QPixmap(350, 300)
        pixmap.fill(Qt.lightGray)
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.gray, 2))
        painter.drawRect(10, 10, 330, 280)
        painter.drawText(175, 150, "No Image")
        painter.end()
        
        self.image_preview.setPixmap(pixmap)
        self.file_info_label.setText("画像ファイルが見つかりません")
    
    def update_file_info(self):
        """ファイル情報を更新"""
        if self.image:
            info_text = f"ファイル: {self.image.name}\n"
            info_text += f"並び順: {self.image.sort_order}\n"
            info_text += f"データサイズ: {len(self.image.file_data)} bytes"
            self.file_info_label.setText(info_text)
    
    def change_image_file(self):
        """画像ファイルを変更"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("画像ファイル (*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp)")
        file_dialog.setViewMode(QFileDialog.Detail)
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.replace_image_file(file_path)
    
    def replace_image_file(self, new_file_path):
        """画像ファイルを置き換え"""
        try:
            # 新しいファイルの情報を取得
            new_path_obj = Path(new_file_path)
            new_pixmap = QPixmap(new_file_path)
            
            if new_pixmap.isNull():
                QMessageBox.warning(self, "警告", "選択されたファイルは有効な画像ではありません。")
                return
            
            # ファイルをバイナリデータとして読み込み
            with open(new_file_path, 'rb') as f:
                file_data = f.read()
            
            # 画像情報を更新
            self.image.name = new_path_obj.name
            self.image.file_data = file_data
            
            # フォームを更新
            self.filename_input.setText(self.image.name)
            
            # プレビューを更新
            self.load_image_preview()
            
            QMessageBox.information(self, "完了", "画像ファイルが変更されました。")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイルの変更に失敗しました:\n{str(e)}")
    
    def get_mime_type(self, extension):
        """拡張子からMIMEタイプを取得"""
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.webp': 'image/webp'
        }
        return mime_types.get(extension, 'image/jpeg')
    
    def save_changes(self):
        """変更を保存"""
        try:
            # フォームの値を取得
            new_filename = self.filename_input.text().strip()
            new_sort_order = self.sort_input.value()
            
            if not new_filename:
                QMessageBox.warning(self, "警告", "ファイル名を入力してください。")
                return
            
            # 画像情報を更新
            self.image.name = new_filename
            self.image.sort_order = new_sort_order
            
            # データベースに保存
            self.image.save()
            
            QMessageBox.information(self, "完了", "画像情報が更新されました。")
            self.image_updated.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"保存中にエラーが発生しました:\n{str(e)}")
    
    def delete_image(self):
        """画像を削除"""
        reply = QMessageBox.question(
            self, 
            "画像削除確認", 
            "この画像を削除しますか？\nこの操作は取り消せません。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # データベースから削除
                if self.image.delete():
                    QMessageBox.information(self, "削除完了", "画像を削除しました。")
                    self.image_deleted.emit()
                else:
                    QMessageBox.critical(self, "エラー", "画像の削除に失敗しました。")
                    
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"画像の削除中にエラーが発生しました:\n{str(e)}")
    
    def refresh(self):
        """画面をリフレッシュ"""
        self.load_image_info()
