#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
キャンパス一覧画面
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta

from models import Campus


class CampusIndexWidget(QWidget):
    """キャンパス一覧画面ウィジェット"""
    
    # シグナル定義
    create_campus_requested = Signal()  # キャンパス作成画面への遷移要求
    edit_campus_requested = Signal(int)  # キャンパス編集画面への遷移要求（campus_id）
    image_index_requested = Signal(int)  # 画像一覧画面への遷移要求（campus_id）
    
    def __init__(self):
        super().__init__()
        self.campuses = []
        self.setup_ui()
        self.load_campuses()
    
    def setup_ui(self):
        """UIをセットアップ"""
        # メインレイアウト
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # ヘッダー部分
        header_layout = QHBoxLayout()
        
        # タイトル
        title_label = QLabel("キャンパス一覧")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1F2937;")
        
        # 新規作成ボタン
        create_button = QPushButton()
        create_button.setIcon(qta.icon('mdi.plus-circle', color='#FFFFFF'))
        create_button.setText("新規作成")
        create_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        create_button.clicked.connect(self.create_campus_requested.emit)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(create_button)
        
        # キャンパス一覧エリア
        self.campus_list = QListWidget()
        self.campus_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: #FFFFFF;
                padding: 10px;
                color: #1F2937;
            }
            QListWidget::item {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 15px;
                margin: 5px;
                background-color: #F9FAFB;
                color: #1F2937;
            }
            QListWidget::item:hover {
                background-color: #F3F4F6;
                border-color: #D1D5DB;
                color: #1F2937;
            }
            QListWidget::item:selected {
                background-color: #EBF8FF;
                border-color: #3B82F6;
                color: #1F2937;
            }
            QListWidget::item:disabled {
                color: #6B7280;
                font-style: italic;
                background-color: #F9FAFB;
                border: none;
            }
        """)
        self.campus_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # レイアウトに追加
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.campus_list)
        
        self.setLayout(main_layout)
    
    def load_campuses(self):
        """キャンパス一覧を読み込み"""
        try:
            self.campuses = Campus.get_all()
            self.update_campus_list()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"キャンパスの読み込みに失敗しました:\n{str(e)}")
    
    def update_campus_list(self):
        """キャンパス一覧を更新"""
        self.campus_list.clear()
        
        if not self.campuses:
            # キャンパスが存在しない場合のメッセージ
            item = QListWidgetItem("キャンパスが登録されていません")
            item.setFlags(Qt.NoItemFlags)  # 選択不可
            item.setTextAlignment(Qt.AlignCenter)
            # QListWidgetItemにはsetStyleSheetがないため、QListWidgetのスタイルで制御
            self.campus_list.addItem(item)
            return
        
        for campus in self.campuses:
            item = QListWidgetItem()
            # タイプに応じてアイコンを変更
            if campus.type == "image":
                icon = "🖼"
                type_text = "画像用"
            else:
                icon = "🎬"
                type_text = "動画用"
            
            item.setText(f"{icon} {campus.name} ({type_text})")
            item.setData(Qt.UserRole, campus.id)  # IDを保存
            self.campus_list.addItem(item)
    
    def on_item_double_clicked(self, item):
        """アイテムがダブルクリックされた時の処理"""
        campus_id = item.data(Qt.UserRole)
        if campus_id:
            # キャンパスのタイプを確認
            campus = next((c for c in self.campuses if c.id == campus_id), None)
            if campus:
                if campus.type == "image":
                    self.image_index_requested.emit(campus_id)
                else:
                    self.edit_campus_requested.emit(campus_id)
    
    def refresh(self):
        """画面をリフレッシュ"""
        self.load_campuses()
