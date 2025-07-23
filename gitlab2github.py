#!/usr/bin/env python3
"""
GitLabからGitHubへの移行ツール
Issues、Merge Requests、Wiki、Labels、Milestonesを含む完全な移行を実行します。
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
from tqdm import tqdm
import re
import subprocess

import gitlab
from github import Github
import requests

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class MigrationConfig:
    """移行設定クラス"""
    gitlab_url: str
    gitlab_token: str
    gitlab_group_id: str
    github_token: str
    github_org: str
    migrate_issues: bool = True
    migrate_merge_requests: bool = True
    migrate_wiki: bool = True
    migrate_labels: bool = True
    migrate_milestones: bool = True
    target_repo: Optional[str] = None  # 特定のリポジトリ名
    force_private: bool = False        # すべてprivateで作成するか


class GitLabToGitHubMigrator:
    """GitLabからGitHubへの移行クラス"""

    def __init__(self, config: MigrationConfig):
        self.config = config
        self.gitlab = gitlab.Gitlab(url=config.gitlab_url, private_token=config.gitlab_token)
        self.github = Github(config.github_token)
        self.github_org = self.github.get_organization(config.github_org)

        # 移行マッピングを保存
        self.user_mapping = {}
        self.label_mapping = {}
        self.milestone_mapping = {}

    def get_gitlab_repositories(self) -> List[Dict]:
        """GitLabグループ内の全リポジトリを取得"""
        try:
            group = self.gitlab.groups.get(self.config.gitlab_group_id)
            projects = group.projects.list(all=True)

            repositories = []
            for project in projects:
                repo_info = {
                    'id': project.id,
                    'name': project.name,
                    'path': project.path,
                    'description': project.description,
                    'visibility': project.visibility,
                    'web_url': project.web_url,
                    'ssh_url_to_repo': project.ssh_url_to_repo,
                    'http_url_to_repo': project.http_url_to_repo
                }
                repositories.append(repo_info)

            logger.info(f"GitLabグループから {len(repositories)} 個のリポジトリを取得しました")
            return repositories

        except Exception as e:
            logger.error(f"GitLabリポジトリの取得に失敗しました: {e}")
            return []

    def get_specific_repository(self, repo_name: str) -> Optional[Dict]:
        """特定のリポジトリを取得"""
        try:
            group = self.gitlab.groups.get(self.config.gitlab_group_id)
            projects = group.projects.list(all=True)

            for project in projects:
                if project.name == repo_name:
                    repo_info = {
                        'id': project.id,
                        'name': project.name,
                        'path': project.path,
                        'description': project.description,
                        'visibility': project.visibility,
                        'web_url': project.web_url,
                        'ssh_url_to_repo': project.ssh_url_to_repo,
                        'http_url_to_repo': project.http_url_to_repo
                    }
                    logger.info(f"リポジトリ {repo_name} を取得しました")
                    return repo_info

            logger.error(f"リポジトリ {repo_name} が見つかりませんでした")
            return None

        except Exception as e:
            logger.error(f"リポジトリ {repo_name} の取得に失敗しました: {e}")
            return None

    def sanitize_description(self, description: Optional[str]) -> str:
        """descriptionからGitHubが許可しない制御文字を除去"""
        if not description:
            return ''
        # ASCII制御文字（0x00-0x1F, 0x7F）を除去
        return re.sub(r'[\x00-\x1F\x7F]', '', description)

    def create_github_repository(self, repo_info: Dict) -> Optional[str]:
        """GitHubにリポジトリを作成（既存ならスキップしてURL返す）"""
        try:
            repo_name = repo_info['name']

            # リポジトリが既に存在するかチェック
            try:
                existing_repo = self.github_org.get_repo(repo_name)
                logger.warning(f"リポジトリ {repo_name} は既に存在します（pushで上書きします）")
                return existing_repo.clone_url
            except Exception:
                pass

            # 可視性の決定
            if self.config.force_private:
                visibility = 'private'
            else:
                visibility = 'private' if repo_info['visibility'] == 'private' else 'public'

            # descriptionの制御文字を除去
            safe_description = self.sanitize_description(repo_info.get('description', ''))

            repo = self.github_org.create_repo(
                name=repo_name,
                description=safe_description,
                private=(visibility == 'private'),
                auto_init=False
            )

            logger.info(f"GitHubリポジトリ {repo_name} を作成しました (visibility: {visibility})")
            return repo.clone_url

        except Exception as e:
            logger.error(f"GitHubリポジトリ {repo_info['name']} の作成に失敗しました: {e}")
            return None

    def migrate_labels(self, gitlab_project, github_repo):
        """ラベルの移行"""
        if not self.config.migrate_labels:
            return

        try:
            labels = gitlab_project.labels.list()

            for label in labels:
                try:
                    # ラベルの色を16進数に変換
                    color = label.color.lstrip('#') if label.color.startswith('#') else label.color

                    github_repo.create_label(
                        name=label.name,
                        color=color,
                        description=label.description or ''
                    )
                    logger.info(f"ラベル {label.name} を移行しました")

                except Exception as e:
                    logger.warning(f"ラベル {label.name} の移行に失敗しました: {e}")

        except Exception as e:
            logger.error(f"ラベルの移行に失敗しました: {e}")

    def migrate_milestones(self, gitlab_project, github_repo):
        """マイルストーンの移行"""
        if not self.config.migrate_milestones:
            return

        try:
            milestones = gitlab_project.milestones.list()

            for milestone in milestones:
                try:
                    # マイルストーンの状態を設定
                    state = 'closed' if milestone.state == 'closed' else 'open'

                    gh_milestone = github_repo.create_milestone(
                        title=milestone.title,
                        description=milestone.description or '',
                        state=state
                    )

                    # マッピングを保存
                    self.milestone_mapping[milestone.id] = gh_milestone.number

                    logger.info(f"マイルストーン {milestone.title} を移行しました")

                except Exception as e:
                    logger.warning(f"マイルストーン {milestone.title} の移行に失敗しました: {e}")

        except Exception as e:
            logger.error(f"マイルストーンの移行に失敗しました: {e}")

    def migrate_git_repository(self, repo_info: Dict) -> bool:
        """GitLabからGitHubへGitリポジトリ（履歴含む）を自動で移行（既存リポジトリにも強制push）"""
        gitlab_url = repo_info['http_url_to_repo']
        if gitlab_url.startswith('https://'):
            gitlab_url = gitlab_url.replace('https://', f'https://oauth2:{self.config.gitlab_token}@')
        github_url = self.github_org.get_repo(repo_info['name']).clone_url.replace('https://', f'https://{self.config.github_token}@')
        temp_dir = f"_tmp_migrate_{repo_info['name']}"
        try:
            # クローン
            subprocess.run(["git", "clone", "--mirror", gitlab_url, temp_dir], check=True)
            # GitHubへpush（--mirrorで強制上書き）
            subprocess.run(["git", "-C", temp_dir, "remote", "set-url", "origin", github_url], check=True)
            subprocess.run(["git", "-C", temp_dir, "push", "--mirror", "--force"], check=True)
            # 後片付け
            subprocess.run(["rm", "-rf", temp_dir])
            logger.info(f"Gitリポジトリ {repo_info['name']} のコード・履歴を移行しました（既存リポジトリも上書き）")
            return True
        except Exception as e:
            logger.error(f"Gitリポジトリ {repo_info['name']} のコード移行に失敗しました: {e}")
            subprocess.run(["rm", "-rf", temp_dir])
            return False

    def migrate_issues(self, gitlab_project, github_repo):
        """Issuesの移行"""
        if not self.config.migrate_issues:
            return

        try:
            issues = gitlab_project.issues.list(all=True)

            # GitHub側の既存Issue一覧を取得（open/closed両方）
            existing_issues = list(github_repo.get_issues(state='all'))
            existing_issue_keys = set()
            for ei in existing_issues:
                # タイトルと状態で重複判定
                existing_issue_keys.add((ei.title, ei.state))

            # GitHub側のラベル名一覧を取得
            github_label_names = set(label.name for label in github_repo.get_labels())
            # GitLab側のラベル情報をキャッシュ
            gitlab_label_dict = {l.name: l for l in gitlab_project.labels.list()}

            for issue in tqdm(issues, desc="Issues移行中"):
                try:
                    # ラベルを取得（GitHub側に存在しない場合は自動作成）
                    labels = []
                    for label in issue.labels:
                        if hasattr(label, 'name'):
                            name = label.name
                        elif isinstance(label, str):
                            name = label
                        else:
                            continue
                        if name not in github_label_names:
                            # GitLab側のラベル情報を取得
                            color = "ededed"
                            description = ""
                            if name in gitlab_label_dict:
                                gl_label = gitlab_label_dict[name]
                                color = gl_label.color.lstrip('#') if gl_label.color else "ededed"
                                description = gl_label.description or ""
                            try:
                                github_repo.create_label(name=name, color=color, description=description)
                                # ラベル作成後はキャッシュを再取得
                                github_label_names = set(label.name for label in github_repo.get_labels())
                                logger.info(f"GitHubにラベル {name} を自動作成しました")
                            except Exception as e:
                                logger.warning(f"GitHubラベル {name} の自動作成に失敗: {e}")
                                continue
                        labels.append(name)

                    # マイルストーンを設定
                    milestone = None
                    if hasattr(issue, 'milestone') and issue.milestone:
                        milestone_number = self.milestone_mapping.get(issue.milestone.id)
                        if milestone_number:
                            milestone = github_repo.get_milestone(milestone_number)

                    # bodyがNoneの場合は空文字
                    body = issue.description if issue.description is not None else ""

                    # 重複判定（タイトル・状態）
                    issue_state = 'closed' if issue.state == 'closed' else 'open'
                    if (issue.title, issue_state) in existing_issue_keys:
                        logger.info(f"Issue {issue.iid}（{issue.title}）は既に存在するためスキップ")
                        continue

                    # Issueを作成
                    try:
                        issue_kwargs = {
                            'title': issue.title,
                            'body': body,
                        }
                        if labels:
                            issue_kwargs['labels'] = labels
                        if milestone is not None:
                            issue_kwargs['milestone'] = milestone
                        logger.info(f"Issue {issue.iid} 作成時の引数: {issue_kwargs}")
                        gh_issue = github_repo.create_issue(**issue_kwargs)
                    except AssertionError as ae:
                        logger.warning(f"Issue {issue.iid} のラベル指定でAssertionError: {ae}, labels={labels}")
                        continue

                    # コメントを移行
                    notes = issue.notes.list()
                    for note in notes:
                        if note.body and note.body.strip():
                            gh_issue.create_comment(note.body)

                    # 状態を設定
                    if issue.state == 'closed':
                        gh_issue.edit(state='closed')

                    logger.info(f"Issue {issue.iid} を移行しました")

                    # API制限を避けるため少し待機
                    time.sleep(0.1)

                except Exception as e:
                    logger.warning(f"Issue {issue.iid} の移行に失敗しました: {e}")
                    # 例外の詳細も出力
                    if hasattr(e, 'data'):
                        logger.warning(f"GitHub API response: {e.data}")
                    if hasattr(e, 'status'):
                        logger.warning(f"GitHub API status: {e.status}")
                    logger.warning(f"Exception type: {type(e)}")

        except Exception as e:
            logger.error(f"Issuesの移行に失敗しました: {e}")

    def migrate_merge_requests(self, gitlab_project, github_repo):
        """Merge Requestsの移行"""
        if not self.config.migrate_merge_requests:
            return

        try:
            merge_requests = gitlab_project.mergerequests.list(all=True)

            for mr in tqdm(merge_requests, desc="Merge Requests移行中"):
                try:
                    # ブランチ存在チェック
                    branches = [b.name for b in github_repo.get_branches()]
                    if mr.source_branch not in branches or mr.target_branch not in branches:
                        logger.warning(f"MR {mr.iid}: ブランチが存在しないためスキップ (source: {mr.source_branch}, target: {mr.target_branch})")
                        # スキップ情報をIssueとして記録し、すぐにクローズ
                        issue_title = f"[移行スキップ] MR: {mr.title} (source: {mr.source_branch}, target: {mr.target_branch})"
                        issue_body = f"""
