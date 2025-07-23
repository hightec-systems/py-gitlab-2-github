#!/usr/bin/env python3
"""
テスト移行専用スクリプト
単一リポジトリの移行を簡単にテストできるスクリプト
"""

import os
import sys
from dotenv import load_dotenv


def check_environment():
    """環境設定の確認"""
    load_dotenv()

    required_vars = [
        'GITLAB_URL',
        'GITLAB_TOKEN',
        'GITLAB_GROUP_ID',
        'GITHUB_TOKEN',
        'GITHUB_ORG'
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ 以下の環境変数が設定されていません:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n.envファイルを確認してください")
        return False

    print("✅ 環境変数の設定が完了しています")
    return True


def main():
    """メイン関数"""
    print("🧪 GitLab to GitHub テスト移行ツール")
    print("=" * 40)

    # 環境設定の確認
    if not check_environment():
        sys.exit(1)

    print("\n📋 利用可能なコマンド:")
    print("1. リポジトリ一覧を表示:")
    print("   python gitlab2github.py --list")
    print()
    print("2. 特定のリポジトリを移行:")
    print("   python gitlab2github.py --repo REPO_NAME")
    print()
    print("3. ドライラン（移行前の確認）:")
    print("   python gitlab2github.py --repo REPO_NAME --dry-run")
    print()
    print("4. 全リポジトリを移行:")
    print("   python gitlab2github.py")
    print()

    # ユーザーに選択肢を提示
    choice = input("どの操作を実行しますか？ (1-4): ").strip()

    if choice == "1":
        os.system("python gitlab2github.py --list")
    elif choice == "2":
        repo_name = input("移行するリポジトリ名を入力してください: ").strip()
        if repo_name:
            os.system(f"python gitlab2github.py --repo {repo_name}")
        else:
            print("❌ リポジトリ名が入力されていません")
    elif choice == "3":
        repo_name = input("確認するリポジトリ名を入力してください: ").strip()
        if repo_name:
            os.system(f"python gitlab2github.py --repo {repo_name} --dry-run")
        else:
            print("❌ リポジトリ名が入力されていません")
    elif choice == "4":
        confirm = input("⚠️  全リポジトリを移行しますか？ (y/N): ").strip().lower()
        if confirm == 'y':
            os.system("python gitlab2github.py")
        else:
            print("移行をキャンセルしました")
    else:
        print("❌ 無効な選択です")


if __name__ == "__main__":
    main()
