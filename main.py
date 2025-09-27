#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6アプリケーションのメインファイル
"""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, 
    QVBoxLayout, QLabel, QFrame, QStackedWidget, QToolButton,
    QMenuBar, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QAction
import qtawesome as qta

# データベース作成スクリプトをインポート
from database_setup import create_database, get_database_info

# キャンパス関連のインポート
from campus.index import CampusIndexWidget
from campus.create import CampusCreateWidget
from campus.edit import CampusEditWidget

# 画像関連のインポート
from image.index import ImageIndexWidget
from image.create import ImageCreateWidget
from image.edit import ImageEditWidget
from image.detail import ImageDetailWidget

# 動画関連のインポート
from video.index import VideoIndexWidget
from video.create import VideoCreateWidget
from video.edit import VideoEditWidget
from video.detail import VideoDetailWidget


class Sidebar(QFrame):
    """左側のメニューバー"""
    
    # シグナル定義
    campus_index_requested = Signal()
    campus_create_requested = Signal()
    image_index_requested = Signal(int)  # 画像一覧画面への遷移要求（campus_id）
    video_index_requested = Signal(int)  # 動画一覧画面への遷移要求（campus_id）
    image_create_requested = Signal()  # 画像アップロード要求
    image_position_edit_requested = Signal()  # 画像位置修正要求
    image_manage_mode_requested = Signal()  # 画像編集モード要求
    video_create_requested = Signal()  # 動画アップロード要求
    video_manage_mode_requested = Signal()  # 動画編集モード要求
    
    def __init__(self):
        super().__init__()
        self.current_page = None
        self.setup_ui()
    
    def setup_ui(self):
        # サイドバーのスタイル設定
        self.setFixedWidth(240)  # 幅を少し小さくして間隔を確保
        self.setStyleSheet("""
            QFrame {
                background-color: #1F2937;
                color: #FFFFFF;
                border: none;
            }
        """)
        
        # レイアウト設定
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 40, 20)  # 右マージンをさらに大きくしてメインコンテンツとの間隔を確保
        layout.setSpacing(10)
        
        # メニュータイトル
        title_label = QLabel("Menu")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #FFFFFF; margin-bottom: 20px;")
        
        layout.addWidget(title_label)
        
        # メニューボタンエリア
        self.menu_layout = QVBoxLayout()
        self.menu_layout.setSpacing(12)  # ボタン間のスペーシングを少し大きく
        
        layout.addLayout(self.menu_layout)
        layout.addStretch()  # 残りのスペースを埋める
        
        self.setLayout(layout)
    
    def set_campus_index_menu(self):
        """キャンパス一覧画面用のメニューを設定"""
        self.clear_menu()
        
        # キャンパス一覧ボタン（無効化）
        campus_list_btn = QToolButton()
        campus_list_btn.setIcon(qta.icon('mdi.school', color='#9CA3AF'))
        campus_list_btn.setText("キャンパス一覧")
        campus_list_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        campus_list_btn.setEnabled(False)
        campus_list_btn.setStyleSheet("""
            QToolButton {
                background-color: #374151;
                color: #9CA3AF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
            }
        """)
        
        # キャンパス作成ボタン
        campus_create_btn = QToolButton()
        campus_create_btn.setIcon(qta.icon('mdi.plus-circle', color='#FFFFFF'))
        campus_create_btn.setText("キャンパス作成")
        campus_create_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        campus_create_btn.setStyleSheet("""
            QToolButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #2563EB;
            }
            QToolButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        campus_create_btn.clicked.connect(self.campus_create_requested.emit)
        
        self.menu_layout.addWidget(campus_list_btn)
        self.menu_layout.addWidget(campus_create_btn)
        self.current_page = "campus_index"
    
    def set_campus_create_menu(self):
        """キャンパス作成画面用のメニューを設定"""
        self.clear_menu()
        
        # キャンパス一覧に戻るボタン
        back_btn = QToolButton()
        back_btn.setIcon(qta.icon('mdi.arrow-left', color='#FFFFFF'))
        back_btn.setText("キャンパス一覧に戻る")
        back_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        back_btn.setStyleSheet("""
            QToolButton {
                background-color: #6B7280;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #4B5563;
            }
        """)
        back_btn.clicked.connect(self.campus_index_requested.emit)
        
        self.menu_layout.addWidget(back_btn)
        self.current_page = "campus_create"
    
    def set_campus_edit_menu(self):
        """キャンパス編集画面用のメニューを設定"""
        self.clear_menu()
        
        # キャンパス一覧に戻るボタン
        back_btn = QToolButton()
        back_btn.setIcon(qta.icon('mdi.arrow-left', color='#FFFFFF'))
        back_btn.setText("キャンパス一覧に戻る")
        back_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        back_btn.setStyleSheet("""
            QToolButton {
                background-color: #6B7280;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #4B5563;
            }
        """)
        back_btn.clicked.connect(self.campus_index_requested.emit)
        
        self.menu_layout.addWidget(back_btn)
        self.current_page = "campus_edit"
    
    def set_image_index_menu(self):
        """画像一覧画面用のメニューを設定"""
        self.clear_menu()
        
        # キャンパス一覧に戻るボタン
        back_btn = QToolButton()
        back_btn.setIcon(qta.icon('mdi.arrow-left', color='#FFFFFF'))
        back_btn.setText("キャンパス一覧に戻る")
        back_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        back_btn.setFixedSize(220, 50)  # サイズを固定（幅を拡張）
        back_btn.setStyleSheet("""
            QToolButton {
                background-color: #6B7280;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
                margin-right: 20px;
            }
            QToolButton:hover {
                background-color: #4B5563;
            }
        """)
        back_btn.clicked.connect(self.campus_index_requested.emit)
        
        # 位置修正ボタン（参照を保存）
        self.position_edit_btn = QToolButton()
        self.position_edit_btn.setIcon(qta.icon('mdi.drag', color='#FFFFFF'))
        self.position_edit_btn.setText("位置修正")
        self.position_edit_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.position_edit_btn.setFixedSize(220, 50)  # サイズを固定（幅を拡張）
        self.position_edit_btn.setStyleSheet("""
            QToolButton {
                background-color: #10B981;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
                margin-right: 20px;
            }
            QToolButton:hover {
                background-color: #059669;
            }
        """)
        self.position_edit_btn.clicked.connect(self.image_position_edit_requested.emit)
        
        # 編集ボタン（参照を保存）
        self.edit_btn = QToolButton()
        self.edit_btn.setIcon(qta.icon('mdi.pencil', color='#FFFFFF'))
        self.edit_btn.setText("編集")
        self.edit_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.edit_btn.setFixedSize(220, 50)  # サイズを固定（幅を拡張）
        self.edit_btn.setStyleSheet("""
            QToolButton {
                background-color: #F59E0B;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
                margin-right: 20px;
            }
            QToolButton:hover {
                background-color: #D97706;
            }
        """)
        self.edit_btn.clicked.connect(self.image_manage_mode_requested.emit)
        
        # アップロードボタン
        upload_btn = QToolButton()
        upload_btn.setIcon(qta.icon('mdi.upload', color='#FFFFFF'))
        upload_btn.setText("画像アップロード")
        upload_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        upload_btn.setFixedSize(220, 50)  # サイズを固定（幅を拡張）
        upload_btn.setStyleSheet("""
            QToolButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
                margin-right: 20px;
            }
            QToolButton:hover {
                background-color: #2563EB;
            }
        """)
        upload_btn.clicked.connect(self.image_create_requested.emit)
        
        self.menu_layout.addWidget(back_btn)
        self.menu_layout.addWidget(self.position_edit_btn)
        self.menu_layout.addWidget(self.edit_btn)
        self.menu_layout.addWidget(upload_btn)
        self.current_page = "image_index"
    
    def set_image_create_menu(self):
        """画像アップロード画面用のメニューを設定"""
        self.clear_menu()
        
        # 画像一覧に戻るボタン
        back_btn = QToolButton()
        back_btn.setIcon(qta.icon('mdi.arrow-left', color='#FFFFFF'))
        back_btn.setText("画像一覧に戻る")
        back_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        back_btn.setStyleSheet("""
            QToolButton {
                background-color: #6B7280;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #4B5563;
            }
        """)
        back_btn.clicked.connect(self.image_index_requested.emit)
        
        self.menu_layout.addWidget(back_btn)
        self.current_page = "image_create"
    
    def set_image_edit_menu(self):
        """画像編集画面用のメニューを設定"""
        self.clear_menu()
        
        # 画像一覧に戻るボタン
        back_btn = QToolButton()
        back_btn.setIcon(qta.icon('mdi.arrow-left', color='#FFFFFF'))
        back_btn.setText("画像一覧に戻る")
        back_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        back_btn.setStyleSheet("""
            QToolButton {
                background-color: #6B7280;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #4B5563;
            }
        """)
        back_btn.clicked.connect(self.image_index_requested.emit)
        
        self.menu_layout.addWidget(back_btn)
        self.current_page = "image_edit"
    
    def set_image_detail_menu(self):
        """画像詳細画面用のメニューを設定"""
        self.clear_menu()
        
        # 画像一覧に戻るボタン
        back_btn = QToolButton()
        back_btn.setIcon(qta.icon('mdi.arrow-left', color='#FFFFFF'))
        back_btn.setText("画像一覧に戻る")
        back_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        back_btn.setStyleSheet("""
            QToolButton {
                background-color: #6B7280;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #4B5563;
            }
        """)
        back_btn.clicked.connect(self.image_index_requested.emit)
        
        self.menu_layout.addWidget(back_btn)
        self.current_page = "image_detail"
    
    def set_video_index_menu(self):
        """動画一覧画面用のメニューを設定"""
        self.clear_menu()
        
        # キャンパス一覧に戻るボタン
        back_btn = QToolButton()
        back_btn.setIcon(qta.icon('mdi.arrow-left', color='#FFFFFF'))
        back_btn.setText("キャンパス一覧に戻る")
        back_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        back_btn.setFixedSize(220, 50)  # サイズを固定（幅を拡張）
        back_btn.setStyleSheet("""
            QToolButton {
                background-color: #6B7280;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
                margin-right: 20px;
            }
            QToolButton:hover {
                background-color: #4B5563;
            }
        """)
        back_btn.clicked.connect(self.campus_index_requested.emit)
        
        # 編集ボタン
        edit_btn = QToolButton()
        edit_btn.setIcon(qta.icon('mdi.pencil', color='#FFFFFF'))
        edit_btn.setText("編集")
        edit_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        edit_btn.setFixedSize(220, 50)  # サイズを固定（幅を拡張）
        edit_btn.setStyleSheet("""
            QToolButton {
                background-color: #F59E0B;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
                margin-right: 20px;
            }
            QToolButton:hover {
                background-color: #D97706;
            }
        """)
        edit_btn.clicked.connect(self.video_manage_mode_requested.emit)
        
        # アップロードボタン
        upload_btn = QToolButton()
        upload_btn.setIcon(qta.icon('mdi.upload', color='#FFFFFF'))
        upload_btn.setText("動画を追加")
        upload_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        upload_btn.setFixedSize(220, 50)  # サイズを固定（幅を拡張）
        upload_btn.setStyleSheet("""
            QToolButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
                margin-right: 20px;
            }
            QToolButton:hover {
                background-color: #2563EB;
            }
        """)
        upload_btn.clicked.connect(self.video_create_requested.emit)
        
        self.menu_layout.addWidget(back_btn)
        self.menu_layout.addWidget(edit_btn)
        self.menu_layout.addWidget(upload_btn)
        self.current_page = "video_index"
    
    def set_video_create_menu(self):
        """動画アップロード画面用のメニューを設定"""
        self.clear_menu()
        
        # 動画一覧に戻るボタン
        back_btn = QToolButton()
        back_btn.setIcon(qta.icon('mdi.arrow-left', color='#FFFFFF'))
        back_btn.setText("動画一覧に戻る")
        back_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        back_btn.setStyleSheet("""
            QToolButton {
                background-color: #6B7280;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #4B5563;
            }
        """)
        back_btn.clicked.connect(self.video_index_requested.emit)
        
        self.menu_layout.addWidget(back_btn)
        self.current_page = "video_create"
    
    def set_video_edit_menu(self):
        """動画編集画面用のメニューを設定"""
        self.clear_menu()
        
        # 動画一覧に戻るボタン
        back_btn = QToolButton()
        back_btn.setIcon(qta.icon('mdi.arrow-left', color='#FFFFFF'))
        back_btn.setText("動画一覧に戻る")
        back_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        back_btn.setStyleSheet("""
            QToolButton {
                background-color: #6B7280;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #4B5563;
            }
        """)
        back_btn.clicked.connect(self.video_index_requested.emit)
        
        self.menu_layout.addWidget(back_btn)
        self.current_page = "video_edit"
    
    def set_video_detail_menu(self):
        """動画詳細画面用のメニューを設定"""
        self.clear_menu()
        
        # キャンパス一覧に戻るボタン
        back_btn = QToolButton()
        back_btn.setIcon(qta.icon('mdi.school', color='#FFFFFF'))
        back_btn.setText("キャンパス一覧表示")
        back_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        back_btn.setStyleSheet("""
            QToolButton {
                background-color: #6B7280;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
            }
            QToolButton:hover {
                background-color: #4B5563;
            }
        """)
        back_btn.clicked.connect(self.campus_index_requested.emit)
        
        self.menu_layout.addWidget(back_btn)
        self.current_page = "video_detail"
    
    def clear_menu(self):
        """メニューをクリア"""
        while self.menu_layout.count():
            child = self.menu_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def update_image_position_edit_button(self, is_active: bool):
        """画像位置修正ボタンの状態を更新"""
        if hasattr(self, 'position_edit_btn') and self.position_edit_btn:
            if is_active:
                self.position_edit_btn.setText("位置修正終了")
                self.position_edit_btn.setStyleSheet("""
                    QToolButton {
                        background-color: #EF4444;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 16px;
                        text-align: left;
                        font-size: 14px;
                        margin-right: 20px;
                    }
                    QToolButton:hover {
                        background-color: #DC2626;
                    }
                """)
            else:
                self.position_edit_btn.setText("位置修正")
                self.position_edit_btn.setStyleSheet("""
                    QToolButton {
                        background-color: #10B981;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 16px;
                        text-align: left;
                        font-size: 14px;
                        margin-right: 20px;
                    }
                    QToolButton:hover {
                        background-color: #059669;
                    }
                """)
    
    def update_image_manage_button(self, is_active: bool):
        """画像編集ボタンの状態を更新"""
        if hasattr(self, 'edit_btn') and self.edit_btn:
            if is_active:
                self.edit_btn.setText("編集終了")
                self.edit_btn.setStyleSheet("""
                    QToolButton {
                        background-color: #EF4444;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 16px;
                        text-align: left;
                        font-size: 14px;
                        margin-right: 20px;
                    }
                    QToolButton:hover {
                        background-color: #DC2626;
                    }
                """)
            else:
                self.edit_btn.setText("編集")
                self.edit_btn.setStyleSheet("""
                    QToolButton {
                        background-color: #F59E0B;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 16px;
                        text-align: left;
                        font-size: 14px;
                        margin-right: 20px;
                    }
                    QToolButton:hover {
                        background-color: #D97706;
                    }
                """)


