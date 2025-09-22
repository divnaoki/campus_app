#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
動画詳細・再生画面
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QMessageBox, QSlider
)
from PySide6.QtCore import Qt, Signal, QTimer, QUrl
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import qtawesome as qta
import os
import numpy as np
from pathlib import Path

# OpenCVのインポートを安全に行う
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    # OpenCVが利用できない場合は静かに処理
    CV2_AVAILABLE = False
    cv2 = None

from models import Video, Campus
from video_utils import get_video_info


class VideoPlayerWidget(QWidget):
    """動画プレイヤーウィジェット"""
    
    def __init__(self, video: Video):
        super().__init__()
        self.video = video
        self.is_playing = False
        self.current_position = 0
        self.duration = 0
        self.cap = None
        self.fps = 30
        self.timer = None
        self.is_seeking = False  # シーク中かどうかのフラグ
        self.last_audio_position = 0  # 最後の音声位置を記録
        
        # 音声プレイヤーを初期化
        self.audio_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_player.setAudioOutput(self.audio_output)
        
        # 音声プレイヤーのシグナルを接続
        self.audio_player.positionChanged.connect(self.on_audio_position_changed)
        self.audio_player.mediaStatusChanged.connect(self.on_media_status_changed)
        
        self.setup_ui()
        self.load_video_info()
    
    def setup_ui(self):
        """UIをセットアップ"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)  # スペーシングを小さく
        
        # ヘッダー部分
        header_layout = QHBoxLayout()
        
        # 一覧に戻るボタン
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
        back_button.clicked.connect(self.go_back)
        
        # タイトル
        filename = os.path.basename(self.video.file_path) if self.video.file_path else "動画ファイル"
        title_label = QLabel(filename)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1F2937;
            }
        """)
        
        header_layout.addWidget(back_button)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # 動画表示エリア（サムネイルを表示）
        self.video_display = QLabel()
        self.video_display.setMinimumSize(800, 450)
        self.video_display.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        self.video_display.setAlignment(Qt.AlignCenter)
        self.video_display.setScaledContents(True)
        
        # サムネイルを読み込み
        self.load_thumbnail()
        
        # コントロールエリア
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10)
        
        # シークバー
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #E5E7EB;
                height: 8px;
                background: #F3F4F6;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3B82F6;
                border: 1px solid #3B82F6;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #3B82F6;
                border-radius: 4px;
            }
        """)
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        self.progress_slider.valueChanged.connect(self.on_slider_value_changed)
        
        # 再生/停止ボタン
        self.play_button = QPushButton()
        self.play_button.setIcon(qta.icon('fa5s.play', color='white'))
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 30px;
                padding: 15px 30px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        self.play_button.clicked.connect(self.toggle_play)
        
        # コントロールレイアウトに追加
        controls_layout.addWidget(self.progress_slider)
        controls_layout.addWidget(self.play_button, 0, Qt.AlignCenter)
        
        # メインレイアウトに追加
        layout.addLayout(header_layout)
        layout.addWidget(self.video_display)
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
    
    def load_thumbnail(self):
        """サムネイルを読み込み"""
        try:
            if self.video.thumbnail_path and os.path.exists(self.video.thumbnail_path):
                pixmap = QPixmap(self.video.thumbnail_path)
                if not pixmap.isNull():
                    # アスペクト比を保ってリサイズ
                    scaled_pixmap = pixmap.scaled(
                        self.video_display.size(), 
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    self.video_display.setPixmap(scaled_pixmap)
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
        pixmap = icon.pixmap(128, 128)
        self.video_display.setPixmap(pixmap)
    
    def load_video_info(self):
        """動画情報を読み込み"""
        if not CV2_AVAILABLE:
            # OpenCVが利用できない場合は音声のみで再生
            self.duration = 10.0  # デフォルト10秒
            self.fps = 30.0
            
            # シークバーの最大値を設定
            self.progress_slider.setMaximum(100)
            
            # 音声プレイヤーに動画ファイルを設定
            self.audio_player.setSource(QUrl.fromLocalFile(self.video.file_path))
            
            # 自動再生を開始
            self.play_video()
            return
            
        try:
            if self.video.file_path and os.path.exists(self.video.file_path):
                # 動画ファイルを開く
                self.cap = cv2.VideoCapture(self.video.file_path)
                if self.cap.isOpened():
                    # 動画情報を取得
                    info = get_video_info(self.video.file_path)
                    if info:
                        # 再生時間を取得
                        duration = info['duration']
                        self.duration = duration
                        self.fps = info['fps']
                        
                        # シークバーの最大値を設定（100%を100として設定）
                        self.progress_slider.setMaximum(100)
                        
                        # 音声プレイヤーに動画ファイルを設定
                        self.audio_player.setSource(QUrl.fromLocalFile(self.video.file_path))
                        
                        # 自動再生を開始
                        self.play_video()
                else:
                    print("動画ファイルを開けませんでした")
                
        except Exception as e:
            print(f"動画情報読み込みエラー: {e}")
    
    def on_audio_position_changed(self, position):
        """音声の位置が変更された時の処理"""
        if not self.is_seeking and self.duration > 0:
            # シーク中でない場合のみプログレスバーを更新
            # positionはミリ秒、durationは秒なので、正しく計算
            progress = int((position / (self.duration * 1000)) * 100)
            self.progress_slider.setValue(progress)
            self.current_position = position / 1000.0
            self.last_audio_position = position
    
    def on_media_status_changed(self, status):
        """メディアの状態が変更された時の処理"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # 動画終了時
            self.pause_video()
            # 最初に戻す
            self.audio_player.setPosition(0)
            if self.cap:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            # 動画終了後に自動で動画一覧ページに移動
            QTimer.singleShot(1000, self.go_back)
    
    def toggle_play(self):
        """再生/停止を切り替え"""
        if self.is_playing:
            self.pause_video()
        else:
            self.play_video()
    
    def play_video(self):
        """動画を再生"""
        if not self.cap or not self.cap.isOpened():
            QMessageBox.warning(self, "エラー", "動画ファイルを開けませんでした。")
            return
        
        self.is_playing = True
        self.play_button.setIcon(qta.icon('fa5s.pause', color='white'))
        self.play_button.setText("")
        
        # 音声を再生
        self.audio_player.play()
        
        # 動画フレームを更新するタイマーを開始
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(int(1000 / self.fps))  # FPSに基づいて更新間隔を設定
    
    def pause_video(self):
        """動画を一時停止"""
        self.is_playing = False
        self.play_button.setIcon(qta.icon('fa5s.play', color='white'))
        self.play_button.setText("")
        
        # 音声を一時停止
        self.audio_player.pause()
        
        if hasattr(self, 'timer'):
            self.timer.stop()
    
    def update_frame(self):
        """動画フレームを更新"""
        if not self.is_playing:
            return
        
        # OpenCVが利用できない場合は音声のみで再生
        if not CV2_AVAILABLE:
            # 音声の位置に基づいてシークバーを更新
            if not self.is_seeking and self.duration > 0:
                current_audio_pos = self.audio_player.position()  # ミリ秒
                if current_audio_pos > 0:
                    progress = int((current_audio_pos / (self.duration * 1000)) * 100)
                    self.progress_slider.setValue(progress)
            return
        
        if not self.cap or not self.cap.isOpened():
            return
        
        # 音声の位置に基づいて動画フレームを同期
        if not self.is_seeking and self.duration > 0:
            current_audio_pos = self.audio_player.position()  # ミリ秒
            if current_audio_pos > 0:
                # 音声の位置に基づいて動画フレームを設定
                progress = current_audio_pos / (self.duration * 1000)
                total_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
                target_frame = int(progress * total_frames)
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        
        ret, frame = self.cap.read()
        if not ret:
            # 動画の終了
            self.pause_video()
            return
        
        # OpenCVのBGRからRGBに変換
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # フレームをリサイズ
        height, width, channel = frame_rgb.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        
        # QPixmapに変換して表示
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.video_display.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.video_display.setPixmap(scaled_pixmap)
    
    def on_slider_pressed(self):
        """スライダーが押された時"""
        self.is_seeking = True
        if hasattr(self, 'timer'):
            self.timer.stop()
        # 音声も一時停止
        self.audio_player.pause()
    
    def on_slider_value_changed(self, value):
        """スライダーの値が変更された時（ドラッグ中）"""
        if self.is_seeking and self.cap and self.cap.isOpened() and self.duration > 0:
            # スライダーの位置に基づいてフレーム位置を設定
            progress = value / 100.0
            total_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            target_frame = int(progress * total_frames)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            
            # 音声の位置も同期（ミリ秒単位）
            audio_position = int(progress * self.duration * 1000)
            self.audio_player.setPosition(audio_position)
            
            self.current_position = progress * self.duration
            self.last_audio_position = audio_position
    
    def on_slider_released(self):
        """スライダーが離された時"""
        self.is_seeking = False
        
        # 再生中の場合のみ再開
        if self.is_playing:
            if hasattr(self, 'timer'):
                self.timer.start(int(1000 / self.fps))
            # 音声も再開
            self.audio_player.play()
    
    def go_back(self):
        """一覧に戻る"""
        self.cleanup_resources()
        # 親ウィジェット（VideoDetailWidget）のgo_backを呼び出し
        if hasattr(self.parent(), 'go_back'):
            self.parent().go_back()
    
    def closeEvent(self, event):
        """ウィジェットが閉じられる時の処理"""
        self.cleanup_resources()
        if event:
            event.accept()
    
    def cleanup_resources(self):
        """リソースをクリーンアップ"""
        # タイマーを停止
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()
            self.timer = None
        
        # 動画キャプチャを解放
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # 音声プレイヤーを停止
        if hasattr(self, 'audio_player') and self.audio_player:
            self.audio_player.stop()
            self.audio_player.setSource(QUrl())
        
        # 再生状態をリセット
        self.is_playing = False
        self.is_seeking = False


class VideoDetailWidget(QWidget):
    """動画詳細ウィジェット"""
    
    # シグナル定義
    back_requested = Signal()
    back_to_index_requested = Signal()
    video_edit_requested = Signal(int)
    video_index_requested = Signal(int)  # campus_idが必要
    
    def __init__(self, video_id: int):
        super().__init__()
        self.video_id = video_id
        self.video = Video.get_by_id(video_id)
        self.campus_id = self.video.campus_id if self.video else None
        self.setup_ui()
    
    def setup_ui(self):
        """UIをセットアップ"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        if self.video:
            self.player_widget = VideoPlayerWidget(self.video)
            layout.addWidget(self.player_widget)
        else:
            # 動画が見つからない場合
            error_label = QLabel("動画が見つかりません")
            error_label.setStyleSheet("""
                QLabel {
                    color: #EF4444;
                    font-size: 18px;
                    font-weight: bold;
                }
            """)
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setMinimumHeight(200)
            layout.addWidget(error_label)
        
        self.setLayout(layout)
    
    def go_back(self):
        """一覧に戻る"""
        if self.campus_id:
            self.video_index_requested.emit(self.campus_id)
        else:
            self.back_to_index_requested.emit()
