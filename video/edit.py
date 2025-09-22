#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
動画編集画面
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QSpinBox, QMessageBox,
    QGroupBox, QFormLayout, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
import qtawesome as qta
import os
from pathlib import Path

from models import Video, Campus
from video_utils import (
    get_video_directories, is_video_file, copy_video_file, 
    generate_thumbnail, get_video_info
)


class VideoEditWidget(QWidget):
    """動画編集ウィジェット"""
    
    # シグナル定義
    video_updated = Signal(int)  # video_id
    video_deleted = Signal()
    back_to_index_requested = Signal()
    
    def __init__(self, video_id: int):
        super().__init__()
        self.video_id = video_id
        self.video = Video.get_by_id(video_id)
        self.campus = Campus.get_by_id(self.video.campus_id) if self.video else None
        self.setup_ui()
        self.load_video_data()
    
    def setup_ui(self):
        """UIをセットアップ"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # ヘッダー部分
        header_layout = QHBoxLayout()
        
        # タイトル
        title_text = f"動画編集 - {self.campus.name if self.campus else 'Unknown'}"
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
        content_group = QGroupBox("動画情報の編集")
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
        content_layout.setSpacing(20)
        
        # 現在の動画情報
        current_info_group = QGroupBox("現在の動画情報")
        current_info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        current_info_layout = QFormLayout()
        current_info_layout.setSpacing(10)
        
        self.current_file_label = QLabel("-")
        self.current_thumbnail_label = QLabel("-")
        self.current_sort_order_label = QLabel("-")
        
        current_info_layout.addRow("ファイルパス:", self.current_file_label)
        current_info_layout.addRow("サムネイルパス:", self.current_thumbnail_label)
        current_info_layout.addRow("並び順:", self.current_sort_order_label)
        
        current_info_group.setLayout(current_info_layout)
        
        # 編集フォーム
        edit_form_group = QGroupBox("編集項目")
        edit_form_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        edit_form_layout = QFormLayout()
        edit_form_layout.setSpacing(15)
        
        # ファイル変更
        file_layout = QHBoxLayout()
        
        self.new_file_edit = QLineEdit()
        self.new_file_edit.setPlaceholderText("新しい動画ファイルを選択してください")
        self.new_file_edit.setReadOnly(True)
        self.new_file_edit.setStyleSheet("""
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
        
        select_file_button = QPushButton()
        select_file_button.setIcon(qta.icon('fa5s.folder-open', color='white'))
        select_file_button.setText("ファイルを選択")
        select_file_button.setStyleSheet("""
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
        select_file_button.clicked.connect(self.select_new_video_file)
        
        file_layout.addWidget(self.new_file_edit)
        file_layout.addWidget(select_file_button)
        
        # 並び順
        self.sort_order_spinbox = QSpinBox()
        self.sort_order_spinbox.setMinimum(0)
        self.sort_order_spinbox.setMaximum(999)
        self.sort_order_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 10px;
                border: 2px solid #E5E7EB;
                border-radius: 6px;
                font-size: 14px;
            }
            QSpinBox:focus {
                border-color: #3B82F6;
            }
        """)
        
        edit_form_layout.addRow("新しい動画ファイル:", file_layout)
        edit_form_layout.addRow("並び順:", self.sort_order_spinbox)
        
        edit_form_group.setLayout(edit_form_layout)
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # 更新ボタン
        update_button = QPushButton()
        update_button.setIcon(qta.icon('fa5s.save', color='white'))
        update_button.setText("更新")
        update_button.setStyleSheet("""
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
        """)
        update_button.clicked.connect(self.update_video)
        
        # 削除ボタン
        delete_button = QPushButton()
        delete_button.setIcon(qta.icon('fa5s.trash', color='white'))
        delete_button.setText("削除")
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 15px 30px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        delete_button.clicked.connect(self.delete_video)
        
        button_layout.addStretch()
        button_layout.addWidget(update_button)
        button_layout.addWidget(delete_button)
        
        # レイアウトに追加
        content_layout.addWidget(current_info_group)
        content_layout.addWidget(edit_form_group)
        content_layout.addLayout(button_layout)
        
        content_group.setLayout(content_layout)
        
        layout.addLayout(header_layout)
        layout.addWidget(content_group)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def load_video_data(self):
        """動画データを読み込み"""
        if not self.video:
            return
        
        # 現在の情報を表示
        self.current_file_label.setText(self.video.file_path or "-")
        self.current_thumbnail_label.setText(self.video.thumbnail_path or "-")
        self.current_sort_order_label.setText(str(self.video.sort_order))
        
        # 並び順の初期値を設定
        self.sort_order_spinbox.setValue(self.video.sort_order)
    
    def select_new_video_file(self):
        """新しい動画ファイルを選択"""
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("動画ファイル (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if is_video_file(file_path):
                self.new_file_edit.setText(file_path)
            else:
                QMessageBox.warning(self, "エラー", "選択されたファイルは動画ファイルではありません。")
    
    def update_video(self):
        """動画情報を更新"""
        try:
            # 新しいファイルが選択されている場合
            if self.new_file_edit.text():
                new_file_path = self.new_file_edit.text()
                
                # ファイルをコピー
                copied_path = copy_video_file(new_file_path, self.video.campus_id)
                if not copied_path:
                    QMessageBox.warning(self, "エラー", "動画ファイルのコピーに失敗しました。")
                    return
                
                # サムネイルを生成
                video_dir, thumbnail_dir = get_video_directories()
                video_filename = Path(copied_path).name
                thumbnail_filename = f"thumb_{Path(video_filename).stem}.jpg"
                thumbnail_path = thumbnail_dir / thumbnail_filename
                
                if not generate_thumbnail(copied_path, str(thumbnail_path)):
                    QMessageBox.warning(self, "エラー", "サムネイルの生成に失敗しました。")
                    return
                
                # 古いファイルを削除（オプション）
                if self.video.file_path and os.path.exists(self.video.file_path):
                    try:
                        os.remove(self.video.file_path)
                    except:
                        pass  # 削除に失敗しても続行
                
                if self.video.thumbnail_path and os.path.exists(self.video.thumbnail_path):
                    try:
                        os.remove(self.video.thumbnail_path)
                    except:
                        pass  # 削除に失敗しても続行
                
                # パスを更新
                self.video.file_path = copied_path
                self.video.thumbnail_path = str(thumbnail_path)
            
            # 並び順を更新
            self.video.sort_order = self.sort_order_spinbox.value()
            
            # データベースに保存
            self.video.save()
            
            QMessageBox.information(self, "成功", "動画情報が更新されました。")
            self.video_updated.emit(self.video.id)
            
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"動画の更新中にエラーが発生しました: {e}")
    
    def delete_video(self):
        """動画を削除"""
        reply = QMessageBox.question(
            self, 
            "確認", 
            "この動画を削除しますか？\nこの操作は元に戻せません。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # ファイルを削除
                if self.video.file_path and os.path.exists(self.video.file_path):
                    os.remove(self.video.file_path)
                
                if self.video.thumbnail_path and os.path.exists(self.video.thumbnail_path):
                    os.remove(self.video.thumbnail_path)
                
                # データベースから削除
                self.video.delete()
                
                QMessageBox.information(self, "成功", "動画が削除されました。")
                self.video_deleted.emit()
                
            except Exception as e:
                QMessageBox.warning(self, "エラー", f"動画の削除中にエラーが発生しました: {e}")
    
    def go_back(self):
        """一覧に戻る"""
        self.back_to_index_requested.emit()
