# GitLab to GitHub Migration Tool

Welcome! This is a Python tool I built to help teams (including my own) move all their GitLab repositories—code, issues, merge requests, labels, milestones—over to GitHub, with as little manual work as possible. If you’re facing a big migration, I hope this saves you a lot of time and headaches.

---

## Why I Made This

When our team needed to move dozens of projects from GitLab to GitHub, we found that most existing tools were either too limited, too manual, or didn’t handle code history and issues the way we wanted. So, I wrote this script to automate the whole process, and made it flexible enough for others to use and adapt.

---

## What It Does

- **Migrates all code and git history** (branches, tags, commits) automatically
- **Transfers issues, merge requests (as pull requests), labels, and milestones**
- **Records skipped merge requests** (e.g., missing branches) as closed GitHub issues, so nothing gets lost
- **Lets you control repository visibility** (private/public) with a simple setting
- **Cleans up descriptions** to avoid GitHub API errors
- **Gives you clear logs and error messages** (in English and Japanese)
- **No Wiki migration** (by design—keeps things simple)

---

## How It’s Different

- **No manual git push needed**—all code and history are moved for you
- **Skipped MRs are visible** as closed issues, so you can follow up if needed
- **Easy to tweak**—it’s just Python, and you can comment out features you don’t need
- **Works for both global and Japanese teams**

---

## Quick Start

### 1. Requirements
- Python 3.7+
- git command line tool
- GitLab personal access token (`read_api`, `read_repository`)
- GitHub personal access token (`repo`, `admin:org`)

### 2. Setup
```bash
pip install -r requirements.txt
cp env.example .env
# Edit .env with your tokens and group/org info
```

### 3. Run
- **Migrate everything:**
  ```bash
  python gitlab2github.py
  ```
- **Test with one repo:**
  ```bash
  python gitlab2github.py --repo your-repo-name
  ```
- **List available repos:**
  ```bash
  python gitlab2github.py --list
  ```
- **Force all repos to private:**
  ```bash
  python gitlab2github.py --force-private
  ```

---

## What to Expect
- All your code, branches, and tags will show up on GitHub
- Issues and merge requests will be recreated (as much as possible)
- If a merge request can’t be migrated (e.g., missing branch), you’ll see a closed issue with all the details
- Existing GitHub repos will be overwritten with the GitLab content
- You’ll get a detailed log (`migration.log`) for troubleshooting

---

## What’s Not Included
- **Wiki migration** (if you need this, you’ll want to handle it separately)
- **User mapping**—all migrated issues/PRs will be created by the GitHub token user

---

## Troubleshooting
- If you hit errors, check your tokens and permissions first
- For API errors, see `migration.log` for details
- If you get stuck, open an issue or send a PR—happy to help or take suggestions!

---

## License
MIT. Use it, fork it, improve it—just let me know if you make it better!

---

## 日本語README
日本語のREADMEは `README.md` をご覧ください。 