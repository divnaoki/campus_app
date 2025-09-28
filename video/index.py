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
    edit_clicked = Signal(int)
    delete_clicked = Signal(int)
    
    def __init__(self, video: Video, row: int = 0, col: int = 0):
        super().__init__()
        self.video = video
        self.row = row
        self.col = col
        self.drag_start_position = QPoint()
        self.position_edit_mode_ref = None  # 位置修正モードの参照
        self.manage_mode_ref = None  # 編集/削除ボタン表示モードの参照
        self.buttons_container = None
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
        
        # サムネイルプレビューエリア
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(240, 200)  # 幅を少し大きく
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 4px;
            }
        """)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setScaledContents(False)  # 手動でスケーリングするため無効化
        
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
        
        # ボタン行（編集・削除）
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        buttons_layout.setAlignment(Qt.AlignCenter)
        edit_btn = QPushButton("編集")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4F46E5;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.video.id))
        delete_btn = QPushButton("削除")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.video.id))
        buttons_layout.addWidget(edit_btn)
        buttons_layout.addWidget(delete_btn)

        self.buttons_container = QWidget()
        self.buttons_container.setLayout(buttons_layout)
        self.buttons_container.hide()

        # レイアウトに追加
        layout.addWidget(self.thumbnail_label)
        layout.addWidget(filename_label)
        layout.addWidget(self.buttons_container)
        
        self.setLayout(layout)
    
    def load_thumbnail_preview(self):
        """サムネイルプレビューを読み込み"""
        try:
            if self.video.thumbnail_path and os.path.exists(self.video.thumbnail_path):
                pixmap = QPixmap(self.video.thumbnail_path)
                if not pixmap.isNull():
                    # アスペクト比を保ってリサイズ（より高品質なスケーリング）
                    self.set_scaled_preview_pixmap(pixmap)
                else:
                    self.set_default_thumbnail()
            else:
                self.set_default_thumbnail()
        except Exception as e:
            print(f"サムネイル読み込みエラー: {e}")
            self.set_default_thumbnail()
    
    def set_scaled_preview_pixmap(self, pixmap):
        """アスペクト比を保ってプレビュー画像をスケールして表示"""
        if pixmap.isNull():
            return
        
        # 表示エリアのサイズを取得
        display_size = self.thumbnail_label.size()
        display_width = display_size.width()
        display_height = display_size.height()
        
        # 元画像のサイズを取得
        original_width = pixmap.width()
        original_height = pixmap.height()
        
        # アスペクト比を計算
        original_aspect = original_width / original_height
        display_aspect = display_width / display_height
        
        # アスペクト比に基づいて適切なサイズを計算
        if original_aspect > display_aspect:
            # 元画像が横長の場合、幅に合わせる
            scaled_width = display_width
            scaled_height = int(display_width / original_aspect)
        else:
            # 元画像が縦長の場合、高さに合わせる
            scaled_height = display_height
            scaled_width = int(display_height * original_aspect)
        
        # 高品質なスケーリングを実行
        scaled_pixmap = pixmap.scaled(
            scaled_width, 
            scaled_height, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        # 中央に配置するためのQPixmapを作成
        final_pixmap = QPixmap(display_width, display_height)
        final_pixmap.fill(Qt.transparent)
        
        # 中央に配置
        painter = QPainter(final_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        x_offset = (display_width - scaled_width) // 2
        y_offset = (display_height - scaled_height) // 2
        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
        painter.end()
        
        self.thumbnail_label.setPixmap(final_pixmap)
    
    def set_default_thumbnail(self):
        """デフォルトのサムネイルを設定"""
        # プレースホルダー画像を作成
        pixmap = QPixmap(240, 200)
        pixmap.fill(Qt.lightGray)
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.gray, 2))
        painter.drawRect(15, 15, 210, 170)
        painter.drawText(120, 100, "No Video")
        painter.end()
        
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

    def update_manage_buttons_visibility(self):
        """編集/削除ボタンの表示状態を更新"""
        if not self.buttons_container:
            return
        show = False
        if self.manage_mode_ref:
            try:
                show = bool(self.manage_mode_ref())
            except Exception:
                show = False
        self.buttons_container.setVisible(show)


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
        self.manage_mode = False
        self.current_columns = 4  # デフォルト列数
        self.setup_ui()
        self.load_videos()
    
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
        title_text = f"動画一覧 - {self.campus.name if self.campus else 'Unknown'}"
        title_label = QLabel(title_text)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1F2937;")
        
        header_layout.addWidget(back_button)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
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
        
        # 動画グリッドコンテナ
        self.grid_container = QWidget()
        self.grid_container.setAcceptDrops(True)
        self.grid_container.setSizePolicy(
            QSizePolicy.Expanding, 
            QSizePolicy.Preferred
        )
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(20, 10, 20, 10)  # 左右マージンを大きく
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)  # 上詰めかつ水平中央揃え
        self.grid_container.setLayout(self.grid_layout)
        
        # ドロップイベントをグリッドコンテナに接続
        self.grid_container.dragEnterEvent = self.dragEnterEvent
        self.grid_container.dragMoveEvent = self.dragMoveEvent
        self.grid_container.dropEvent = self.dropEvent
        
        scroll_area.setWidget(self.grid_container)
        
        # レイアウトに追加
        main_layout.addLayout(header_layout)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
    
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
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def create_video_cards(self, videos):
        """動画カードを作成"""
        # レスポンシブ対応で列数を計算
        columns = self.calculate_responsive_columns(self.width())
        self.current_columns = columns  # 現在の列数を更新
        
        # グリッドコンテナの最小幅を設定（中央揃えのため）
        card_width = 250
        spacing = 10
        min_width = columns * (card_width + spacing) - spacing + 40  # 40はマージン
        self.grid_container.setMinimumWidth(min_width)
        
        for i, video in enumerate(videos):
            row = i // columns
            col = i % columns
            
            card = VideoCard(video, row, col)
            card.video_clicked.connect(self.on_video_clicked)
            card.video_dragged.connect(self.on_video_dragged)
            card.video_dropped.connect(self.on_video_dropped)
            # 編集/削除ボタンの参照とイベント接続
            card.manage_mode_ref = lambda: self.manage_mode
            card.edit_clicked.connect(self.video_edit_requested.emit)
            card.delete_clicked.connect(lambda vid=video.id: self.confirm_and_delete_video(vid))
            
            self.grid_layout.addWidget(card, row, col)
            self.video_cards.append(card)
            card.update_manage_buttons_visibility()
    
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
        
        self.grid_layout.addWidget(empty_label, 0, 0, 1, -1)
    
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
            # レスポンシブ対応で列数を取得
            columns = self.current_columns if hasattr(self, 'current_columns') else 4
            new_sort_order = new_row * columns + new_col + 1
            
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

    def toggle_manage_mode(self):
        """編集/削除モードの切り替え"""
        self.manage_mode = not self.manage_mode

        # すべてのカードの表示状態を更新
        for card in self.video_cards:
            card.update_manage_buttons_visibility()

    def confirm_and_delete_video(self, video_id: int):
        """削除確認ダイアログを表示し、はいで削除、一覧更新"""
        try:
            video = Video.get_by_id(video_id)
            filename = os.path.basename(video.file_path) if (video and video.file_path) else "この動画"
            reply = QMessageBox.question(
                self,
                "削除確認",
                f"{filename} を削除します。よろしいですか？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                if video:
                    video.delete()
                self.load_videos()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"削除に失敗しました:\n{str(e)}")
    
    def calculate_responsive_columns(self, window_width: int) -> int:
        """ウィンドウ幅に基づいて列数を計算（2-5列の範囲）"""
        card_width = 250
        spacing = 10
        margin = 80  # 左右マージンを大きくして余白を確保
        
        available_width = window_width - margin
        calculated_columns = available_width // (card_width + spacing)
        
        # 2-5列の範囲に制限
        return max(2, min(5, calculated_columns))
    
    def resizeEvent(self, event):
        """ウィンドウリサイズ時の処理"""
        super().resizeEvent(event)
        # レスポンシブ対応でグリッドを再描画
        if hasattr(self, 'video_cards') and self.video_cards:
            self.refresh_layout_only()
    
    def refresh_layout_only(self):
        """レイアウトのみを更新（レスポンシブ対応）"""
        # 現在の列数を取得
        old_columns = self.current_columns
        new_columns = self.calculate_responsive_columns(self.width())
        
        # 列数が変わらない場合は何もしない
        if old_columns == new_columns:
            return
        
        # 現在の列数を更新
        self.current_columns = new_columns
        
        # グリッドレイアウトをクリア
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 動画カードをクリア
        self.video_cards.clear()
        
        # 動画一覧を再読み込み
        self.load_videos()
    
    def dragEnterEvent(self, event):
        """ドラッグエンターイベント"""
        if event.mimeData().hasText() and event.mimeData().text().startswith("video:"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """ドラッグ移動イベント"""
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
                    
                    # ドロップ位置からグリッド位置を計算
                    drop_position = event.position().toPoint()
                    target_row, target_col = self.get_grid_position_from_point(drop_position)
                    
                    if target_row != -1 and target_col != -1:
                        self.update_video_order(video_id, target_row, target_col)
                    
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def get_grid_position_from_point(self, point: QPoint) -> tuple:
        """ポイントからグリッド位置を計算"""
        # グリッドのセルサイズを計算（カードサイズ + スペーシング）
        card_width = 250
        card_height = 300
        spacing = 10
        columns = self.current_columns
        
        # グリッドコンテナ内での相対位置を計算
        relative_point = point - self.grid_container.pos()
        
        # グリッドレイアウトのマージンを取得
        margins = self.grid_layout.getContentsMargins()
        margin_x = margins[0]  # 左マージン
        margin_y = margins[1]  # 上マージン
        
        # マージンを引いた位置で計算
        adjusted_x = relative_point.x() - margin_x
        adjusted_y = relative_point.y() - margin_y
        
        # 負の値の場合は0に調整
        if adjusted_x < 0:
            adjusted_x = 0
        if adjusted_y < 0:
            adjusted_y = 0
        
        col = adjusted_x // (card_width + spacing)
        row = adjusted_y // (card_height + spacing)
        
        # 有効な範囲内かチェック
        if 0 <= row < 10 and 0 <= col < columns:  # 最大10行
            return row, col
        else:
            return -1, -1
