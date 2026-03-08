#!/usr/bin/env python3
"""
Sync all forked repositories with their upstream branches.
This script uses the GitHub API to find all your forks and sync them with upstream.
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Optional, Union
import requests


class GitHubForkSyncer:
    """Handles syncing of forked repositories with their upstream branches."""

    REQUEST_TIMEOUT_SECONDS = 20
    
    def __init__(self, token: str, default_branch: str = "main"):
        """
        Initialize the syncer.
        
        Args:
            token: GitHub personal access token
            default_branch: Default branch name to sync (default: "main")
        """
        self.token = token
        self.default_branch = default_branch
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def get_authenticated_user(self) -> str:
        """Get the authenticated user's username."""
        url = f"{self.base_url}/user"
        response = requests.get(url, headers=self.headers, timeout=self.REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()["login"]
    
    def get_all_forks(self, username: str) -> List[Dict]:
        """
        Get all forked repositories for the authenticated user.
        
        Args:
            username: GitHub username
            
        Returns:
            List of fork repository objects
        """
        forks = []
        page = 1
        per_page = 100
        
        self.logger.info(f"Fetching forked repositories for user: {username}")
        
        while True:
            url = f"{self.base_url}/user/repos"
            params = {
                "type": "owner",
                "per_page": per_page,
                "page": page
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=self.REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            repos = response.json()
            
            if not repos:
                break
            
            # Filter only forked repositories
            forked_repos = [repo for repo in repos if repo.get("fork", False)]
            forks.extend(forked_repos)
            
            page += 1
        
        self.logger.info(f"Found {len(forks)} forked repositories")
        return forks
    
    def get_default_branch(self, repo: Dict) -> str:
        """
        Get the default branch for a repository.
        
        Args:
            repo: Repository object
            
        Returns:
            Default branch name
        """
        return repo.get("default_branch", self.default_branch)
    
    def sync_fork_with_upstream(self, owner: str, repo_name: str, branch: Optional[str] = None) -> Union[bool, str]:
        """
        Sync a fork with its upstream repository.
        
        Args:
            owner: Repository owner (your username)
            repo_name: Repository name
            branch: Branch to sync (if None, uses default branch)
            
        Returns:
            True if sync was successful, False otherwise
        """
        url = f"{self.base_url}/repos/{owner}/{repo_name}/merge-upstream"
        
        data = {
            "branch": branch or self.default_branch
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=self.REQUEST_TIMEOUT_SECONDS)
            
            if response.status_code == 200:
                self.logger.info(f"✓ Successfully synced {owner}/{repo_name} (branch: {data['branch']})")
                return True
            elif response.status_code == 204:
                self.logger.info(f"✓ {owner}/{repo_name} is already up-to-date (branch: {data['branch']})")
                return "already_synced"
            elif response.status_code == 202:
                self.logger.info(f"↻ Sync started for {owner}/{repo_name} (branch: {data['branch']})")
                return "accepted"
            elif response.status_code == 409:
                self.logger.warning(f"⚠ Merge conflict in {owner}/{repo_name} (branch: {data['branch']}) - manual intervention required")
                return False
            elif response.status_code == 404:
                self.logger.warning(f"⚠ Upstream not found for {owner}/{repo_name} or branch doesn't exist")
                return False
            elif response.status_code == 403:
                self.logger.error(f"✗ Permission denied for {owner}/{repo_name} (bad token/scopes or rate limit reached)")
                return False
            elif response.status_code == 422:
                self.logger.warning(f"⚠ Cannot merge {owner}/{repo_name} (branch not valid or not yet available)")
                return False
            else:
                self.logger.error(f"✗ Failed to sync {owner}/{repo_name}: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"✗ Error syncing {owner}/{repo_name}: {str(e)}")
            return False
    
    def sync_all_forks(self, dry_run: bool = False, specific_repos: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Sync all forked repositories with their upstream.
        
        Args:
            dry_run: If True, only show what would be synced without actually syncing
            specific_repos: List of specific repository names to sync (if None, sync all)
            
        Returns:
            Dictionary with sync statistics
        """
        stats = {
            "total": 0,
            "success": 0,
            "already_synced": 0,
            "failed": 0,
            "skipped": 0
        }
        
        try:
            username = self.get_authenticated_user()
            forks = self.get_all_forks(username)
            
            if not forks:
                self.logger.info("No forked repositories found")
                return stats
            
            stats["total"] = len(forks)
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Starting sync process for {len(forks)} fork(s)")
            if dry_run:
                self.logger.info("DRY RUN MODE - No actual syncing will occur")
            self.logger.info(f"{'='*60}\n")
            
            for idx, repo in enumerate(forks, 1):
                repo_name = repo["name"]
                full_name = repo["full_name"]
                default_branch = self.get_default_branch(repo)
                
                # Skip if specific repos are specified and this isn't one of them
                if specific_repos and repo_name not in specific_repos:
                    stats["skipped"] += 1
                    continue
                
                self.logger.info(f"[{idx}/{len(forks)}] Processing: {full_name}")
                
                if dry_run:
                    self.logger.info(f"    Would sync branch: {default_branch}")
                    continue
                
                sync_status = self.sync_fork_with_upstream(username, repo_name, default_branch)
                if sync_status is True:
                    stats["success"] += 1
                elif sync_status == "already_synced":
                    stats["already_synced"] += 1
                    stats["success"] += 1
                elif sync_status == "accepted":
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                
                # Small delay to avoid rate limiting
                import time
                time.sleep(0.5)
            
            return stats
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API Error: {str(e)}")
            return stats
    
    def print_summary(self, stats: Dict[str, int]):
        """Print summary of sync operation."""
        self.logger.info(f"\n{'='*60}")
        self.logger.info("SYNC SUMMARY")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Total forks found:    {stats['total']}")
        self.logger.info(f"Successfully synced:  {stats['success']}")
        self.logger.info(f"Already up-to-date:   {stats['already_synced']}")
        self.logger.info(f"Failed to sync:       {stats['failed']}")
        self.logger.info(f"Skipped:              {stats['skipped']}")
        self.logger.info(f"{'='*60}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sync all your forked GitHub repositories with their upstream branches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync all forks
  python sync_forks.py
  
  # Dry run to see what would be synced
  python sync_forks.py --dry-run
  
  # Sync specific repositories only
  python sync_forks.py --repos repo1 repo2
  
  # Use a specific default branch
  python sync_forks.py --branch master
  
Environment Variables:
  GITHUB_TOKEN: Your GitHub personal access token (required)
                Create one at: https://github.com/settings/tokens
                Required scopes: repo (or public_repo for public-only repos)
        """
    )
    
    parser.add_argument(
        "--token",
        help="GitHub personal access token (or set GITHUB_TOKEN env var)",
        default=os.environ.get("GITHUB_TOKEN")
    )
    
    parser.add_argument(
        "--branch",
        default="main",
        help="Default branch name to sync (default: main)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without actually syncing"
    )
    
    parser.add_argument(
        "--repos",
        nargs="+",
        help="Specific repository names to sync (if not specified, syncs all)"
    )
    
    args = parser.parse_args()
    
    # Validate token
    if not args.token:
        print("Error: GitHub token is required!")
        print("Either set GITHUB_TOKEN environment variable or use --token argument")
        print("\nCreate a token at: https://github.com/settings/tokens")
        print("Required scopes: repo (or public_repo for public-only repos)")
        sys.exit(1)
    
    # Create syncer and run
    syncer = GitHubForkSyncer(args.token, args.branch)
    stats = syncer.sync_all_forks(dry_run=args.dry_run, specific_repos=args.repos)
    syncer.print_summary(stats)
    
    # Exit with error code if any syncs failed
    if stats["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
