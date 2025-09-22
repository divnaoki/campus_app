#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
動画管理用ユーティリティ
"""

import os
import platform
from pathlib import Path
from typing import Optional, Tuple

# PySide6のインポート
try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPixmap, QPainter, QPen, QFont
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

# OpenCVのインポートを安全に行う
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    # OpenCVが利用できない場合は静かに処理
    CV2_AVAILABLE = False
    cv2 = None


def get_user_data_dir(app_name: str) -> Path:
    """プラットフォームに基づいてユーザーデータディレクトリを取得する"""
    system = platform.system()
    home = Path.home()

    if system == "Windows":
        path = Path(os.getenv("LOCALAPPDATA", home)) / app_name
    elif system == "Darwin":  # macOS
        path = home / "Library" / "Application Support" / app_name
    else:  # Linux / その他
        path = home / ".local" / "share" / app_name

    path.mkdir(parents=True, exist_ok=True)
    return path


def get_video_directories() -> Tuple[Path, Path]:
    """動画ファイルとサムネイルファイルのディレクトリパスを取得"""
    app_data_dir = get_user_data_dir("PySide6App")
    video_dir = app_data_dir / "videos" / "video"
    thumbnail_dir = app_data_dir / "videos" / "thumbnail"
    
    # ディレクトリが存在しない場合は作成
    video_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    
    return video_dir, thumbnail_dir


def generate_thumbnail_with_qt(video_path: str, thumbnail_path: str, 
                               frame_time: float = 0.0, 
                               max_size: Tuple[int, int] = (320, 240)) -> bool:
    """
    QMediaPlayerを使用して動画からサムネイル画像を生成する
    
    Args:
        video_path: 動画ファイルのパス
        thumbnail_path: 生成するサムネイル画像のパス
        frame_time: サムネイルを取得する時間（秒）
        max_size: サムネイルの最大サイズ (width, height)
    
    Returns:
        bool: 成功した場合True
    """
    try:
        from PySide6.QtMultimedia import QMediaPlayer, QVideoSink
        from PySide6.QtCore import QUrl, QTimer, QEventLoop, QCoreApplication
        from PySide6.QtGui import QImage, QPixmap
        
        # アプリケーションインスタンスが必要な場合
        app = QCoreApplication.instance()
        if app is None:
            from PySide6.QtWidgets import QApplication
            app = QApplication([])
        
        # QMediaPlayerを作成
        player = QMediaPlayer()
        video_sink = QVideoSink()
        player.setVideoSink(video_sink)
        
        # 動画ファイルを設定
        player.setSource(QUrl.fromLocalFile(video_path))
        
        # フレームキャプチャ用の変数
        captured_frame = None
        capture_completed = False
        timeout_occurred = False
        
        def on_frame_changed(frame):
            nonlocal captured_frame, capture_completed
            if not capture_completed and not frame.isNull():
                captured_frame = frame
                capture_completed = True
        
        def on_timeout():
            nonlocal timeout_occurred
            timeout_occurred = True
        
        # フレーム変更シグナルを接続
        video_sink.videoFrameChanged.connect(on_frame_changed)
        
        # タイムアウトタイマーを設定
        timer = QTimer()
        timer.timeout.connect(on_timeout)
        timer.setSingleShot(True)
        timer.start(3000)  # 3秒でタイムアウト
        
        # 動画を再生開始（一時的に）
        player.play()
        
        # 指定された時間に移動
        player.setPosition(int(frame_time * 1000))  # ミリ秒に変換
        
        # イベントループでフレームを待機
        loop = QEventLoop()
        
        # タイムアウトまたはフレームキャプチャ完了まで待機
        while not capture_completed and not timeout_occurred:
            loop.processEvents()
            app.processEvents()
        
        # タイマーを停止
        timer.stop()
        
        # プレイヤーを停止
        player.stop()
        
        if captured_frame is None or timeout_occurred:
            # フレームが取得できない場合はプレースホルダーを作成
            return create_placeholder_thumbnail(thumbnail_path, max_size)
        
        # QVideoFrameをQImageに変換
        image = captured_frame.toImage()
        if image.isNull():
            return create_placeholder_thumbnail(thumbnail_path, max_size)
        
        # 画像をリサイズ
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            max_size[0], max_size[1], 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        # 画像を保存
        return scaled_pixmap.save(thumbnail_path)
        
    except Exception as e:
        print(f"QMediaPlayerサムネイル生成エラー: {e}")
        # エラーの場合はプレースホルダーを作成
        return create_placeholder_thumbnail(thumbnail_path, max_size)


def create_placeholder_thumbnail(thumbnail_path: str, max_size: Tuple[int, int] = (320, 240)) -> bool:
    """
    プレースホルダーサムネイル画像を作成する
    
    Args:
        thumbnail_path: 生成するサムネイル画像のパス
        max_size: サムネイルの最大サイズ (width, height)
    
    Returns:
        bool: 成功した場合True
    """
    if not PYSIDE6_AVAILABLE:
        print("PySide6 is not available. Cannot create placeholder thumbnail.")
        return False
    
    try:
        # プレースホルダー画像を作成
        pixmap = QPixmap(max_size[0], max_size[1])
        pixmap.fill(Qt.lightGray)
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.gray, 2))
        painter.drawRect(10, 10, max_size[0] - 20, max_size[1] - 20)
        
        # テキストを描画
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "動画\nサムネイル")
        painter.end()
        
        # 画像を保存
        return pixmap.save(thumbnail_path)
        
    except Exception as e:
        print(f"プレースホルダーサムネイル作成エラー: {e}")
        return False


def generate_thumbnail(video_path: str, thumbnail_path: str, 
                      frame_time: float = 0.0, 
                      max_size: Tuple[int, int] = (320, 240)) -> bool:
    """
    動画からサムネイル画像を生成する
    
    Args:
        video_path: 動画ファイルのパス
        thumbnail_path: 生成するサムネイル画像のパス
        frame_time: サムネイルを取得する時間（秒）
        max_size: サムネイルの最大サイズ (width, height)
    
    Returns:
        bool: 成功した場合True
    """
    if not CV2_AVAILABLE:
        # OpenCVが利用できない場合はQMediaPlayerを使用
        return generate_thumbnail_with_qt(video_path, thumbnail_path, frame_time, max_size)
    
    try:
        # 動画ファイルを開く
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"動画ファイルを開けませんでした: {video_path}")
            return False
        
        # 指定された時間のフレームに移動
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(frame_time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # フレームを読み取り
        ret, frame = cap.read()
        
        if not ret:
            print(f"フレームを読み取れませんでした: {video_path}")
            cap.release()
            return False
        
        # フレームをリサイズ（アスペクト比を保持）
        height, width = frame.shape[:2]
        max_width, max_height = max_size
        
        # アスペクト比を計算
        aspect_ratio = width / height
        
        if width > max_width or height > max_height:
            if aspect_ratio > max_width / max_height:
                # 幅が制限を超えている場合
                new_width = max_width
                new_height = int(new_width / aspect_ratio)
            else:
                # 高さが制限を超えている場合
                new_height = max_height
                new_width = int(new_height * aspect_ratio)
            
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # サムネイルを保存
        success = cv2.imwrite(thumbnail_path, frame)
        
        cap.release()
        
        if success:
            print(f"サムネイルを生成しました: {thumbnail_path}")
            return True
        else:
            print(f"サムネイルの保存に失敗しました: {thumbnail_path}")
            return False
            
    except Exception as e:
        print(f"サムネイル生成中にエラーが発生しました: {e}")
        return False


def get_video_info(video_path: str) -> Optional[dict]:
    """
    動画ファイルの情報を取得する
    
    Args:
        video_path: 動画ファイルのパス
    
    Returns:
        dict: 動画情報（fps, duration, width, height等）またはNone
    """
    if not CV2_AVAILABLE:
        # デフォルトの動画情報を返す
        return {
            'fps': 30.0,
            'duration': 10.0,  # デフォルト10秒
            'width': 640,
            'height': 480,
            'frame_count': 300
        }
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return None
        
        # 動画の基本情報を取得
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            'fps': fps,
            'frame_count': frame_count,
            'width': width,
            'height': height,
            'duration': duration
        }
        
    except Exception as e:
        print(f"動画情報取得中にエラーが発生しました: {e}")
        return None


def is_video_file(file_path: str) -> bool:
    """
    ファイルが動画ファイルかどうかを判定する
    
    Args:
        file_path: ファイルパス
    
    Returns:
        bool: 動画ファイルの場合True
    """
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
    return Path(file_path).suffix.lower() in video_extensions


def copy_video_file(source_path: str, campus_id: int) -> Optional[str]:
    """
    動画ファイルをvideos/videoディレクトリにコピーする
    
    Args:
        source_path: 元の動画ファイルのパス
        campus_id: キャンパスID
    
    Returns:
        str: コピー先のファイルパスまたはNone
    """
    try:
        import shutil
        
        video_dir, _ = get_video_directories()
        
        # ファイル名を生成（campus_id_元ファイル名）
        source_file = Path(source_path)
        new_filename = f"{campus_id}_{source_file.name}"
        dest_path = video_dir / new_filename
        
        # ファイルをコピー
        shutil.copy2(source_path, dest_path)
        
        return str(dest_path)
        
    except Exception as e:
        print(f"動画ファイルのコピー中にエラーが発生しました: {e}")
        return None
