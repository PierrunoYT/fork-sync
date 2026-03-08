# Upstream Fetcher

A Python script to automatically sync all your forked GitHub repositories with their upstream branches.

## Features

- 🔄 Automatically syncs all your forked repositories with upstream
- 📊 Detailed logging and progress tracking
- 🎯 Selective syncing - sync specific repos or all at once
- 🔍 Dry-run mode to preview changes
- ⚡ Handles rate limiting and errors gracefully
- ✅ Clear success/failure reporting

## Prerequisites

- Python 3.6 or higher
- GitHub Personal Access Token with `repo` scope (or `public_repo` for public-only repos)

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Setup

### Create a GitHub Personal Access Token

1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a descriptive name (e.g., "Fork Sync Tool")
4. Select the following scopes:
   - ✅ `repo` (Full control of private repositories)
   - (Optional) `public_repo` if you only need access to public repositories
5. Click "Generate token"
6. **Copy the token** (you won't be able to see it again!)

### Set up the token

**Option 1: Environment Variable (Recommended)**
```bash
# Windows (PowerShell)
$env:GITHUB_TOKEN="your_token_here"

# Windows (Command Prompt)
set GITHUB_TOKEN=your_token_here

# Linux/Mac
export GITHUB_TOKEN="your_token_here"
```

**Option 2: Command Line Argument**
```bash
python sync_forks.py --token your_token_here
```

## Usage

### Basic Usage - Sync All Forks

```bash
python sync_forks.py
```

### Dry Run - Preview What Would Be Synced

```bash
python sync_forks.py --dry-run
```

### Sync Specific Repositories

```bash
python sync_forks.py --repos repo1 repo2 repo3
```

### Use a Different Default Branch

```bash
python sync_forks.py --branch master
```

### Combine Options

```bash
python sync_forks.py --dry-run --repos my-fork --branch develop
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--token TOKEN` | GitHub personal access token (or set `GITHUB_TOKEN` env var) |
| `--branch BRANCH` | Default branch name to sync (default: `main`) |
| `--dry-run` | Show what would be synced without actually syncing |
| `--repos REPO [REPO ...]` | Specific repository names to sync (syncs all if not specified) |
| `-h, --help` | Show help message |

## Output

The script provides detailed output including:

- ✓ Successfully synced repositories
- ⚠ Repositories that are already up-to-date
- ⚠ Repositories with merge conflicts (require manual intervention)
- ✗ Failed sync attempts with error details
- 📊 Final summary with statistics

### Example Output

```
2025-11-10 14:10:00 - INFO - Fetching forked repositories for user: yourusername
2025-11-10 14:10:01 - INFO - Found 5 forked repositories

============================================================
Starting sync process for 5 fork(s)
============================================================

2025-11-10 14:10:02 - INFO - [1/5] Processing: yourusername/repo1
2025-11-10 14:10:03 - INFO - ✓ Successfully synced yourusername/repo1 (branch: main)
2025-11-10 14:10:04 - INFO - [2/5] Processing: yourusername/repo2
2025-11-10 14:10:05 - INFO - ✓ yourusername/repo2 is already up-to-date (branch: main)
...

============================================================
SYNC SUMMARY
============================================================
Total forks found:    5
Successfully synced:  5
Failed to sync:       0
Skipped:              0
============================================================
```

## How It Works

1. **Authentication**: Uses your GitHub token to authenticate with the GitHub API
2. **Discovery**: Fetches all repositories you own and filters for forks
3. **Sync**: For each fork, uses GitHub's merge-upstream API to sync with the upstream repository
4. **Reporting**: Provides detailed status for each repository and a final summary

## Troubleshooting

### "Error: GitHub token is required!"
- Make sure you've set the `GITHUB_TOKEN` environment variable or passed `--token`

### "Upstream not found"
- The repository may not have an upstream configured
- The upstream repository may have been deleted

### "Merge conflict"
- Manual intervention is required
- Go to the repository on GitHub and resolve conflicts manually

### Rate Limiting
- The script includes a small delay between requests to avoid rate limiting
- GitHub API has a rate limit of 5000 requests/hour for authenticated users

## Security Notes

⚠️ **Never commit your GitHub token to version control!**

- Use environment variables or pass tokens via command line
- Add `.env` files to `.gitignore` if you use them
- Rotate tokens periodically
- Use tokens with minimal required scopes

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.
