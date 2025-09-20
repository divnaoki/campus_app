#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
キャンパス新規作成画面
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QMessageBox, QFrame, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta

from models import Campus


class CampusCreateWidget(QWidget):
    """キャンパス新規作成画面ウィジェット"""
    
    # シグナル定義
    campus_created = Signal()  # キャンパス作成完了
    back_to_index = Signal()  # 一覧画面に戻る
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
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
        title_label = QLabel("キャンパス新規作成")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1F2937;")
        
        header_layout.addWidget(back_button)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
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
        self.name_input.returnPressed.connect(self.create_campus)
        
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
        
        # 説明ラベル
        description_label = QLabel("キャンパスは画像や動画を管理するためのコンテナです。")
        description_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        
        form_layout.addWidget(name_label)
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(type_label)
        form_layout.addWidget(self.type_combo)
        form_layout.addWidget(description_label)
        
        form_frame.setLayout(form_layout)
        
        # ボタン部分
        button_layout = QHBoxLayout()
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
        
        # 作成ボタン
        create_button = QPushButton()
        create_button.setIcon(qta.icon('mdi.check', color='#FFFFFF'))
        create_button.setText("作成")
        create_button.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        create_button.clicked.connect(self.create_campus)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(create_button)
        
        # レイアウトに追加
        main_layout.addLayout(header_layout)
        main_layout.addWidget(form_frame)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def create_campus(self):
        """キャンパスを作成"""
        name = self.name_input.text().strip()
        campus_type = self.type_combo.currentData()
        
        if not name:
            QMessageBox.warning(self, "入力エラー", "キャンパス名を入力してください。")
            self.name_input.setFocus()
            return
        
        try:
            campus = Campus(name=name, type=campus_type)
            campus.save()
            
            type_text = "画像用" if campus_type == "image" else "動画用"
            QMessageBox.information(self, "作成完了", f"{type_text}キャンパス「{name}」を作成しました。")
            self.name_input.clear()
            self.campus_created.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"キャンパスの作成に失敗しました:\n{str(e)}")
    
    def clear_form(self):
        """フォームをクリア"""
        self.name_input.clear()
        self.type_combo.setCurrentIndex(0)  # デフォルトで画像用を選択