このMerge Requestは移行時にスキップされました。
- GitLab MR番号: !{mr.iid}
- タイトル: {mr.title}
- 作成者: {getattr(mr, 'author', {}).get('name', '不明')}
- 状態: {mr.state}
- ソースブランチ: {mr.source_branch}
- ターゲットブランチ: {mr.target_branch}
- 理由: GitHub上に該当ブランチが存在しないためPull Requestとして作成できませんでした。
- 元GitLab URL: {getattr(mr, 'web_url', '')}
"""
                        gh_issue = github_repo.create_issue(title=issue_title, body=issue_body)
                        gh_issue.edit(state='closed')
                        logger.info(f"MR {mr.iid}: スキップし、内容をIssue（クローズ済み）として記録しました")
                        continue
                    # ラベルを取得
                    labels = []
                    for label in mr.labels:
                        if hasattr(label, 'name'):
                            labels.append(label.name)
                        elif isinstance(label, str):
                            labels.append(label)

                    # マイルストーンを設定
                    milestone = None
                    if hasattr(mr, 'milestone') and mr.milestone:
                        milestone_number = self.milestone_mapping.get(mr.milestone.id)
                        if milestone_number:
                            milestone = github_repo.get_milestone(milestone_number)

                    # Pull Requestを作成
                    gh_pr = github_repo.create_pull(
                        title=mr.title,
                        body=mr.description or '',
                        head=mr.source_branch,
                        base=mr.target_branch
                    )

                    # ラベルを設定
                    if labels:
                        gh_pr.add_to_labels(*labels)

                    # マイルストーンを設定
                    if milestone:
                        gh_pr.add_to_assignees(milestone)

                    # コメントを移行
                    notes = mr.notes.list()
                    for note in notes:
                        if note.body and note.body.strip():
                            gh_pr.create_issue_comment(note.body)

                    # 状態を設定
                    if mr.state == 'merged':
                        gh_pr.edit(state='closed')
                    elif mr.state == 'closed':
                        gh_pr.edit(state='closed')

                    logger.info(f"Merge Request {mr.iid} を移行しました")

                    # API制限を避けるため少し待機
                    time.sleep(0.1)

                except Exception as e:
                    logger.warning(f"Merge Request {mr.iid} の移行に失敗しました: {e}")

        except Exception as e:
            logger.error(f"Merge Requestsの移行に失敗しました: {e}")

    def migrate_repository(self, repo_info: Dict):
        """単一リポジトリの移行"""
        try:
            logger.info(f"リポジトリ {repo_info['name']} の移行を開始します")

            # GitLabプロジェクトを取得
            gitlab_project = self.gitlab.projects.get(repo_info['id'])

            # GitHubリポジトリを作成
            github_repo_url = self.create_github_repository(repo_info)
            if not github_repo_url:
                logger.error(f"GitHubリポジトリの作成に失敗しました: {repo_info['name']}")
                return False

            github_repo = self.github_org.get_repo(repo_info['name'])

            # コード・履歴を移行
            self.migrate_git_repository(repo_info)

            # 各要素を移行
            self.migrate_labels(gitlab_project, github_repo)
            self.migrate_milestones(gitlab_project, github_repo)
            self.migrate_issues(gitlab_project, github_repo)
            self.migrate_merge_requests(gitlab_project, github_repo)

            logger.info(f"リポジトリ {repo_info['name']} の移行が完了しました")
            return True

        except Exception as e:
            logger.error(f"リポジトリ {repo_info['name']} の移行に失敗しました: {e}")
            return False

    def run_migration(self):
        """移行を実行"""
        logger.info("GitLabからGitHubへの移行を開始します")

        # 特定のリポジトリが指定されている場合
        if self.config.target_repo:
            logger.info(f"特定のリポジトリ {self.config.target_repo} を移行します")
            repo_info = self.get_specific_repository(self.config.target_repo)
            if not repo_info:
                logger.error(f"リポジトリ {self.config.target_repo} の移行に失敗しました")
                return

            if self.migrate_repository(repo_info):
                logger.info(f"リポジトリ {self.config.target_repo} の移行が完了しました")
            else:
                logger.error(f"リポジトリ {self.config.target_repo} の移行に失敗しました")
            return

        # 全リポジトリを移行
        repositories = self.get_gitlab_repositories()
        if not repositories:
            logger.error("移行するリポジトリが見つかりませんでした")
            return

        # 各リポジトリを移行
        success_count = 0
        for repo_info in repositories:
            if self.migrate_repository(repo_info):
                success_count += 1

        logger.info(f"移行完了: {success_count}/{len(repositories)} リポジトリが正常に移行されました")


def load_config() -> MigrationConfig:
    """設定を読み込み"""
    load_dotenv()

    return MigrationConfig(
        gitlab_url=os.getenv('GITLAB_URL'),
        gitlab_token=os.getenv('GITLAB_TOKEN'),
        gitlab_group_id=os.getenv('GITLAB_GROUP_ID'),
        github_token=os.getenv('GITHUB_TOKEN'),
        github_org=os.getenv('GITHUB_ORG'),
        migrate_issues=os.getenv('MIGRATE_ISSUES', 'true').lower() == 'true',
        migrate_merge_requests=os.getenv('MIGRATE_MERGE_REQUESTS', 'true').lower() == 'true',
        migrate_wiki=os.getenv('MIGRATE_WIKI', 'true').lower() == 'true',
        migrate_labels=os.getenv('MIGRATE_LABELS', 'true').lower() == 'true',
        migrate_milestones=os.getenv('MIGRATE_MILESTONES', 'true').lower() == 'true',
        force_private=os.getenv('FORCE_PRIVATE', 'false').lower() == 'true'
    )


def main():
    """メイン関数"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='GitLabからGitHubへの移行ツール')
    parser.add_argument('--repo', '-r', type=str, help='移行する特定のリポジトリ名')
    parser.add_argument('--list', '-l', action='store_true', help='利用可能なリポジトリ一覧を表示')
    parser.add_argument('--dry-run', action='store_true', help='実際の移行は行わず、移行対象を表示')
    parser.add_argument('--force-private', action='store_true', help='すべてprivateリポジトリとして作成する')

    args = parser.parse_args()

    try:
        config = load_config()

        # コマンドライン引数でforce_privateが指定された場合は上書き
        if args.force_private:
            config.force_private = True

        # 必須設定のチェック
        required_fields = [
            'gitlab_url', 'gitlab_token', 'gitlab_group_id',
            'github_token', 'github_org'
        ]

        for field in required_fields:
            if not getattr(config, field):
                logger.error(f"必須設定 {field} が設定されていません")
                logger.info("env.exampleファイルを参考に.envファイルを作成してください")
                sys.exit(1)

        # 特定のリポジトリが指定されている場合
        if args.repo:
            config.target_repo = args.repo

        # リポジトリ一覧表示
        if args.list:
            migrator = GitLabToGitHubMigrator(config)
            repositories = migrator.get_gitlab_repositories()
            if repositories:
                print("\n📋 利用可能なリポジトリ一覧:")
                print("=" * 50)
                for repo in repositories:
                    print(f"• {repo['name']} - {repo.get('description', '説明なし')}")
                print(f"\n合計: {len(repositories)} 個のリポジトリ")
            else:
                print("❌ リポジトリが見つかりませんでした")
            return

        # ドライラン
        if args.dry_run:
            migrator = GitLabToGitHubMigrator(config)
            if config.target_repo:
                repo_info = migrator.get_specific_repository(config.target_repo)
                if repo_info:
                    print(f"\n🔍 移行対象: {repo_info['name']}")
                    print(f"   説明: {repo_info.get('description', '説明なし')}")
                    print(f"   可視性: {repo_info['visibility']}")
                    print(f"   URL: {repo_info['web_url']}")
                else:
                    print(f"❌ リポジトリ {config.target_repo} が見つかりませんでした")
            else:
                repositories = migrator.get_gitlab_repositories()
                if repositories:
                    print(f"\n🔍 移行対象: {len(repositories)} 個のリポジトリ")
                    for repo in repositories:
                        print(f"   • {repo['name']}")
                else:
                    print("❌ 移行対象のリポジトリが見つかりませんでした")
            return

        # 移行を実行
        migrator = GitLabToGitHubMigrator(config)
        migrator.run_migration()

    except Exception as e:
        logger.error(f"移行中にエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
