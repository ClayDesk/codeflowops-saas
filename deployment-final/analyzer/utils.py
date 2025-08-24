"""
Analyzer Utilities
Shared utility functions for the analyzer stages
"""
import hashlib
import mimetypes
import os
import re
from pathlib import Path
from typing import Optional


def calculate_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of a file"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return "unknown"


def count_file_lines(file_path: Path) -> int:
    """Count lines in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def detect_file_language(file_path: Path) -> str:
    """Detect programming language from file extension and content"""
    extension = file_path.suffix.lower()
    
    # Language mappings
    language_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React JSX',
        '.tsx': 'React TSX',
        '.php': 'PHP',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.cs': 'C#',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.clj': 'Clojure',
        '.hs': 'Haskell',
        '.ml': 'OCaml',
        '.elm': 'Elm',
        '.dart': 'Dart',
        '.lua': 'Lua',
        '.r': 'R',
        '.m': 'Objective-C',
        '.pl': 'Perl',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.zsh': 'Zsh',
        '.fish': 'Fish',
        '.ps1': 'PowerShell',
        '.bat': 'Batch',
        '.cmd': 'Command',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.xml': 'XML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.less': 'Less',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
        '.ini': 'INI',
        '.cfg': 'Config',
        '.conf': 'Config',
        '.sql': 'SQL',
        '.md': 'Markdown',
        '.rst': 'reStructuredText',
        '.tex': 'LaTeX',
        '.dockerfile': 'Dockerfile',
        '.dockerignore': 'Docker',
        '.gitignore': 'Git',
        '.gitattributes': 'Git',
        '.env': 'Environment',
        '.lock': 'Lock File',
    }
    
    if extension in language_map:
        return language_map[extension]
    
    # Check for files without extensions but with known names
    filename = file_path.name.lower()
    if filename in ['dockerfile', 'makefile', 'rakefile', 'gemfile', 'podfile']:
        return filename.title()
    
    # Use mimetype as fallback
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type:
        if 'text' in mime_type:
            return 'Text'
        elif 'image' in mime_type:
            return 'Image'
        elif 'video' in mime_type:
            return 'Video'
        elif 'audio' in mime_type:
            return 'Audio'
        elif 'application' in mime_type:
            return 'Binary'
    
    return 'Unknown'


def is_text_file(file_path: Path) -> bool:
    """Check if a file is likely a text file"""
    try:
        # Check by extension first
        text_extensions = {
            '.txt', '.md', '.rst', '.py', '.js', '.ts', '.jsx', '.tsx',
            '.php', '.java', '.cpp', '.c', '.cs', '.rb', '.go', '.rs',
            '.html', '.htm', '.xml', '.css', '.scss', '.sass', '.less',
            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.sql', '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat',
            '.cmd', '.dockerfile', '.gitignore', '.env', '.lock'
        }
        
        if file_path.suffix.lower() in text_extensions:
            return True
        
        # Check by filename
        text_filenames = {
            'dockerfile', 'makefile', 'rakefile', 'gemfile', 'podfile',
            'readme', 'license', 'changelog', 'authors', 'contributors'
        }
        
        if file_path.name.lower() in text_filenames:
            return True
        
        # Check mimetype
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and 'text' in mime_type:
            return True
        
        # Try to read a small portion to detect if it's text
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                if not chunk:
                    return True  # Empty file is considered text
                
                # Check for null bytes (binary indicator)
                if b'\x00' in chunk:
                    return False
                
                # Try to decode as UTF-8
                try:
                    chunk.decode('utf-8')
                    return True
                except UnicodeDecodeError:
                    return False
        except Exception:
            return False
            
    except Exception:
        return False


def is_source_code_file(file_path: Path) -> bool:
    """Check if a file is source code"""
    source_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.php', '.java', '.cpp',
        '.c', '.cs', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
        '.clj', '.hs', '.ml', '.elm', '.dart', '.lua', '.r', '.m',
        '.pl', '.sh', '.bash', '.zsh', '.fish', '.ps1'
    }
    
    return file_path.suffix.lower() in source_extensions


def should_analyze_file(file_path: Path) -> bool:
    """Determine if a file should be analyzed"""
    # Skip hidden files and directories
    if any(part.startswith('.') for part in file_path.parts):
        # But allow some important dotfiles
        important_dotfiles = {
            '.env', '.gitignore', '.gitattributes', '.dockerignore',
            '.editorconfig', '.eslintrc', '.prettierrc', '.babelrc'
        }
        if file_path.name not in important_dotfiles:
            return False
    
    # Skip common build/cache directories
    skip_dirs = {
        'node_modules', '__pycache__', '.git', '.svn', '.hg',
        'build', 'dist', 'target', 'bin', 'obj', 'out',
        '.vscode', '.idea', '.vs', 'vendor', 'composer',
        '.pytest_cache', '.coverage', 'htmlcov'
    }
    
    if any(part in skip_dirs for part in file_path.parts):
        return False
    
    # Skip large files (> 10MB)
    try:
        if file_path.stat().st_size > 10 * 1024 * 1024:
            return False
    except Exception:
        pass
    
    # Skip binary files for deep analysis
    if not is_text_file(file_path):
        return False
    
    return True


def extract_file_metadata(file_path: Path) -> dict:
    """Extract basic metadata from a file"""
    try:
        stat = file_path.stat()
        return {
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'language': detect_file_language(file_path),
            'is_text': is_text_file(file_path),
            'is_source': is_source_code_file(file_path),
            'hash': calculate_file_hash(file_path),
            'lines': count_file_lines(file_path) if is_text_file(file_path) else 0
        }
    except Exception as e:
        return {
            'size': 0,
            'modified': 0,
            'language': 'Unknown',
            'is_text': False,
            'is_source': False,
            'hash': 'unknown',
            'lines': 0,
            'error': str(e)
        }
