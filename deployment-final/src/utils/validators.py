"""
GitHub validation utilities for CodeFlowOps
Validates repository access and format
"""

import re
import logging
from typing import Dict, Any, Optional
import httpx
from urllib.parse import urlparse

from ..config.env import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def validate_github_access(github_url: str) -> Dict[str, Any]:
    """
    Validate GitHub repository URL and accessibility
    
    Args:
        github_url: GitHub repository URL
        
    Returns:
        Dict with validation results
    """
    try:
        # Validate URL format
        if not is_valid_github_url(github_url):
            return {
                "accessible": False,
                "error": "Invalid GitHub repository URL format",
                "details": "URL must be in format: https://github.com/owner/repo"
            }
        
        # Extract owner and repo from URL
        owner, repo = extract_github_info(github_url)
        if not owner or not repo:
            return {
                "accessible": False,
                "error": "Could not extract repository information from URL",
                "details": "Unable to parse owner and repository name"
            }
        
        # Check repository accessibility
        accessibility_result = await check_repository_accessibility(owner, repo)
        
        return {
            "accessible": accessibility_result["accessible"],
            "error": accessibility_result.get("error"),
            "details": accessibility_result.get("details"),
            "owner": owner,
            "repo": repo,
            "is_private": accessibility_result.get("is_private", False),
            "default_branch": accessibility_result.get("default_branch", "main")
        }
        
    except Exception as e:
        logger.error(f"GitHub validation failed for {github_url}: {str(e)}")
        return {
            "accessible": False,
            "error": "Validation failed",
            "details": str(e)
        }


def is_valid_github_url(url: str) -> bool:
    """
    Check if URL is a valid GitHub repository URL
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid GitHub repository URL
    """
    try:
        # GitHub URL patterns
        patterns = [
            r"^https://github\.com/[\w\-\.]+/[\w\-\.]+/?$",
            r"^git@github\.com:[\w\-\.]+/[\w\-\.]+\.git$",
            r"^https://github\.com/[\w\-\.]+/[\w\-\.]+\.git$"
        ]
        
        for pattern in patterns:
            if re.match(pattern, url.strip()):
                return True
        
        return False
        
    except Exception:
        return False


def extract_github_info(url: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract owner and repository name from GitHub URL
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repo) or (None, None) if extraction fails
    """
    try:
        # Normalize URL
        url = url.strip().rstrip('/')
        
        # Remove .git suffix if present
        if url.endswith('.git'):
            url = url[:-4]
        
        # Handle different URL formats
        if url.startswith('git@github.com:'):
            # SSH format: git@github.com:owner/repo.git
            path = url.replace('git@github.com:', '')
        elif url.startswith('https://github.com/'):
            # HTTPS format: https://github.com/owner/repo
            parsed = urlparse(url)
            path = parsed.path.lstrip('/')
        else:
            return None, None
        
        # Split path into owner and repo
        parts = path.split('/')
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1]
            
            # Validate owner and repo names
            if owner and repo and _is_valid_github_name(owner) and _is_valid_github_name(repo):
                return owner, repo
        
        return None, None
        
    except Exception as e:
        logger.error(f"Failed to extract GitHub info from {url}: {str(e)}")
        return None, None


def _is_valid_github_name(name: str) -> bool:
    """
    Validate GitHub username or repository name
    
    Args:
        name: Name to validate
        
    Returns:
        True if valid GitHub name
    """
    if not name or len(name) > 39:
        return False
    
    # GitHub names can contain alphanumeric characters, hyphens, and dots
    # Cannot start or end with hyphen or dot
    pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-\.])*[a-zA-Z0-9]$|^[a-zA-Z0-9]$"
    return bool(re.match(pattern, name))


async def check_repository_accessibility(owner: str, repo: str) -> Dict[str, Any]:
    """
    Check if GitHub repository is accessible
    
    Args:
        owner: Repository owner
        repo: Repository name
        
    Returns:
        Dict with accessibility information
    """
    try:
        # GitHub API URL
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        
        # Headers for GitHub API
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeFlowOps/1.0"
        }
        
        # Add GitHub token if available
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
        
        # Make API request
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(api_url, headers=headers)
        
        if response.status_code == 200:
            repo_data = response.json()
            return {
                "accessible": True,
                "is_private": repo_data.get("private", False),
                "default_branch": repo_data.get("default_branch", "main"),
                "size": repo_data.get("size", 0),
                "language": repo_data.get("language"),
                "fork": repo_data.get("fork", False),
                "archived": repo_data.get("archived", False)
            }
        elif response.status_code == 404:
            return {
                "accessible": False,
                "error": "Repository not found",
                "details": "Repository does not exist or is private without access"
            }
        elif response.status_code == 403:
            return {
                "accessible": False,
                "error": "Access forbidden",
                "details": "Repository is private or rate limit exceeded"
            }
        else:
            return {
                "accessible": False,
                "error": f"GitHub API error: {response.status_code}",
                "details": response.text
            }
            
    except httpx.TimeoutException:
        return {
            "accessible": False,
            "error": "Request timeout",
            "details": "GitHub API request timed out"
        }
    except Exception as e:
        logger.error(f"Failed to check repository accessibility: {str(e)}")
        return {
            "accessible": False,
            "error": "Accessibility check failed",
            "details": str(e)
        }


async def validate_github_token(token: str) -> Dict[str, Any]:
    """
    Validate GitHub personal access token
    
    Args:
        token: GitHub token to validate
        
    Returns:
        Dict with validation results
    """
    try:
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeFlowOps/1.0"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://api.github.com/user", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            return {
                "valid": True,
                "username": user_data.get("login"),
                "user_id": user_data.get("id"),
                "scopes": response.headers.get("X-OAuth-Scopes", "").split(", ") if response.headers.get("X-OAuth-Scopes") else []
            }
        elif response.status_code == 401:
            return {
                "valid": False,
                "error": "Invalid or expired token"
            }
        else:
            return {
                "valid": False,
                "error": f"GitHub API error: {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"GitHub token validation failed: {str(e)}")
        return {
            "valid": False,
            "error": str(e)
        }


def normalize_github_url(url: str) -> str:
    """
    Normalize GitHub URL to standard HTTPS format
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Normalized GitHub URL
    """
    try:
        owner, repo = extract_github_info(url)
        if owner and repo:
            return f"https://github.com/{owner}/{repo}"
        return url
    except Exception:
        return url


async def get_repository_languages(owner: str, repo: str) -> Dict[str, Any]:
    """
    Get programming languages used in repository
    
    Args:
        owner: Repository owner
        repo: Repository name
        
    Returns:
        Dict with language information
    """
    try:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeFlowOps/1.0"
        }
        
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(api_url, headers=headers)
        
        if response.status_code == 200:
            languages = response.json()
            total_bytes = sum(languages.values())
            
            # Calculate percentages
            language_stats = {}
            for lang, bytes_count in languages.items():
                percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
                language_stats[lang] = {
                    "bytes": bytes_count,
                    "percentage": round(percentage, 2)
                }
            
            # Sort by usage
            sorted_languages = dict(sorted(language_stats.items(), key=lambda x: x[1]["bytes"], reverse=True))
            
            return {
                "success": True,
                "languages": sorted_languages,
                "primary_language": list(sorted_languages.keys())[0] if sorted_languages else None,
                "total_bytes": total_bytes
            }
        else:
            return {
                "success": False,
                "error": f"Failed to fetch languages: {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get repository languages: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
