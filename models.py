#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベースモデル定義
"""

import sqlite3
import os
import platform
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


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


class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self):
        self.app_data_dir = get_user_data_dir("PySide6App")
        self.db_path = self.app_data_dir / "database.db"
    
    def get_connection(self):
        """データベース接続を取得"""
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Tuple]:
        """クエリを実行して結果を取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """更新クエリを実行して影響を受けた行数を取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount


class Campus:
    """キャンパスモデル"""
    
    def __init__(self, id: int = None, name: str = "", type: str = "image", created_at: str = None, updated_at: str = None):
        self.id = id
        self.name = name
        self.type = type  # 'image' または 'video'
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def get_all() -> List['Campus']:
        """すべてのキャンパスを取得"""
        db = DatabaseManager()
        query = "SELECT id, name, type, created_at, updated_at FROM campus ORDER BY created_at DESC"
        results = db.execute_query(query)
        
        campuses = []
        for row in results:
            campus = Campus(
                id=row[0],
                name=row[1],
                type=row[2],
                created_at=row[3],
                updated_at=row[4]
            )
            campuses.append(campus)
        
        return campuses
    
    @staticmethod
    def get_by_id(campus_id: int) -> Optional['Campus']:
        """IDでキャンパスを取得"""
        db = DatabaseManager()
        query = "SELECT id, name, type, created_at, updated_at FROM campus WHERE id = ?"
        results = db.execute_query(query, (campus_id,))
        
        if results:
            row = results[0]
            return Campus(
                id=row[0],
                name=row[1],
                type=row[2],
                created_at=row[3],
                updated_at=row[4]
            )
        return None
    
    def save(self) -> int:
        """キャンパスを保存（新規作成または更新）"""
        db = DatabaseManager()
        
        if self.id is None:
            # 新規作成
            query = "INSERT INTO campus (name, type) VALUES (?, ?)"
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (self.name, self.type))
                conn.commit()
                self.id = cursor.lastrowid
                return self.id
        else:
            # 更新
            query = "UPDATE campus SET name = ?, type = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            db.execute_update(query, (self.name, self.type, self.id))
            return self.id
    
    def delete(self) -> bool:
        """キャンパスを削除"""
        if self.id is None:
            return False
        
        db = DatabaseManager()
        query = "DELETE FROM campus WHERE id = ?"
        affected_rows = db.execute_update(query, (self.id,))
        return affected_rows > 0
    
    def __str__(self):
        return f"Campus(id={self.id}, name='{self.name}', type='{self.type}')"


class Image:
    """画像モデル"""
    
    def __init__(self, id: int = None, campus_id: int = None, name: str = "", 
                 file_data: bytes = b"", sort_order: int = 0,
                 created_at: str = None, updated_at: str = None):
        self.id = id
        self.campus_id = campus_id
        self.name = name
        self.file_data = file_data
        self.sort_order = sort_order
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def get_by_campus_id(campus_id: int) -> List['Image']:
        """キャンパスIDで画像一覧を取得"""
        db = DatabaseManager()
        query = """
            SELECT id, campus_id, name, file_data, sort_order, created_at, updated_at 
            FROM image 
            WHERE campus_id = ? 
            ORDER BY sort_order ASC, created_at DESC
        """
        results = db.execute_query(query, (campus_id,))
        
        images = []
        for row in results:
            image = Image(
                id=row[0],
                campus_id=row[1],
                name=row[2],
                file_data=row[3],
                sort_order=row[4],
                created_at=row[5],
                updated_at=row[6]
            )
            images.append(image)
        
        return images
    
    @staticmethod
    def get_by_id(image_id: int) -> Optional['Image']:
        """IDで画像を取得"""
        db = DatabaseManager()
        query = """
            SELECT id, campus_id, name, file_data, sort_order, created_at, updated_at 
            FROM image 
            WHERE id = ?
        """
        results = db.execute_query(query, (image_id,))
        
        if results:
            row = results[0]
            return Image(
                id=row[0],
                campus_id=row[1],
                name=row[2],
                file_data=row[3],
                sort_order=row[4],
                created_at=row[5],
                updated_at=row[6]
            )
        return None
    
    @staticmethod
    def _get_next_sort_order(db: 'DatabaseManager', campus_id: int) -> int:
        """指定されたキャンパスの次のsort_order値を取得（1-15の範囲内）"""
        query = """
            SELECT COALESCE(MAX(sort_order), 0) + 1 
            FROM image 
            WHERE campus_id = ?
        """
        results = db.execute_query(query, (campus_id,))
        next_order = results[0][0] if results else 1
        
        # 15を超える場合は1から空いている位置を探す
        if next_order > 15:
            for i in range(1, 16):  # 1-15の範囲で空いている位置を探す
                check_query = "SELECT COUNT(*) FROM image WHERE campus_id = ? AND sort_order = ?"
                count_results = db.execute_query(check_query, (campus_id, i))
                if count_results[0][0] == 0:  # 空いている位置
                    return i
            # すべて埋まっている場合は1を返す（既存の画像を上書き）
            return 1
        
        return next_order
    
    def save(self) -> int:
        """画像を保存（新規作成または更新）"""
        db = DatabaseManager()
        
        if self.id is None:
            # 新規作成時、sort_orderが指定されていない場合は最大値+1を設定
            if self.sort_order == 0:
                self.sort_order = self._get_next_sort_order(db, self.campus_id)
            
            # sort_orderの範囲チェック
            if not (1 <= self.sort_order <= 15):
                raise ValueError(f"sort_order must be between 1 and 15, got {self.sort_order}")
            
            query = """
                INSERT INTO image (campus_id, name, file_data, sort_order) 
                VALUES (?, ?, ?, ?)
            """
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (self.campus_id, self.name, self.file_data, 
                                     self.sort_order))
                conn.commit()
                self.id = cursor.lastrowid
                return self.id
        else:
            # 更新
            # sort_orderの範囲チェック
            if not (1 <= self.sort_order <= 15):
                raise ValueError(f"sort_order must be between 1 and 15, got {self.sort_order}")
            
            query = """
                UPDATE image SET name = ?, file_data = ?, sort_order = ?, 
                                updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """
            db.execute_update(query, (self.name, self.file_data, self.sort_order, self.id))
            return self.id
    
    def delete(self) -> bool:
        """画像を削除"""
        if self.id is None:
            return False
        
        db = DatabaseManager()
        query = "DELETE FROM image WHERE id = ?"
        affected_rows = db.execute_update(query, (self.id,))
        return affected_rows > 0
    
    def __str__(self):
        return f"Image(id={self.id}, campus_id={self.campus_id}, name='{self.name}')"


class Video:
    """動画モデル"""
    
    def __init__(self, id: int = None, campus_id: int = None, file_path: str = "", 
                 thumbnail_path: str = "", sort_order: int = 0,
                 created_at: str = None, updated_at: str = None):
        self.id = id
        self.campus_id = campus_id
        self.file_path = file_path
        self.thumbnail_path = thumbnail_path
        self.sort_order = sort_order
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def get_by_campus_id(campus_id: int) -> List['Video']:
        """キャンパスIDで動画一覧を取得"""
        db = DatabaseManager()
        query = """
            SELECT id, file_path, thumbnail_path, sort_order, created_at, updated_at, campus_id 
            FROM video 
            WHERE campus_id = ? 
            ORDER BY sort_order ASC, created_at DESC
        """
        results = db.execute_query(query, (campus_id,))
        
        videos = []
        for row in results:
            video = Video(
                id=row[0],
                file_path=row[1],
                thumbnail_path=row[2],
                sort_order=row[3],
                created_at=row[4],
                updated_at=row[5],
                campus_id=row[6]
            )
            videos.append(video)
        
        return videos
    
    @staticmethod
    def get_by_id(video_id: int) -> Optional['Video']:
        """IDで動画を取得"""
        db = DatabaseManager()
        query = """
            SELECT id, file_path, thumbnail_path, sort_order, created_at, updated_at, campus_id 
            FROM video 
            WHERE id = ?
        """
        results = db.execute_query(query, (video_id,))
        
        if results:
            row = results[0]
            return Video(
                id=row[0],
                file_path=row[1],
                thumbnail_path=row[2],
                sort_order=row[3],
                created_at=row[4],
                updated_at=row[5],
                campus_id=row[6]
            )
        return None
    
    @staticmethod
    def _get_next_sort_order(db: 'DatabaseManager', campus_id: int) -> int:
        """指定されたキャンパスの次のsort_order値を取得"""
        query = """
            SELECT COALESCE(MAX(sort_order), 0) + 1 
            FROM video 
            WHERE campus_id = ?
        """
        results = db.execute_query(query, (campus_id,))
        return results[0][0] if results else 1
    
    def save(self) -> int:
        """動画を保存（新規作成または更新）"""
        db = DatabaseManager()
        
        if self.id is None:
            # 新規作成時、sort_orderが指定されていない場合は最大値+1を設定
            if self.sort_order == 0:
                self.sort_order = self._get_next_sort_order(db, self.campus_id)
            
            query = """
                INSERT INTO video (campus_id, file_path, thumbnail_path, sort_order) 
                VALUES (?, ?, ?, ?)
            """
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (self.campus_id, self.file_path, self.thumbnail_path, 
                                     self.sort_order))
                conn.commit()
                self.id = cursor.lastrowid
                return self.id
        else:
            # 更新
            query = """
                UPDATE video SET file_path = ?, thumbnail_path = ?, sort_order = ?, 
                                updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """
            db.execute_update(query, (self.file_path, self.thumbnail_path, self.sort_order, self.id))
            return self.id
    
    def delete(self) -> bool:
        """動画を削除"""
        if self.id is None:
            return False
        
        db = DatabaseManager()
        query = "DELETE FROM video WHERE id = ?"
        affected_rows = db.execute_update(query, (self.id,))
        return affected_rows > 0
    
    def __str__(self):
        return f"Video(id={self.id}, campus_id={self.campus_id}, file_path='{self.file_path}')"
