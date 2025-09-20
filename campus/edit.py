#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
キャンパス編集画面
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QMessageBox, QFrame, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta

from models import Campus


class CampusEditWidget(QWidget):
    """キャンパス編集画面ウィジェット"""
    
    # シグナル定義
    campus_updated = Signal()  # キャンパス更新完了
    campus_deleted = Signal()  # キャンパス削除完了
    back_to_index = Signal()  # 一覧画面に戻る
    
    def __init__(self, campus_id: int):
        super().__init__()
        self.campus_id = campus_id
        self.campus = None
        self.setup_ui()
        self.load_campus()
    
    def setup_ui(self):
        """UIをセットアップ"""
        # メインレイアウト
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # ヘッダー部分
        header_layout = QHBoxLayout()
        
        # 戻るボタン
        back_button = QPushButton()
        back_button.setIcon(qta.icon('mdi.arrow-left', color='#6B7280'))
        back_button.setText("戻る")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                color: #6B7280;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
                border-color: #9CA3AF;
            }
        """)
        back_button.clicked.connect(self.back_to_index.emit)
        
        # タイトル
        self.title_label = QLabel("キャンパス編集")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #1F2937;")
        
        header_layout.addWidget(back_button)
        header_layout.addStretch()
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        # フォーム部分
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 30px;
            }
        """)
        
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)
        
        # キャンパス名入力
        name_label = QLabel("キャンパス名 *")
        name_label.setStyleSheet("color: #374151; font-weight: bold; font-size: 14px;")
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("キャンパス名を入力してください")
        self.name_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                background-color: #FFFFFF;
                color: #1F2937;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
                outline: none;
            }
        """)
        self.name_input.returnPressed.connect(self.update_campus)
        
        # キャンパスタイプ選択
        type_label = QLabel("キャンパスタイプ *")
        type_label.setStyleSheet("color: #374151; font-weight: bold; font-size: 14px;")
        
        self.type_combo = QComboBox()
        self.type_combo.addItem("🖼 画像用", "image")
        self.type_combo.addItem("🎬 動画用", "video")
        self.type_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                background-color: #FFFFFF;
                color: #1F2937;
            }
            QComboBox:focus {
                border-color: #3B82F6;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #6B7280;
                margin-right: 5px;
            }
        """)
        
        # 作成日時表示
        self.created_at_label = QLabel()
        self.created_at_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        
        form_layout.addWidget(name_label)
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(type_label)
        form_layout.addWidget(self.type_combo)
        form_layout.addWidget(self.created_at_label)
        
        form_frame.setLayout(form_layout)
        
        # ボタン部分
        button_layout = QHBoxLayout()
        
        # 削除ボタン（左側）
        delete_button = QPushButton()
        delete_button.setIcon(qta.icon('mdi.delete', color='#FFFFFF'))
        delete_button.setText("削除")
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
            QPushButton:pressed {
                background-color: #B91C1C;
            }
        """)
        delete_button.clicked.connect(self.delete_campus)
        
        button_layout.addWidget(delete_button)
        button_layout.addStretch()
        
        # キャンセルボタン
        cancel_button = QPushButton("キャンセル")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
                border-color: #9CA3AF;
            }
        """)
        cancel_button.clicked.connect(self.back_to_index.emit)
        
        # 更新ボタン
        update_button = QPushButton()
        update_button.setIcon(qta.icon('mdi.check', color='#FFFFFF'))
        update_button.setText("更新")
        update_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        update_button.clicked.connect(self.update_campus)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(update_button)
        
        # レイアウトに追加
        main_layout.addLayout(header_layout)
        main_layout.addWidget(form_frame)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def load_campus(self):
        """キャンパス情報を読み込み"""
        try:
            self.campus = Campus.get_by_id(self.campus_id)
            if not self.campus:
                QMessageBox.critical(self, "エラー", "キャンパスが見つかりません。")
                self.back_to_index.emit()
                return
            
            # フォームにデータを設定
            self.name_input.setText(self.campus.name)
            self.title_label.setText(f"キャンパス編集 - {self.campus.name}")
            
            # タイプを設定
            if self.campus.type == "image":
                self.type_combo.setCurrentIndex(0)
            else:
                self.type_combo.setCurrentIndex(1)
            
            if self.campus.created_at:
                self.created_at_label.setText(f"作成日時: {self.campus.created_at}")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"キャンパス情報の読み込みに失敗しました:\n{str(e)}")
            self.back_to_index.emit()
    
    def update_campus(self):
        """キャンパスを更新"""
        if not self.campus:
            return
        
        name = self.name_input.text().strip()
        campus_type = self.type_combo.currentData()
        
        if not name:
            QMessageBox.warning(self, "入力エラー", "キャンパス名を入力してください。")
            self.name_input.setFocus()
            return
        
        if name == self.campus.name and campus_type == self.campus.type:
            QMessageBox.information(self, "情報", "変更がありません。")
            return
        
        try:
            self.campus.name = name
            self.campus.type = campus_type
            self.campus.save()
            
            type_text = "画像用" if campus_type == "image" else "動画用"
            QMessageBox.information(self, "更新完了", f"{type_text}キャンパス「{name}」を更新しました。")
            self.campus_updated.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"キャンパスの更新に失敗しました:\n{str(e)}")
    
    def delete_campus(self):
        """キャンパスを削除"""
        if not self.campus:
            return
        
        # 確認ダイアログ
        reply = QMessageBox.question(
            self, 
            "削除確認", 
            f"キャンパス「{self.campus.name}」を削除しますか？\n\nこの操作は取り消せません。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.campus.delete()
                QMessageBox.information(self, "削除完了", f"キャンパス「{self.campus.name}」を削除しました。")
                self.campus_deleted.emit()
                
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"キャンパスの削除に失敗しました:\n{str(e)}")
