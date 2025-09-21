#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画像一覧画面（シンプル版）
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QGridLayout,
    QMessageBox, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
from PySide6.QtGui import QFont, QPixmap, QPainter, QPen, QDrag, QPainterPath
import qtawesome as qta
from typing import Optional

from models import Image, Campus


class ImageCard(QFrame):
    """画像カードウィジェット（ドラッグ&ドロップ対応版）"""
    
    # シグナル定義
    image_clicked = Signal(int)
    image_dragged = Signal(int, int, int)  # image_id, from_row, from_col
    image_dropped = Signal(int, int, int)  # image_id, to_row, to_col
    
    def __init__(self, image: Image, row: int = 0, col: int = 0):
        super().__init__()
        self.image = image
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
            self.drag_start_position = event.position().toPoint()
            
            # 位置修正モードかどうかを確認
            position_edit_mode = False
            if self.position_edit_mode_ref:
                position_edit_mode = self.position_edit_mode_ref()
            else:
                # フォールバック: 親ウィジェットを辿って確認
                widget = self.parent()
                while widget:
                    if hasattr(widget, 'position_edit_mode'):
                        position_edit_mode = widget.position_edit_mode
                        break
                    widget = widget.parent()
            
            # 位置修正モードの場合はクリック処理を無効化
            if position_edit_mode:
                return
            # 位置修正モードでない場合は通常のクリック処理
            self.image_clicked.emit(self.image.id)
    
    def mouseMoveEvent(self, event):
        """マウス移動イベント（ドラッグ処理）"""
        if not event.buttons() == Qt.LeftButton:
            return
        
        # 位置修正モードかどうかを確認
        position_edit_mode = False
        if self.position_edit_mode_ref:
            position_edit_mode = self.position_edit_mode_ref()
        else:
            # フォールバック: 親ウィジェットを辿って確認
            widget = self.parent()
            while widget:
                if hasattr(widget, 'position_edit_mode'):
                    position_edit_mode = widget.position_edit_mode
                    break
                widget = widget.parent()
        
        if not position_edit_mode:
            return
        
        distance = (event.position().toPoint() - self.drag_start_position).manhattanLength()
        min_distance = QApplication.startDragDistance()
        
        if distance < min_distance:
            return
        
        # ドラッグ開始
        self.start_drag()
    
    def start_drag(self):
        """ドラッグを開始"""
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"image_{self.image.id}_{self.row}_{self.col}")
        drag.setMimeData(mime_data)
        
        # ドラッグ中の画像を半透明に
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                margin: 5px;
                opacity: 0.7;
            }
        """)
        
        # ドラッグ実行
        result = drag.exec(Qt.MoveAction)
        
        # ドラッグ終了後、スタイルを元に戻す
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                margin: 5px;
            }
        """)
    
    def update_position(self, row: int, col: int):
        """カードの位置を更新"""
        self.row = row
        self.col = col


class DropZone(QFrame):
    """配置可能エリアを表示するウィジェット"""
    
    def __init__(self, row: int, col: int):
        super().__init__()
        self.row = row
        self.col = col
        self.setFixedSize(250, 300)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(34, 197, 94, 0.3);
                border: 2px dashed #22C55E;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        self.hide()  # 初期状態では非表示
    
    def highlight(self):
        """ドロップ先としてハイライト"""
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(34, 197, 94, 0.6);
                border: 3px solid #22C55E;
                border-radius: 8px;
                margin: 5px;
            }
        """)
    
    def unhighlight(self):
        """ハイライトを解除"""
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(34, 197, 94, 0.3);
                border: 2px dashed #22C55E;
                border-radius: 8px;
                margin: 5px;
            }
        """)


class EmptyCell(QFrame):
    """空きセル用のウィジェット"""
    
    def __init__(self, row: int, col: int, sort_order: int):
        super().__init__()
        self.row = row
        self.col = col
        self.sort_order = sort_order
        self.setup_ui()
    
    def setup_ui(self):
        self.setFixedSize(250, 300)
        self.setStyleSheet("""
            QFrame {
                background-color: #F9FAFB;
                border: 2px dashed #D1D5DB;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        # 空きセル表示用のラベル
        label = QLabel("空き")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: #9CA3AF;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)
    
    def highlight(self):
        """ドロップ先としてハイライト"""
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(34, 197, 94, 0.3);
                border: 3px solid #22C55E;
                border-radius: 8px;
                margin: 5px;
            }
        """)
    
    def unhighlight(self):
        """ハイライトを解除"""
        self.setStyleSheet("""
            QFrame {
                background-color: #F9FAFB;
                border: 2px dashed #D1D5DB;
                border-radius: 8px;
                margin: 5px;
            }
        """)


