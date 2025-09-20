#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画像一覧画面（シンプル版）
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QGridLayout,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter, QPen
import qtawesome as qta

from models import Image, Campus


class ImageCard(QFrame):
    """画像カードウィジェット（シンプル版）"""
    
    # シグナル定義
    image_clicked = Signal(int)
    
    def __init__(self, image: Image):
        super().__init__()
        self.image = image
        self.setup_ui()
    
    def setup_ui(self):
        """UIをセットアップ"""
        # カードのスタイル設定
        self.setFixedSize(250, 300)
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        # レイアウト設定
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 10)  # 左右マージンを小さく
        layout.setSpacing(5)  # スペーシングを小さく
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)  # 上詰めかつ水平中央揃え
        
        # 画像プレビューエリア
        self.image_label = QLabel()
        self.image_label.setFixedSize(240, 200)  # 幅を少し大きく
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
        filename_label = QLabel(self.image.name)
        filename_label.setStyleSheet("""
            QLabel {
                color: #1F2937;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        filename_label.setWordWrap(True)
        filename_label.setMaximumHeight(40)
        filename_label.setAlignment(Qt.AlignCenter)
        
        # レイアウトに追加
        layout.addWidget(self.image_label)
        layout.addWidget(filename_label)
        
        self.setLayout(layout)
    
    def load_image_preview(self):
        """画像プレビューを読み込み"""
        try:
            if self.image.file_data and len(self.image.file_data) > 0:
                pixmap = QPixmap()
                if pixmap.loadFromData(self.image.file_data):
                    # アスペクト比を保ってリサイズ
                    scaled_pixmap = pixmap.scaled(
                        self.image_label.size(), 
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                else:
                    self.set_placeholder_image()
            else:
                self.set_placeholder_image()
        except Exception as e:
            print(f"画像読み込みエラー: {e}")
            self.set_placeholder_image()
    
    def set_placeholder_image(self):
        """プレースホルダー画像を設定"""
        # プレースホルダー画像を作成
        pixmap = QPixmap(240, 200)
        pixmap.fill(Qt.lightGray)
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.gray, 2))
        painter.drawRect(15, 15, 210, 170)
        painter.drawText(120, 100, "No Image")
        painter.end()
        
        self.image_label.setPixmap(pixmap)
    
    def mousePressEvent(self, event):
        """マウスクリックイベント"""
        if event.button() == Qt.LeftButton:
            self.image_clicked.emit(self.image.id)


class ImageIndexWidget(QWidget):
    """画像一覧画面ウィジェット（シンプル版）"""
    
    # シグナル定義（main.pyで必要なシグナル）
    back_to_campus_requested = Signal()
    image_create_requested = Signal()
    image_edit_requested = Signal(int)
    image_detail_requested = Signal(int)
    
    def __init__(self, campus_id: int):
        super().__init__()
        self.campus_id = campus_id
        self.images = []
        self.setup_ui()
        self.load_images()
    
    def setup_ui(self):
        """UIをセットアップ"""
        # メインレイアウト
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # ヘッダー部分
        header_layout = QHBoxLayout()
        
        # 戻るボタン
        back_button = QPushButton("← キャンパス一覧に戻る")
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
        back_button.clicked.connect(self.back_to_campus_requested.emit)
        
        # タイトル
        title_label = QLabel("画像一覧")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1F2937;")
        
        # アップロードボタン
        upload_button = QPushButton("画像アップロード")
        upload_button.setStyleSheet("""
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
        """)
        upload_button.clicked.connect(self.image_create_requested.emit)
        
        header_layout.addWidget(back_button)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(upload_button)
        
        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #F9FAFB;
            }
        """)
        
        # 画像グリッドコンテナ
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(10, 5, 10, 10)  # 上マージンを小さく
        self.grid_layout.setAlignment(Qt.AlignTop)  # グリッドも上詰めに設定
        self.grid_container.setLayout(self.grid_layout)
        
        scroll_area.setWidget(self.grid_container)
        
        # レイアウトに追加
        main_layout.addLayout(header_layout)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
    
    def load_images(self):
        """画像一覧を読み込み"""
        try:
            self.images = Image.get_by_campus_id(self.campus_id)
            self.display_images()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"画像の読み込みに失敗しました:\n{str(e)}")
    
    def display_images(self):
        """画像をグリッドに表示（sort_order順）"""
        # グリッドレイアウトをクリア
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.images:
            # 画像が存在しない場合のメッセージ
            no_images_label = QLabel("画像が登録されていません")
            no_images_label.setAlignment(Qt.AlignCenter)
            no_images_label.setStyleSheet("""
                QLabel {
                    color: #6B7280;
                    font-size: 16px;
                    padding: 50px;
                }
            """)
            self.grid_layout.addWidget(no_images_label, 0, 0, 1, -1)
            return
        
        # sort_orderでソート（念のため）
        sorted_images = sorted(self.images, key=lambda x: x.sort_order)
        
        # 固定列数でグリッドに配置（上詰め）
        columns = 3  # 画像サイズが大きくなったので3列に変更
        
        for i, image in enumerate(sorted_images):
            card = ImageCard(image)
            card.image_clicked.connect(self.image_detail_requested.emit)
            row = i // columns
            col = i % columns
            self.grid_layout.addWidget(card, row, col)
    
    def refresh(self):
        """画像一覧を再読み込み"""
        self.load_images()