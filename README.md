# PySide6 Application

PySide6を使用したデスクトップアプリケーションです。

## セットアップ

### 1. 仮想環境の作成と有効化

```bash
cd /Users/imainaoki/work/pyside6_app/
python3 -m venv venv
source venv/bin/activate
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. アプリケーションの実行

```bash
python main.py
```

## プロジェクト構造

```
pyside6_app/
├── main.py              # メインアプリケーションファイル
├── requirements.txt     # 依存関係
└── README.md           # このファイル
```

## 機能

- 左側メニューバー（サイドバー）
- 右側メインコンテンツエリア
- レスポンシブなレイアウト
- モダンなUIデザイン
- キャンパス管理機能（画像用・動画用）

## スタイルガイドライン

### 文字色の統一
すべてのUIコンポーネントで文字色は `#1F2937` を使用してください。

```css
/* 基本文字色 */
color: #1F2937;

/* セカンダリ文字色（説明文など） */
color: #6B7280;

/* 無効化された文字色 */
color: #9CA3AF;
```

### 実装例
```python
widget.setStyleSheet("""
    QWidget {
        background-color: #FFFFFF;
        color: #1F2937;
        border: 1px solid #E5E7EB;
    }
    QWidget:hover {
        background-color: #F3F4F6;
        color: #1F2937;
    }
""")
```

### カラーパレット
- **プライマリテキスト**: `#1F2937` (濃いグレー)
- **セカンダリテキスト**: `#6B7280` (中程度のグレー)
- **無効化テキスト**: `#9CA3AF` (薄いグレー)
- **背景色**: `#FFFFFF` (白)
- **ボーダー色**: `#E5E7EB` (薄いグレー)
- **アクセント色**: `#3B82F6` (青)