class ImageIndexWidget(QWidget):
    """画像一覧画面ウィジェット（5×3グリッド対応、レスポンシブ対応版）"""
    
    # シグナル定義（main.pyで必要なシグナル）
    back_to_campus_requested = Signal()
    image_create_requested = Signal()
    image_edit_requested = Signal(int)
    image_detail_requested = Signal(int)
    
    def __init__(self, campus_id: int):
        super().__init__()
        self.campus_id = campus_id
        self.images = []
        self.position_edit_mode = False
        self.image_cards = {}  # (row, col) -> ImageCard
        self.empty_cells = {}  # (row, col) -> EmptyCell
        self.drop_zones = {}   # (row, col) -> DropZone
        self.max_cells = 15  # 5×3の最大セル数
        self.current_columns = 3  # 現在の列数を追跡
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
        
        # 位置修正ボタン
        self.position_edit_button = QPushButton("位置修正")
        self.position_edit_button.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.position_edit_button.clicked.connect(self.toggle_position_edit_mode)
        
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
        header_layout.addWidget(self.position_edit_button)
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
    
    def calculate_responsive_columns(self, window_width: int) -> int:
        """ウィンドウ幅に基づいて列数を計算（2-5列の範囲）"""
        card_width = 250
        spacing = 10
        margin = 80  # 左右マージンを大きくして余白を確保
        
        available_width = window_width - margin
        calculated_columns = available_width // (card_width + spacing)
        
        # 2-5列の範囲に制限
        return max(2, min(5, calculated_columns))
    
    def get_max_rows(self, columns: int) -> int:
        """列数に基づいて最大行数を計算（最大15セル）"""
        return self.max_cells // columns + (1 if self.max_cells % columns > 0 else 0)
    
    def resizeEvent(self, event):
        """ウィンドウリサイズ時の処理"""
        super().resizeEvent(event)
        # レスポンシブ対応でグリッドを再描画（sort_orderを保持）
        if hasattr(self, 'images') and self.images:
            self.refresh_layout_only()
    
    def find_image_by_sort_order(self, sort_order: int) -> Optional[Image]:
        """指定されたsort_orderの画像を検索"""
        for image in self.images:
            if image.sort_order == sort_order:
                return image
        return None
    
    def dragEnterEvent(self, event):
        """ドラッグエンターイベント"""
        print(f"[DEBUG] dragEnterEvent: position_edit_mode={self.position_edit_mode}")
        if self.position_edit_mode and event.mimeData().hasText() and event.mimeData().text().startswith("image_"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """ドラッグ移動イベント"""
        if self.position_edit_mode and event.mimeData().hasText() and event.mimeData().text().startswith("image_"):
            # ドロップ先のセルをハイライト
            drop_position = event.position().toPoint()
            target_row, target_col = self.get_grid_position_from_point(drop_position)
            print(f"[DEBUG] dragMoveEvent: target=({target_row}, {target_col})")
            
            # 前のハイライトを解除
            self.clear_highlights()
            
            # 新しいセルをハイライト
            if target_row != -1 and target_col != -1:
                self.highlight_cell(target_row, target_col)
            
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """ドロップイベント"""
        print(f"[DEBUG] dropEvent: position_edit_mode={self.position_edit_mode}")
        
        if not self.position_edit_mode or not event.mimeData().hasText():
            print(f"[DEBUG] dropEvent: 条件を満たさないため無視")
            event.ignore()
            return
        
        text = event.mimeData().text()
        print(f"[DEBUG] dropEvent: mimeData text={text}")
        
        if not text.startswith("image_"):
            print(f"[DEBUG] dropEvent: image_で始まらないため無視")
            event.ignore()
            return
        
        # ドロップ位置からグリッドセルを計算
        drop_position = event.position().toPoint()
        target_row, target_col = self.get_grid_position_from_point(drop_position)
        print(f"[DEBUG] dropEvent: ドロップ位置=({target_row}, {target_col})")
        
        if target_row == -1 or target_col == -1:
            print(f"[DEBUG] dropEvent: 無効な位置のため無視")
            event.ignore()
            return
        
        # ドラッグされた画像の情報を取得
        parts = text.split("_")
        if len(parts) != 4:
            print(f"[DEBUG] dropEvent: 不正な形式のため無視")
            event.ignore()
            return
        
        image_id = int(parts[1])
        from_row = int(parts[2])
        from_col = int(parts[3])
        print(f"[DEBUG] dropEvent: 移動元=({from_row}, {from_col}), 移動先=({target_row}, {target_col})")
        
        # ハイライトを解除
        self.clear_highlights()
        
        # 画像を移動
        self.move_image(from_row, from_col, target_row, target_col)
        event.acceptProposedAction()
    
    def highlight_cell(self, row: int, col: int):
        """指定されたセルをハイライト"""
        print(f"[DEBUG] highlight_cell: ({row}, {col})")
        
        # 画像カードをハイライト
        if (row, col) in self.image_cards:
            # 画像カードのハイライト（現在は実装なし）
            pass
        
        # 空きセルをハイライト
        if (row, col) in self.empty_cells:
            self.empty_cells[(row, col)].highlight()
        
        # ドロップゾーンをハイライト
        if (row, col) in self.drop_zones:
            self.drop_zones[(row, col)].highlight()
    
    def clear_highlights(self):
        """すべてのハイライトを解除"""
        # 空きセルのハイライトを解除
        for empty_cell in self.empty_cells.values():
            empty_cell.unhighlight()
        
        # ドロップゾーンのハイライトを解除
        for drop_zone in self.drop_zones.values():
            drop_zone.unhighlight()
    
    def get_grid_position_from_point(self, point: QPoint) -> tuple:
        """ポイントからグリッド位置を計算（レスポンシブ対応）"""
        # グリッドのセルサイズを計算（カードサイズ + スペーシング）
        card_width = 250
        card_height = 300
        spacing = 10
        columns = self.current_columns  # 現在の列数を使用
        max_rows = self.get_max_rows(columns)
        
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
        
        print(f"[DEBUG] get_grid_position_from_point: point=({point.x()}, {point.y()}), relative=({relative_point.x()}, {relative_point.y()}), margins=({margin_x}, {margin_y}), adjusted=({adjusted_x}, {adjusted_y}), calculated=({row}, {col}), columns={columns}, max_rows={max_rows}")
        print(f"[DEBUG] get_grid_position_from_point: card_size=({card_width}, {card_height}), spacing={spacing}")
        
        # 有効な範囲内かチェック
        if 0 <= row < max_rows and 0 <= col < columns:
            print(f"[DEBUG] get_grid_position_from_point: 有効な位置")
            return row, col
        else:
            print(f"[DEBUG] get_grid_position_from_point: 無効な位置 (row={row}, col={col}, max_rows={max_rows}, columns={columns})")
            return -1, -1
    
    def move_image(self, from_row: int, from_col: int, to_row: int, to_col: int):
        """画像を移動（デバッグログ付き）"""
        print(f"[DEBUG] move_image called: from({from_row}, {from_col}) -> to({to_row}, {to_col})")
        
        # 移動元のカードを取得
        if (from_row, from_col) not in self.image_cards:
            print(f"[DEBUG] 移動元のカードが見つかりません: ({from_row}, {from_col})")
            return
        
        card = self.image_cards[(from_row, from_col)]
        columns = self.current_columns  # 現在の列数を使用
        print(f"[DEBUG] 現在の列数: {columns}")
        
        # sort_orderを計算
        from_sort_order = from_row * columns + from_col + 1
        to_sort_order = to_row * columns + to_col + 1
        print(f"[DEBUG] sort_order計算: from={from_sort_order}, to={to_sort_order}")
        
        try:
            from models import DatabaseManager
            db = DatabaseManager()
            
            # 移動先に既にカードがある場合は入れ替え
            if (to_row, to_col) in self.image_cards:
                print(f"[DEBUG] 入れ替えモード: 移動先に既存のカードがあります")
                target_card = self.image_cards[(to_row, to_col)]
                
                # データベースでsort_orderを入れ替え
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    # 一時的な値を使用して入れ替え
                    cursor.execute("UPDATE image SET sort_order = ? WHERE id = ?", (999999, card.image.id))
                    cursor.execute("UPDATE image SET sort_order = ? WHERE id = ?", (from_sort_order, target_card.image.id))
                    cursor.execute("UPDATE image SET sort_order = ? WHERE id = ?", (to_sort_order, card.image.id))
                    conn.commit()
                
                # UIを更新
                self.grid_layout.removeWidget(card)
                self.grid_layout.removeWidget(target_card)
                self.grid_layout.addWidget(card, to_row, to_col)
                self.grid_layout.addWidget(target_card, from_row, from_col)
                
                # 辞書を更新
                self.image_cards[(to_row, to_col)] = card
                self.image_cards[(from_row, from_col)] = target_card
                card.update_position(to_row, to_col)
                target_card.update_position(from_row, from_col)
                
            else:
                print(f"[DEBUG] 単純移動モード: 移動先は空です")
                # 移動先が空の場合は単純に移動
                # データベースでsort_orderを更新
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE image SET sort_order = ? WHERE id = ?", (to_sort_order, card.image.id))
                    conn.commit()
                
                # UIを更新
                self.grid_layout.removeWidget(card)
                self.grid_layout.addWidget(card, to_row, to_col)
                
                # 辞書を更新
                del self.image_cards[(from_row, from_col)]
                self.image_cards[(to_row, to_col)] = card
                card.update_position(to_row, to_col)
            
            print(f"[DEBUG] 移動完了: 画像一覧を再読み込みします")
            # 画像一覧を再読み込みしてUIを完全に更新
            self.load_images()
            
        except Exception as e:
            print(f"[DEBUG] 画像移動エラー: {e}")
            # エラー時はUIを再描画
            self.display_images()
    
    def update_empty_cells_after_move(self, from_row: int, from_col: int, to_row: int, to_col: int):
        """移動後の空きセルを更新"""
        columns = self.current_columns  # 現在の列数を使用
        
        # 移動元のセルが空きセルになる場合
        if (from_row, from_col) not in self.image_cards:
            from_sort_order = from_row * columns + from_col + 1
            # 既存の空きセルを削除
            if (from_row, from_col) in self.empty_cells:
                self.empty_cells[(from_row, from_col)].deleteLater()
                del self.empty_cells[(from_row, from_col)]
            
            # 新しい空きセルを作成
            empty_cell = EmptyCell(from_row, from_col, from_sort_order)
            self.grid_layout.addWidget(empty_cell, from_row, from_col)
            self.empty_cells[(from_row, from_col)] = empty_cell
        
        # 移動先のセルから空きセルを削除
        if (to_row, to_col) in self.empty_cells:
            self.empty_cells[(to_row, to_col)].deleteLater()
            del self.empty_cells[(to_row, to_col)]
    
    def update_sort_orders(self):
        """データベースのsort_orderを更新（レスポンシブ対応）
        注意: 個別の移動操作では move_image で直接更新するため、このメソッドは使用されません
        """
        try:
            from models import DatabaseManager
            db = DatabaseManager()
            
            # 現在のグリッド配置に基づいてsort_orderを更新
            columns = self.calculate_responsive_columns(self.width())
            for (row, col), card in self.image_cards.items():
                sort_order = row * columns + col + 1  # レスポンシブ列数での順序
                query = "UPDATE image SET sort_order = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                db.execute_update(query, (sort_order, card.image.id))
        except Exception as e:
            print(f"sort_order更新エラー: {e}")
    
    def toggle_position_edit_mode(self):
        """位置修正モードの切り替え"""
        self.position_edit_mode = not self.position_edit_mode
        
        if self.position_edit_mode:
            self.position_edit_button.setText("位置修正終了")
            self.position_edit_button.setStyleSheet("""
                QPushButton {
                    background-color: #EF4444;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                }
            """)
            self.show_drop_zones()
        else:
            self.position_edit_button.setText("位置修正")
            self.position_edit_button.setStyleSheet("""
                QPushButton {
                    background-color: #10B981;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
            """)
            self.hide_drop_zones()
    
    def show_drop_zones(self):
        """配置可能エリアを表示（既存の画像があるセルは除外、レスポンシブ対応）"""
        # 既存のドロップゾーンをクリア
        for drop_zone in self.drop_zones.values():
            drop_zone.deleteLater()
        self.drop_zones.clear()
        
        # レスポンシブ対応で列数と行数を計算
        columns = self.current_columns  # 現在の列数を使用
        max_rows = self.get_max_rows(columns)
        
        for row in range(max_rows):
            for col in range(columns):
                # 既存の画像がないセルのみにドロップゾーンを配置
                if (row, col) not in self.image_cards and (row, col) not in self.empty_cells:
                    drop_zone = DropZone(row, col)
                    self.grid_layout.addWidget(drop_zone, row, col)
                    self.drop_zones[(row, col)] = drop_zone
                    drop_zone.show()
    
    def hide_drop_zones(self):
        """配置可能エリアを非表示"""
        for drop_zone in self.drop_zones.values():
            drop_zone.hide()
    
    def load_images(self):
        """画像一覧を読み込み"""
        try:
            self.images = Image.get_by_campus_id(self.campus_id)
            self.display_images()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"画像の読み込みに失敗しました:\n{str(e)}")
    
    def display_images(self):
        """画像をグリッドに表示（5×3グリッド対応、空きセル表示、レスポンシブ対応）"""
        # グリッドレイアウトをクリア
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 辞書もクリア
        self.image_cards.clear()
        self.empty_cells.clear()
        self.drop_zones.clear()
        
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
        
        # レスポンシブ対応で列数を計算
        columns = self.calculate_responsive_columns(self.width())
        self.current_columns = columns  # 現在の列数を更新
        max_rows = self.get_max_rows(columns)
        
        # グリッドコンテナの最小幅を設定（中央揃えのため）
        card_width = 250
        spacing = 10
        min_width = columns * (card_width + spacing) - spacing + 40  # 40はマージン
        self.grid_container.setMinimumWidth(min_width)
        
        # 全セル（1-15）をチェックして画像または空きセルを配置
        for sort_order in range(1, self.max_cells + 1):
            row = (sort_order - 1) // columns
            col = (sort_order - 1) % columns
            
            # 最大行数を超える場合はスキップ
            if row >= max_rows:
                continue
            
            # 該当するsort_orderの画像を検索
            image = self.find_image_by_sort_order(sort_order)
            
            if image:
                # 画像カードを配置
                card = ImageCard(image, row, col)
                card.image_clicked.connect(self.image_detail_requested.emit)
                # 位置修正モードの参照を設定
                card.position_edit_mode_ref = lambda: self.position_edit_mode
                self.grid_layout.addWidget(card, row, col)
                self.image_cards[(row, col)] = card
            else:
                # 空きセルを配置
                empty_cell = EmptyCell(row, col, sort_order)
                self.grid_layout.addWidget(empty_cell, row, col)
                self.empty_cells[(row, col)] = empty_cell
    
    def refresh_layout_only(self):
        """レイアウトのみを更新（sort_orderを保持）"""
        print(f"[DEBUG] refresh_layout_only: 列数変更時のレイアウト更新")
        
        # 現在の列数を取得
        old_columns = 3  # デフォルト値
        if hasattr(self, 'current_columns'):
            old_columns = self.current_columns
        
        new_columns = self.calculate_responsive_columns(self.width())
        print(f"[DEBUG] refresh_layout_only: 旧列数={old_columns}, 新列数={new_columns}")
        
        # 列数が変わらない場合は何もしない
        if old_columns == new_columns:
            print(f"[DEBUG] refresh_layout_only: 列数が同じためスキップ")
            return
        
        # 現在の列数を更新
        self.current_columns = new_columns
        
        # グリッドレイアウトをクリア
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 辞書をクリア
        self.image_cards.clear()
        self.empty_cells.clear()
        self.drop_zones.clear()
        
        # 新しい列数でレイアウトを再構築
        self.display_images()
    
    def refresh(self):
        """画像一覧を再読み込み"""
        self.load_images()