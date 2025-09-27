#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画像詳細画面（自動読み上げ機能付き）
"""

import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QFont, QPixmap, QPainter, QPen
import qtawesome as qta

from models import Image, Campus


class TextToSpeechThread(QThread):
    """テキスト読み上げ用のスレッド（クロスプラットフォーム対応）"""
    
    speech_completed = Signal()
    speech_error = Signal(str)
    
    def __init__(self, text, rate=200, volume=0.8, voice=None):
        super().__init__()
        self.text = text
        self.rate = rate
        self.volume = volume
        self.voice = voice
    
    def run(self):
        """テキスト読み上げを実行"""
        try:
            import pyttsx3
            import platform
            
            # pyttsx3エンジンを初期化
            engine = pyttsx3.init()
            
            # 音声設定
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            
            # 音声の選択（プラットフォーム別）
            voices = engine.getProperty('voices')
            if voices and self.voice:
                # 指定された音声を検索
                for voice in voices:
                    if self.voice.lower() in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
            elif voices:
                # デフォルト音声を設定（プラットフォーム別）
                system = platform.system()
                if system == "Windows":
                    # Windows用の日本語音声を優先
                    for voice in voices:
                        if 'japanese' in voice.name.lower() or 'japan' in voice.name.lower():
                            engine.setProperty('voice', voice.id)
                            break
                elif system == "Darwin":  # macOS
                    # macOS用の日本語音声を優先
                    for voice in voices:
                        if 'kyoko' in voice.name.lower() or 'japanese' in voice.name.lower():
                            engine.setProperty('voice', voice.id)
                            break
            
            # テキストを読み上げ
            engine.say(self.text)
            engine.runAndWait()
            
            self.speech_completed.emit()
            
        except Exception as e:
            self.speech_error.emit(f"読み上げ中にエラーが発生しました: {e}")


class ImageDetailWidget(QWidget):
    """画像詳細画面ウィジェット"""
    
    # シグナル定義
    back_to_index_requested = Signal()  # 画像一覧に戻る要求
    image_edit_requested = Signal(int)  # 画像編集画面への遷移要求（image_id）
    
    def __init__(self, image_id: int):
        super().__init__()
        self.image_id = image_id
        self.image = None
        self.campus = None
        self.speech_thread = None
        self.is_speaking = False
        self.setup_ui()
        self.load_image_info()
        # 画像読み込み後に自動読み上げを開始
        QTimer.singleShot(500, self.start_auto_speech)
    
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
        self.title_label = QLabel("画像詳細")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #1F2937;")
        
        header_layout.addWidget(back_button)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        # メインコンテンツエリア（画像表示）
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        
        # 画像表示エリア
        image_frame = QFrame()
        image_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        image_layout = QVBoxLayout()
        image_layout.setSpacing(15)
        
        # 画像表示（大きく表示）
        self.image_display = QLabel()
        self.image_display.setMinimumSize(800, 600)
        self.image_display.setStyleSheet("""
            QLabel {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        self.image_display.setAlignment(Qt.AlignCenter)
        self.image_display.setScaledContents(False)  # 手動でスケーリングするため無効化
        
        # 画像名表示
        self.image_name_label = QLabel()
        self.image_name_label.setStyleSheet("""
            QLabel {
                color: #1F2937;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                text-align: center;
            }
        """)
        self.image_name_label.setAlignment(Qt.AlignCenter)
        self.image_name_label.setWordWrap(True)
        
        image_layout.addWidget(self.image_display)
        image_layout.addWidget(self.image_name_label)
        
        image_frame.setLayout(image_layout)
        
        # メインレイアウトに追加
        main_layout.addLayout(header_layout)
        main_layout.addLayout(content_layout)
        main_layout.addWidget(image_frame)
        
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
                self.title_label.setText(f"画像詳細 - {self.campus.name}")
            
            # 画像を表示
            self.load_image_display()
            
            # 画像名を表示
            self.image_name_label.setText(self.image.name)
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"画像情報の読み込みに失敗しました:\n{str(e)}")
    
    def load_image_display(self):
        """画像表示を読み込み"""
        try:
            if self.image.file_data and len(self.image.file_data) > 0:
                pixmap = QPixmap()
                if pixmap.loadFromData(self.image.file_data):
                    # アスペクト比を保ってリサイズ（より高品質なスケーリング）
                    self.set_scaled_pixmap(pixmap)
                else:
                    self.set_placeholder_image()
            else:
                self.set_placeholder_image()
        except Exception as e:
            print(f"画像表示読み込みエラー: {e}")
            self.set_placeholder_image()
    
    def set_scaled_pixmap(self, pixmap):
        """アスペクト比を保って画像をスケールして表示"""
        if pixmap.isNull():
            return
        
        # 表示エリアのサイズを取得
        display_size = self.image_display.size()
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
        
        self.image_display.setPixmap(final_pixmap)
    
    def set_placeholder_image(self):
        """プレースホルダー画像を設定"""
        pixmap = QPixmap(800, 600)
        pixmap.fill(Qt.lightGray)
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.gray, 2))
        painter.drawRect(10, 10, 780, 580)
        painter.drawText(400, 300, "No Image")
        painter.end()
        
        self.image_display.setPixmap(pixmap)
    
    def start_auto_speech(self):
        """自動読み上げを開始"""
        if self.image:
            # 画像名を読み上げ
            text = f"{self.image.name}"
            
            try:
                # 読み上げスレッドを開始（プラットフォーム別の音声設定）
                import platform
                system = platform.system()
                
                if system == "Windows":
                    # Windows用の音声設定
                    self.speech_thread = TextToSpeechThread(text, rate=200, volume=0.8, voice='Microsoft')
                elif system == "Darwin":  # macOS
                    # macOS用の音声設定
                    self.speech_thread = TextToSpeechThread(text, rate=200, volume=0.8, voice='Kyoko')
                else:
                    # その他のプラットフォーム
                    self.speech_thread = TextToSpeechThread(text, rate=200, volume=0.8)
                
                self.speech_thread.speech_completed.connect(self.on_auto_speech_completed)
                self.speech_thread.speech_error.connect(self.on_auto_speech_error)
                self.speech_thread.start()
                
                # UIを更新
                self.is_speaking = True
                
            except Exception as e:
                print(f"自動読み上げエラー: {e}")
                # エラーが発生しても自動的に前のページに戻る
                QTimer.singleShot(1000, self.back_to_index_requested.emit)
    
    def on_auto_speech_completed(self):
        """自動読み上げ完了時の処理"""
        self.is_speaking = False
        # 読み上げ完了後に3秒待ってから前のページに戻る
        QTimer.singleShot(3000, self.back_to_index_requested.emit)
    
    def on_auto_speech_error(self, error_message):
        """自動読み上げエラー時の処理"""
        self.is_speaking = False
        print(f"自動読み上げエラー: {error_message}")
        # エラーが発生しても自動的に前のページに戻る
        QTimer.singleShot(1000, self.back_to_index_requested.emit)
    
    def refresh(self):
        """画面をリフレッシュ"""
        self.load_image_info()