class MainContent(QFrame):
    """右側のメインコンテンツエリア"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        # メインコンテンツのスタイル設定
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: none;
            }
        """)
        
        # QStackedWidgetを使用してページ切り替え
        self.stacked_widget = QStackedWidget()
        
        # レイアウト設定
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 0, 0, 0)  # 左マージンを大きくしてサイドバーとの間隔を確保
        layout.addWidget(self.stacked_widget)
        
        self.setLayout(layout)
    
    def add_page(self, widget, page_name):
        """ページを追加"""
        self.stacked_widget.addWidget(widget)
        return self.stacked_widget.count() - 1
    
    def set_current_page(self, index):
        """現在のページを設定"""
        self.stacked_widget.setCurrentIndex(index)


class MainWindow(QMainWindow):
    """メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.sidebar_visible = True  # サイドバーの表示状態を管理
        self.setup_ui()
        self.setup_pages()
        self.connect_signals()
    
    def setup_ui(self):
        # ウィンドウの基本設定
        self.setWindowTitle("PySide6 画像・動画管理アプリ")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)
        
        # メニューバーの設定
        self.setup_menu_bar()
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト（水平方向）
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)  # サイドバーとメインコンテンツの間に大きな間隔を追加
        
        # サイドバーとメインコンテンツを追加
        self.sidebar = Sidebar()
        self.main_content = MainContent()
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.main_content)
        
        central_widget.setLayout(main_layout)
        
        # ウィンドウ全体のスタイル設定
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F7FA;
            }
        """)
    
    def setup_menu_bar(self):
        """メニューバーを設定"""
        menubar = self.menuBar()
        
        # 表示メニューを作成
        view_menu = menubar.addMenu('表示')
        
        # 左メニュー表示アクション
        self.show_sidebar_action = QAction('左メニューを表示', self)
        self.show_sidebar_action.setIcon(qta.icon('mdi.menu', color='#1F2937'))
        self.show_sidebar_action.triggered.connect(self.show_sidebar)
        
        # 左メニュー非表示アクション
        self.hide_sidebar_action = QAction('左メニューを非表示', self)
        self.hide_sidebar_action.setIcon(qta.icon('mdi.menu-open', color='#1F2937'))
        self.hide_sidebar_action.triggered.connect(self.hide_sidebar)
        
        # メニューにアクションを追加
        view_menu.addAction(self.show_sidebar_action)
        view_menu.addAction(self.hide_sidebar_action)
        
        # 初期状態の設定（左メニューが表示されているので、表示ボタンを無効化）
        self.update_sidebar_menu_state()
    
    def show_sidebar(self):
        """左メニューを表示"""
        if not self.sidebar_visible:
            self.sidebar.show()
            self.sidebar_visible = True
            self.update_sidebar_menu_state()
    
    def hide_sidebar(self):
        """左メニューを非表示"""
        if self.sidebar_visible:
            self.sidebar.hide()
            self.sidebar_visible = False
            self.update_sidebar_menu_state()
    
    def update_sidebar_menu_state(self):
        """左メニューの表示状態に応じてメニューボタンの有効/無効を切り替え"""
        if self.sidebar_visible:
            # 左メニューが表示されている場合
            self.show_sidebar_action.setEnabled(False)  # 表示ボタンを無効化
            self.hide_sidebar_action.setEnabled(True)   # 非表示ボタンを有効化
        else:
            # 左メニューが非表示の場合
            self.show_sidebar_action.setEnabled(True)   # 表示ボタンを有効化
            self.hide_sidebar_action.setEnabled(False)  # 非表示ボタンを無効化
    
    def setup_pages(self):
        """ページをセットアップ"""
        # キャンパス関連ページを作成
        self.campus_index_widget = CampusIndexWidget()
        self.campus_create_widget = CampusCreateWidget()
        
        # ページをスタックに追加
        self.campus_index_index = self.main_content.add_page(self.campus_index_widget, "campus_index")
        self.campus_create_index = self.main_content.add_page(self.campus_create_widget, "campus_create")
        
        # 編集ページは動的に作成するため、ここでは追加しない
        self.campus_edit_widget = None
        self.campus_edit_index = None
        
        # 画像関連ページも動的に作成するため、ここでは追加しない
        self.image_index_widget = None
        self.image_index_index = None
        self.image_create_widget = None
        self.image_create_index = None
        self.image_edit_widget = None
        self.image_edit_index = None
        self.image_detail_widget = None
        self.image_detail_index = None
        
        # 動画関連ページも動的に作成するため、ここでは追加しない
        self.video_index_widget = None
        self.video_index_index = None
        self.video_create_widget = None
        self.video_create_index = None
        self.video_edit_widget = None
        self.video_edit_index = None
        self.video_detail_widget = None
        self.video_detail_index = None
        
        # 初期ページを設定
        self.main_content.set_current_page(self.campus_index_index)
        self.sidebar.set_campus_index_menu()
    
    def connect_signals(self):
        """シグナルを接続"""
        # サイドバーのシグナル
        self.sidebar.campus_index_requested.connect(self.show_campus_index)
        self.sidebar.campus_create_requested.connect(self.show_campus_create)
        self.sidebar.image_index_requested.connect(self.show_image_index)
        self.sidebar.video_index_requested.connect(self.show_video_index)
        self.sidebar.image_create_requested.connect(self.show_image_create)
        self.sidebar.image_position_edit_requested.connect(self.toggle_image_position_edit_mode)
        self.sidebar.image_manage_mode_requested.connect(self.toggle_image_manage_mode)
        self.sidebar.video_create_requested.connect(self.show_video_create)
        self.sidebar.video_manage_mode_requested.connect(self.toggle_video_manage_mode)
        
        # キャンパス一覧のシグナル
        self.campus_index_widget.create_campus_requested.connect(self.show_campus_create)
        self.campus_index_widget.edit_campus_requested.connect(self.show_campus_edit)
        self.campus_index_widget.image_index_requested.connect(self.show_image_index)
        self.campus_index_widget.video_index_requested.connect(self.show_video_index)
        
        # キャンパス作成のシグナル
        self.campus_create_widget.campus_created.connect(self.on_campus_created)
        self.campus_create_widget.back_to_index.connect(self.show_campus_index)
    
    def show_campus_index(self):
        """キャンパス一覧画面を表示"""
        # 動画詳細画面が表示されている場合は動画リソースを解放
        if hasattr(self, 'video_detail_widget') and self.video_detail_widget:
            if hasattr(self.video_detail_widget, 'player_widget'):
                self.video_detail_widget.player_widget.closeEvent(None)
        
        self.main_content.set_current_page(self.campus_index_index)
        self.sidebar.set_campus_index_menu()
        self.campus_index_widget.refresh()
    
    def show_campus_create(self):
        """キャンパス作成画面を表示"""
        self.main_content.set_current_page(self.campus_create_index)
        self.sidebar.set_campus_create_menu()
        self.campus_create_widget.clear_form()
    
    def show_campus_edit(self, campus_id):
        """キャンパス編集画面を表示"""
        # 既存の編集ウィジェットがあれば削除
        if self.campus_edit_widget:
            self.main_content.stacked_widget.removeWidget(self.campus_edit_widget)
            self.campus_edit_widget.deleteLater()
        
        # 新しい編集ウィジェットを作成
        self.campus_edit_widget = CampusEditWidget(campus_id)
        self.campus_edit_index = self.main_content.add_page(self.campus_edit_widget, "campus_edit")
        
        # シグナルを接続
        self.campus_edit_widget.campus_updated.connect(self.on_campus_updated)
        self.campus_edit_widget.campus_deleted.connect(self.on_campus_deleted)
        self.campus_edit_widget.back_to_index.connect(self.show_campus_index)
        
        # ページを表示
        self.main_content.set_current_page(self.campus_edit_index)
        self.sidebar.set_campus_edit_menu()
    
    def on_campus_created(self):
        """キャンパス作成完了時の処理"""
        self.show_campus_index()
    
    def on_campus_updated(self):
        """キャンパス更新完了時の処理"""
        self.show_campus_index()
    
    def on_campus_deleted(self):
        """キャンパス削除完了時の処理"""
        self.show_campus_index()
    
    def show_image_index(self, campus_id):
        """画像一覧画面を表示"""
        # 既存の画像一覧ウィジェットがあれば削除
        if self.image_index_widget:
            self.main_content.stacked_widget.removeWidget(self.image_index_widget)
            self.image_index_widget.deleteLater()
        
        # 新しい画像一覧ウィジェットを作成
        self.image_index_widget = ImageIndexWidget(campus_id)
        self.image_index_index = self.main_content.add_page(self.image_index_widget, "image_index")
        
        # シグナルを接続
        self.image_index_widget.back_to_campus_requested.connect(self.show_campus_index)
        self.image_index_widget.image_create_requested.connect(self.show_image_create)
        self.image_index_widget.image_edit_requested.connect(self.show_image_edit)
        self.image_index_widget.image_detail_requested.connect(self.show_image_detail)
        
        # ページを表示
        self.main_content.set_current_page(self.image_index_index)
        self.sidebar.set_image_index_menu()
        
        # 現在の状態に応じて左メニューのボタン状態を更新
        self.sidebar.update_image_position_edit_button(self.image_index_widget.position_edit_mode)
        self.sidebar.update_image_manage_button(self.image_index_widget.manage_mode)
    
    def show_image_create(self):
        """画像アップロード画面を表示"""
        if not self.image_index_widget:
            return
        
        campus_id = self.image_index_widget.campus_id
        
        # 既存の画像アップロードウィジェットがあれば削除
        if self.image_create_widget:
            self.main_content.stacked_widget.removeWidget(self.image_create_widget)
            self.image_create_widget.deleteLater()
        
        # 新しい画像アップロードウィジェットを作成
        self.image_create_widget = ImageCreateWidget(campus_id)
        self.image_create_index = self.main_content.add_page(self.image_create_widget, "image_create")
        
        # シグナルを接続
        self.image_create_widget.back_to_index_requested.connect(self.show_image_index_from_create)
        self.image_create_widget.image_created.connect(self.on_image_created)
        
        # ページを表示
        self.main_content.set_current_page(self.image_create_index)
        self.sidebar.set_image_create_menu()
    
    def show_image_edit(self, image_id):
        """画像編集画面を表示"""
        # 既存の画像編集ウィジェットがあれば削除
        if self.image_edit_widget:
            self.main_content.stacked_widget.removeWidget(self.image_edit_widget)
            self.image_edit_widget.deleteLater()
        
        # 新しい画像編集ウィジェットを作成
        self.image_edit_widget = ImageEditWidget(image_id)
        self.image_edit_index = self.main_content.add_page(self.image_edit_widget, "image_edit")
        
        # シグナルを接続
        self.image_edit_widget.back_to_index_requested.connect(self.show_image_index_from_edit)
        self.image_edit_widget.image_updated.connect(self.on_image_updated)
        self.image_edit_widget.image_deleted.connect(self.on_image_deleted)
        
        # ページを表示
        self.main_content.set_current_page(self.image_edit_index)
        self.sidebar.set_image_edit_menu()
    
    def show_image_detail(self, image_id):
        """画像詳細画面を表示"""
        # 既存の画像詳細ウィジェットがあれば削除
        if self.image_detail_widget:
            self.main_content.stacked_widget.removeWidget(self.image_detail_widget)
            self.image_detail_widget.deleteLater()
        
        # 新しい画像詳細ウィジェットを作成
        self.image_detail_widget = ImageDetailWidget(image_id)
        self.image_detail_index = self.main_content.add_page(self.image_detail_widget, "image_detail")
        
        # シグナルを接続
        self.image_detail_widget.back_to_index_requested.connect(self.show_image_index_from_detail)
        self.image_detail_widget.image_edit_requested.connect(self.show_image_edit)
        
        # ページを表示
        self.main_content.set_current_page(self.image_detail_index)
        self.sidebar.set_image_detail_menu()
    
    def show_image_index_from_create(self):
        """画像アップロード画面から画像一覧に戻る"""
        if self.image_index_widget:
            self.main_content.set_current_page(self.image_index_index)
            self.sidebar.set_image_index_menu()
            self.image_index_widget.refresh()
    
    def show_image_index_from_edit(self):
        """画像編集画面から画像一覧に戻る"""
        if self.image_index_widget:
            self.main_content.set_current_page(self.image_index_index)
            self.sidebar.set_image_index_menu()
            self.image_index_widget.refresh()
    
    def show_image_index_from_detail(self):
        """画像詳細画面から画像一覧に戻る"""
        if self.image_index_widget:
            self.main_content.set_current_page(self.image_index_index)
            self.sidebar.set_image_index_menu()
            self.image_index_widget.refresh()
    
    def on_image_created(self):
        """画像作成完了時の処理"""
        self.show_image_index_from_create()
    
    def on_image_updated(self):
        """画像更新完了時の処理"""
        self.show_image_index_from_edit()
    
    def on_image_deleted(self):
        """画像削除完了時の処理"""
        self.show_image_index_from_edit()
    
    def show_video_index(self, campus_id):
        """動画一覧画面を表示"""
        # 既存の動画一覧ウィジェットがあれば削除
        if self.video_index_widget:
            self.main_content.stacked_widget.removeWidget(self.video_index_widget)
            self.video_index_widget.deleteLater()
        
        # 新しい動画一覧ウィジェットを作成
        self.video_index_widget = VideoIndexWidget(campus_id)
        self.video_index_index = self.main_content.add_page(self.video_index_widget, "video_index")
        
        # シグナルを接続
        self.video_index_widget.back_to_campus_requested.connect(self.show_campus_index)
        self.video_index_widget.video_create_requested.connect(self.show_video_create)
        self.video_index_widget.video_edit_requested.connect(self.show_video_edit)
        self.video_index_widget.video_detail_requested.connect(self.show_video_detail)
        
        # ページを表示
        self.main_content.set_current_page(self.video_index_index)
        self.sidebar.set_video_index_menu()
    
    def show_video_create(self):
        """動画アップロード画面を表示"""
        if not self.video_index_widget:
            return
        
        campus_id = self.video_index_widget.campus_id
        
        # 既存の動画アップロードウィジェットがあれば削除
        if self.video_create_widget:
            self.main_content.stacked_widget.removeWidget(self.video_create_widget)
            self.video_create_widget.deleteLater()
        
        # 新しい動画アップロードウィジェットを作成
        self.video_create_widget = VideoCreateWidget(campus_id)
        self.video_create_index = self.main_content.add_page(self.video_create_widget, "video_create")
        
        # シグナルを接続
        self.video_create_widget.back_to_index_requested.connect(self.show_video_index_from_create)
        self.video_create_widget.video_created.connect(self.on_video_created)
        
        # ページを表示
        self.main_content.set_current_page(self.video_create_index)
        self.sidebar.set_video_create_menu()
    
    def show_video_edit(self, video_id):
        """動画編集画面を表示"""
        # 既存の動画編集ウィジェットがあれば削除
        if self.video_edit_widget:
            self.main_content.stacked_widget.removeWidget(self.video_edit_widget)
            self.video_edit_widget.deleteLater()
        
        # 新しい動画編集ウィジェットを作成
        self.video_edit_widget = VideoEditWidget(video_id)
        self.video_edit_index = self.main_content.add_page(self.video_edit_widget, "video_edit")
        
        # シグナルを接続
        self.video_edit_widget.back_to_index_requested.connect(self.show_video_index_from_edit)
        self.video_edit_widget.video_updated.connect(self.on_video_updated)
        self.video_edit_widget.video_deleted.connect(self.on_video_deleted)
        
        # ページを表示
        self.main_content.set_current_page(self.video_edit_index)
        self.sidebar.set_video_edit_menu()
    
    def show_video_detail(self, video_id):
        """動画詳細画面を表示"""
        # 既存の動画詳細ウィジェットがあれば削除
        if self.video_detail_widget:
            self.main_content.stacked_widget.removeWidget(self.video_detail_widget)
            self.video_detail_widget.deleteLater()
        
        # 新しい動画詳細ウィジェットを作成
        self.video_detail_widget = VideoDetailWidget(video_id)
        self.video_detail_index = self.main_content.add_page(self.video_detail_widget, "video_detail")
        
        # シグナルを接続
        self.video_detail_widget.back_to_index_requested.connect(self.show_video_index_from_detail)
        self.video_detail_widget.video_index_requested.connect(self.show_video_index)
        self.video_detail_widget.video_edit_requested.connect(self.show_video_edit)
        
        # ページを表示
        self.main_content.set_current_page(self.video_detail_index)
        self.sidebar.set_video_detail_menu()
    
    def show_video_index_from_create(self):
        """動画アップロード画面から動画一覧に戻る"""
        if self.video_index_widget:
            self.main_content.set_current_page(self.video_index_index)
            self.sidebar.set_video_index_menu()
            self.video_index_widget.refresh()
    
    def show_video_index_from_edit(self):
        """動画編集画面から動画一覧に戻る"""
        if self.video_index_widget:
            self.main_content.set_current_page(self.video_index_index)
            self.sidebar.set_video_index_menu()
            self.video_index_widget.refresh()
    
    def show_video_index_from_detail(self):
        """動画詳細画面から動画一覧に戻る"""
        if self.video_index_widget:
            self.main_content.set_current_page(self.video_index_index)
            self.sidebar.set_video_index_menu()
            self.video_index_widget.refresh()
    
    def on_video_created(self):
        """動画作成完了時の処理"""
        self.show_video_index_from_create()
    
    def on_video_updated(self):
        """動画更新完了時の処理"""
        self.show_video_index_from_edit()
    
    def on_video_deleted(self):
        """動画削除完了時の処理"""
        self.show_video_index_from_edit()
    
    def toggle_image_position_edit_mode(self):
        """画像位置修正モードの切り替え"""
        if self.image_index_widget:
            self.image_index_widget.toggle_position_edit_mode()
            # 左メニューのボタン状態を更新
            self.sidebar.update_image_position_edit_button(self.image_index_widget.position_edit_mode)
    
    def toggle_image_manage_mode(self):
        """画像編集モードの切り替え"""
        if self.image_index_widget:
            self.image_index_widget.toggle_manage_mode()
            # 左メニューのボタン状態を更新
            self.sidebar.update_image_manage_button(self.image_index_widget.manage_mode)
    
    def toggle_video_manage_mode(self):
        """動画編集モードの切り替え"""
        if self.video_index_widget:
            self.video_index_widget.toggle_manage_mode()


def main():
    """アプリケーションのエントリーポイント"""
    # データベースの初期化
    print("データベースを初期化しています...")
    try:
        db_path = create_database()
        print(f"データベース '{db_path}' の初期化が完了しました。")
    except Exception as e:
        print(f"データベース初期化中にエラーが発生しました: {e}")
        return
    
    # PySide6アプリケーションの開始
    app = QApplication(sys.argv)
    
    # アプリケーションのスタイル設定
    app.setStyle('Fusion')
    
    # アプリケーション全体のスタイルを設定（QMessageBoxの文字色を修正）
    app.setStyleSheet("""
        QMessageBox {
            background-color: #FFFFFF;
            color: #1F2937;
        }
        QMessageBox QLabel {
            color: #1F2937;
        }
        QMessageBox QPushButton {
            background-color: #3B82F6;
            color: #FFFFFF;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }
        QMessageBox QPushButton:hover {
            background-color: #2563EB;
        }
    """)
    
    # メインウィンドウを作成して表示
    window = MainWindow()
    window.show()
    
    # アプリケーションの実行
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
