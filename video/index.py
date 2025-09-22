#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
動画一覧画面
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QGridLayout,
    QMessageBox, QApplication, QSizePolicy, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
from PySide6.QtGui import QFont, QPixmap, QPainter, QPen, QDrag, QPainterPath
import qtawesome as qta
from typing import Optional
import os

from models import Video, Campus
from video_utils import get_video_directories, is_video_file, copy_video_file, generate_thumbnail


class VideoCard(QFrame):
    """動画カードウィジェット"""
    
    # シグナル定義
    video_clicked = Signal(int)
    video_dragged = Signal(int, int, int)  # video_id, from_row, from_col
    video_dropped = Signal(int, int, int)  # video_id, to_row, to_col
    
    def __init__(self, video: Video, row: int = 0, col: int = 0):
        super().__init__()
        self.video = video
        self.row = row
        self.col = col
        self.drag_start_position = QPoint()
        self.position_edit_mode_ref = None  # 位置修正モードの参照
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
        layout.setContentsMargins(5, 5, 5, 10)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        # サムネイルプレビューエリア
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(240, 200)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 4px;
            }
        """)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setScaledContents(True)
        
        # サムネイルを読み込み
        self.load_thumbnail_preview()
        
        # ファイル名
        filename = os.path.basename(self.video.file_path) if self.video.file_path else "動画ファイル"
        filename_label = QLabel(filename)
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
        layout.addWidget(self.thumbnail_label)
        layout.addWidget(filename_label)
        
        self.setLayout(layout)
    
    def load_thumbnail_preview(self):
        """サムネイルプレビューを読み込み"""
        try:
            if self.video.thumbnail_path and os.path.exists(self.video.thumbnail_path):
                pixmap = QPixmap(self.video.thumbnail_path)
                if not pixmap.isNull():
                    # アスペクト比を保ってリサイズ
                    scaled_pixmap = pixmap.scaled(
                        self.thumbnail_label.size(), 
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    self.thumbnail_label.setPixmap(scaled_pixmap)
                else:
                    self.set_default_thumbnail()
            else:
                self.set_default_thumbnail()
        except Exception as e:
            print(f"サムネイル読み込みエラー: {e}")
            self.set_default_thumbnail()
    
    def set_default_thumbnail(self):
        """デフォルトのサムネイルを設定"""
        # 動画アイコンを表示
        icon = qta.icon('fa5s.play-circle', color='#9CA3AF')
        pixmap = icon.pixmap(64, 64)
        self.thumbnail_label.setPixmap(pixmap)
    
    def mousePressEvent(self, event):
        """マウスプレスイベント"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """マウスムーブイベント（ドラッグ開始）"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if ((event.position().toPoint() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
        
        # ドラッグ開始
        self.start_drag()
    
    def start_drag(self):
        """ドラッグを開始"""
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"video:{self.video.id}:{self.row}:{self.col}")
        drag.setMimeData(mime_data)
        
        # ドラッグ用の画像を作成
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        
        # ドラッグ実行
        self.video_dragged.emit(self.video.id, self.row, self.col)
        drag.exec_(Qt.MoveAction)
    
    def dragEnterEvent(self, event):
        """ドラッグエンターイベント"""
        if event.mimeData().hasText() and event.mimeData().text().startswith("video:"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """ドロップイベント"""
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("video:"):
                parts = text.split(":")
                if len(parts) >= 4:
                    video_id = int(parts[1])
                    from_row = int(parts[2])
                    from_col = int(parts[3])
                    self.video_dropped.emit(video_id, from_row, from_col)
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def mouseDoubleClickEvent(self, event):
        """ダブルクリックイベント"""
        if event.button() == Qt.LeftButton:
            self.video_clicked.emit(self.video.id)


class VideoIndexWidget(QWidget):
    """動画一覧ウィジェット"""
    
    # シグナル定義
    video_selected = Signal(int)
    add_video_requested = Signal()
    back_to_campus_requested = Signal()
    video_create_requested = Signal()
    video_edit_requested = Signal(int)
    video_detail_requested = Signal(int)
    
    def __init__(self, campus_id: int):
        super().__init__()
        self.campus_id = campus_id
        self.campus = Campus.get_by_id(campus_id)
        self.video_cards = []
        self.setup_ui()
        self.load_videos()
    
    def setup_ui(self):
        """UIをセットアップ"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # ヘッダー部分
        header_layout = QHBoxLayout()
        
        # タイトル
        title_text = f"動画一覧 - {self.campus.name if self.campus else 'Unknown'}"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1F2937;
            }
        """)
        
        # 動画追加ボタン
        add_button = QPushButton()
        add_button.setIcon(qta.icon('fa5s.plus', color='white'))
        add_button.setText("動画を追加")
        add_button.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        add_button.clicked.connect(self.video_create_requested.emit)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(add_button)
        
        # スクロールエリア
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # コンテンツウィジェット
        self.content_widget = QWidget()
        self.content_layout = QGridLayout()
        self.content_layout.setSpacing(10)
        self.content_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.content_widget.setLayout(self.content_layout)
        
        self.scroll_area.setWidget(self.content_widget)
        
        # レイアウトに追加
        layout.addLayout(header_layout)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
    
    def load_videos(self):
        """動画一覧を読み込み"""
        # 既存のカードをクリア
        self.clear_video_cards()
        
        # 動画データを取得
        videos = Video.get_by_campus_id(self.campus_id)
        
        if not videos:
            self.show_empty_state()
            return
        
        # 動画カードを作成
        self.create_video_cards(videos)
    
    def clear_video_cards(self):
        """動画カードをクリア"""
        for card in self.video_cards:
            card.deleteLater()
        self.video_cards.clear()
        
        # レイアウトをクリア
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def create_video_cards(self, videos):
        """動画カードを作成"""
        cols = 4  # 1行に4つのカード
        
        for i, video in enumerate(videos):
            row = i // cols
            col = i % cols
            
            card = VideoCard(video, row, col)
            card.video_clicked.connect(self.on_video_clicked)
            card.video_dragged.connect(self.on_video_dragged)
            card.video_dropped.connect(self.on_video_dropped)
            
            self.content_layout.addWidget(card, row, col)
            self.video_cards.append(card)
    
    def show_empty_state(self):
        """空の状態を表示"""
        empty_label = QLabel("動画がありません\n「動画を追加」ボタンから動画をアップロードしてください")
        empty_label.setStyleSheet("""
            QLabel {
                color: #6B7280;
                font-size: 16px;
                text-align: center;
            }
        """)
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setMinimumHeight(200)
        
        self.content_layout.addWidget(empty_label, 0, 0, 1, 4)
    
    def on_video_clicked(self, video_id: int):
        """動画クリック時の処理"""
        self.video_detail_requested.emit(video_id)
    
    def on_video_dragged(self, video_id: int, from_row: int, from_col: int):
        """動画ドラッグ開始時の処理"""
        # ドラッグ中の視覚的フィードバック
        pass
    
    def on_video_dropped(self, video_id: int, to_row: int, to_col: int):
        """動画ドロップ時の処理"""
        # 並び順の更新処理
        self.update_video_order(video_id, to_row, to_col)
    
    def update_video_order(self, video_id: int, new_row: int, new_col: int):
        """動画の並び順を更新"""
        try:
            # 新しいsort_orderを計算
            new_sort_order = new_row * 4 + new_col + 1
            
            # データベースを更新
            video = Video.get_by_id(video_id)
            if video:
                video.sort_order = new_sort_order
                video.save()
                
                # 一覧を再読み込み
                self.load_videos()
                
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"並び順の更新に失敗しました: {e}")
    
    def refresh(self):
        """一覧を更新"""
        self.load_videos()
