#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLiteデータベース作成スクリプト
"""

import sqlite3
import os
import platform
from datetime import datetime
from pathlib import Path


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


def create_database():
    """データベースとテーブルを作成する"""
    
    # プラットフォームに基づいてデータベースファイルのパスを取得
    app_data_dir = get_user_data_dir("PySide6App")
    db_path = app_data_dir / "database.db"
    
    print(f"データベースファイルの配置先: {db_path}")
    
    # データベース接続
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # campusテーブルを作成
        cursor.execute('''
            CREATE TABLE campus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('image', 'video')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("campusテーブルを作成しました。")
        
        # imageテーブルを作成
        cursor.execute('''
            CREATE TABLE image (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                file_data BLOB NOT NULL,
                sort_order INTEGER NOT NULL CHECK (sort_order >= 1 AND sort_order <= 15),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                campus_id INTEGER,
                FOREIGN KEY (campus_id) REFERENCES campus(id),
                UNIQUE(campus_id, sort_order)
            )
        ''')
        print("imageテーブルを作成しました。")
        
        # videoテーブルを作成
        cursor.execute('''
            CREATE TABLE video (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                thumbnail_path TEXT,
                sort_order INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                campus_id INTEGER,
                FOREIGN KEY (campus_id) REFERENCES campus(id)
            )
        ''')
        print("videoテーブルを作成しました。")
        
        # 変更をコミット
        conn.commit()
        print(f"データベース '{db_path}' が正常に作成されました。")
        
    except sqlite3.Error as e:
        print(f"データベース作成中にエラーが発生しました: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return db_path


def migrate_database():
    """既存のデータベースを新しいスキーマにマイグレーションする"""
    app_data_dir = get_user_data_dir("PySide6App")
    db_path = app_data_dir / "database.db"
    
    if not os.path.exists(db_path):
        print("データベースファイルが見つかりません。")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # imageテーブルの構造を確認
        cursor.execute("PRAGMA table_info(image)")
        columns = cursor.fetchall()
        
        # sort_orderカラムの情報を取得
        sort_order_column = None
        for col in columns:
            if col[1] == 'sort_order':
                sort_order_column = col
                break
        
        if sort_order_column:
            # sort_orderカラムが存在する場合、デフォルト値の制約を削除
            print("sort_orderカラムの制約を更新しています...")
            
            # 既存のsort_orderが0のレコードを、適切な値に更新
            cursor.execute("""
                UPDATE image 
                SET sort_order = (
                    SELECT COALESCE(MAX(sort_order), 0) + 1 
                    FROM image i2 
                    WHERE i2.campus_id = image.campus_id 
                    AND i2.id < image.id
                )
                WHERE sort_order = 0
            """)
            
            # テーブルを再作成してNOT NULL制約を追加
            cursor.execute("""
                CREATE TABLE image_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    file_data BLOB NOT NULL,
                    sort_order INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    campus_id INTEGER,
                    FOREIGN KEY (campus_id) REFERENCES campus(id)
                )
            """)
            
            # データをコピー
            cursor.execute("""
                INSERT INTO image_new (id, name, file_data, sort_order, created_at, updated_at, campus_id)
                SELECT id, name, file_data, sort_order, created_at, updated_at, campus_id
                FROM image
            """)
            
            # 古いテーブルを削除して新しいテーブルにリネーム
            cursor.execute("DROP TABLE image")
            cursor.execute("ALTER TABLE image_new RENAME TO image")
            
            conn.commit()
            print("データベースのマイグレーションが完了しました。")
        else:
            print("sort_orderカラムが見つかりません。")
    
    except sqlite3.Error as e:
        print(f"マイグレーション中にエラーが発生しました: {e}")
        conn.rollback()
    finally:
        conn.close()


def get_database_info():
    """データベースの情報を取得する"""
    app_data_dir = get_user_data_dir("PySide6App")
    db_path = app_data_dir / "database.db"
    
    if not os.path.exists(db_path):
        print("データベースファイルが見つかりません。")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # テーブル一覧を取得
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\nデータベース '{db_path}' の情報:")
        print("=" * 50)
        
        for table in tables:
            table_name = table[0]
            print(f"\nテーブル: {table_name}")
            
            # テーブルの行数を取得
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  行数: {count}")
            
            # テーブルの構造を取得
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print("  カラム:")
            for col in columns:
                print(f"    - {col[1]} ({col[2]})")
    
    except sqlite3.Error as e:
        print(f"データベース情報取得中にエラーが発生しました: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        print("既存のデータベースをマイグレーションしています...")
        migrate_database()
        get_database_info()
        print("マイグレーション完了")
    else:
        print("SQLiteデータベースを作成しています...")
        db_path = create_database()
        get_database_info()
        print(f"\nデータベース作成完了: {db_path}")
        print("\n既存のデータベースをマイグレーションする場合は、以下のコマンドを実行してください:")
        print("python database_setup.py migrate")
