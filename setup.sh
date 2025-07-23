#!/bin/bash

echo "GitLab to GitHub Migration Tool セットアップ"
echo "================================================"

# Pythonのバージョンチェック
python_version_full=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
python_major=$(echo $python_version_full | cut -d. -f1)
python_minor=$(echo $python_version_full | cut -d. -f2)

if [ "$python_major" -gt 3 ] || { [ "$python_major" -eq 3 ] && [ "$python_minor" -ge 7 ]; }; then
    echo "Python 3.7+ が確認されました: $(python3 --version)"
else
    echo "Python 3.7+ が必要です。現在のバージョン: $(python3 --version)"
    exit 1
fi

# venv作成
if [ ! -d "venv" ]; then
    echo "venv仮想環境を作成中..."
    python3 -m venv venv
    echo "venv仮想環境を作成しました"
else
    echo "venv仮想環境は既に存在します"
fi

# venv有効化
source venv/bin/activate

# pipのインストール確認
if ! command -v pip &> /dev/null; then
    echo "pipが見つかりません。インストールしてください。"
    exit 1
fi

echo "依存関係をインストール中..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "依存関係のインストールが完了しました"
else
    echo "依存関係のインストールに失敗しました"
    exit 1
fi

# .envファイルの作成
if [ ! -f .env ]; then
    echo ".envファイルを作成中..."
    cp env.example .env
    echo ".envファイルが作成されました"
    echo ".envファイルを編集して設定を完了してください"
else
    echo ".envファイルは既に存在します"
fi

echo ""
echo "セットアップが完了しました"
echo ""
echo "次の手順:"
echo "1. .envファイルを編集して設定を完了"
echo "2. source venv/bin/activate で仮想環境を有効化"
echo "3. python gitlab2github.py を実行して移行を開始"
echo ""
echo "詳細は README.md を参照してください" 