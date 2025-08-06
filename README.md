# GitLab to GitHub Migration Tool

このツールは、GitLabで運用している複数のリポジトリをGitHubへ移行するためのPythonスクリプトです。コード（全履歴）、Issue、Merge Request、labelを自動で移行します。

## 主な機能

- コード・履歴（全ブランチ・タグ・コミット）の自動移行
- Issue、Merge Request（Pull Requestとして）、ラベル、マイルストーンの移行
- 移行できなかったMerge Requestは、内容をクローズ済みIssueとしてGitHubに記録
- リポジトリの可視性（private/public）を.envやコマンドラインで制御可能
- descriptionの自動クリーンアップ（GitHub API仕様に自動対応）
- 詳細な日本語・英語ログ、エラー出力
- Wiki移行は非対応

## 必要なもの

- Python 3.7以上
- gitコマンド
- GitLab個人アクセストークン（read_api, read_repository権限）
- GitHub個人アクセストークン（repo, admin:org権限）

## セットアップ手順（venv仮想環境を利用）

1. 仮想環境の作成と有効化
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. 依存パッケージのインストール
   ```bash
   pip install -r requirements.txt
   ```
3. 環境変数ファイルの作成
   ```bash
   cp env.example .env
   # .envを編集し、各種トークンやグループ/組織情報を設定
   ```

## 使い方

- 全リポジトリを移行する場合
  ```bash
  python gitlab2github.py
  ```
- 特定のリポジトリのみ移行する場合
  ```bash
  python gitlab2github.py --repo リポジトリ名
  ```
- 利用可能なリポジトリ一覧を表示
  ```bash
  python gitlab2github.py --list
  ```
- すべてprivateで作成したい場合
  ```bash
  python gitlab2github.py --force-private
  ```

## 移行内容

- コード・履歴（全ブランチ・タグ）
- Issue、Merge Request（Pull Requestとして）
- ラベル、マイルストーン
- 移行できなかったMerge Requestはクローズ済みIssueとして記録
- 既存のGitHubリポジトリはGitLabの内容で上書き

## 非対応・注意事項

- Wiki移行は非対応
- ユーザー名のマッピングは行いません（全てGitHubトークンのユーザー名義で作成）
- API制限により大量移行時は時間がかかる場合があります
- 詳細な進行状況・エラーはmigration.logで確認可能

## トラブルシューティング

- 認証エラーや権限エラーはトークン・権限設定を再確認してください
- 詳細なエラー内容はmigration.logを参照してください
- 不明点や改善要望はIssueまたはPRでご連絡ください

## ライセンス

MITライセンスです。ご自由にご利用・改変ください。

## English README

For English, see `README.en.md`. 
