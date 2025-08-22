"""
Stage 1: Deep Repository Crawl
Exhaustive file system analysis - reads every file, every word
"""
import os
import re
import mimetypes
from pathlib import Path
from typing import Dict, List, Any
import logging
import chardet

from ..contracts import AnalysisContext, FileMetadata
from ..utils import calculate_file_hash, count_file_lines, detect_file_language, should_analyze_file, extract_file_metadata

logger = logging.getLogger(__name__)

class DeepCrawlStage:
    """
    Deep crawl stage - analyzes every file in the repository
    
    Responsibilities:
    - Recursive directory scan (including hidden files)
    - File metadata collection (size, hash, encoding, lines)
    - Binary vs text detection
    - Language detection
    - Content sampling for analysis
    """
    
    # Skip these directories for content analysis (but record their existence)
    SKIP_CONTENT_DIRS = {
        'node_modules', '.git', 'vendor', '__pycache__', '.venv', 'venv',
        'env', 'dist', 'build', 'target', '.next', '.cache', 'coverage',
        '.nyc_output', 'logs', 'tmp', 'temp', '.gradle', '.maven'
    }
    
    # Skip these files completely
    SKIP_FILES = {
        '.DS_Store', 'Thumbs.db', 'desktop.ini', '.gitkeep',
        'package-lock.json', 'yarn.lock', 'composer.lock', 'poetry.lock'
    }
    
    # Binary file extensions (don't read content)
    BINARY_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp',
        '.pdf', '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z',
        '.exe', '.dll', '.so', '.dylib', '.bin', '.deb', '.rpm',
        '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
        '.ttf', '.otf', '.woff', '.woff2', '.eot',
        '.psd', '.ai', '.sketch', '.fig'
    }
    
    # Large file threshold (25MB)
    LARGE_FILE_THRESHOLD = 25 * 1024 * 1024
    
    async def analyze(self, context: AnalysisContext):
        """Run deep crawl analysis"""
        logger.info(f"🔍 Deep crawling repository: {context.repo_path}")
        
        crawl_stats = {
            "total_items": 0,
            "files_analyzed": 0,
            "directories_found": 0,
            "binary_files": 0,
            "large_files_skipped": 0,
            "content_read_files": 0,
            "total_size_bytes": 0,
            "languages_detected": set(),
            "file_types": {}
        }
        
        # Walk entire repository tree
        for root, dirs, files in os.walk(context.repo_path):
            # Get relative path
            rel_root = os.path.relpath(root, context.repo_path)
            if rel_root == '.':
                rel_root = ''
                
            crawl_stats["directories_found"] += len(dirs)
            crawl_stats["total_items"] += len(dirs) + len(files)
            
            # Filter out skip directories for content analysis
            # But still record their existence
            for skip_dir in self.SKIP_CONTENT_DIRS:
                if skip_dir in dirs:
                    skip_path = os.path.join(root, skip_dir)
                    skip_size = self._get_directory_size(skip_path)
                    crawl_stats["total_size_bytes"] += skip_size
                    logger.debug(f"📁 Skipped content analysis for {skip_dir} ({skip_size} bytes)")
            
            # Remove skip dirs from dirs list to prevent os.walk from entering them
            dirs[:] = [d for d in dirs if d not in self.SKIP_CONTENT_DIRS]
            
            # Analyze each file
            for file_name in files:
                if file_name in self.SKIP_FILES:
                    continue
                    
                file_path = Path(root) / file_name
                rel_path = str(file_path.relative_to(context.repo_path))
                
                try:
                    file_metadata = await self._analyze_file(file_path, rel_path, crawl_stats)
                    if file_metadata:
                        context.files.append(file_metadata)
                        crawl_stats["files_analyzed"] += 1
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to analyze {rel_path}: {e}")
        
        # Store crawl results in context
        context.intelligence_profile["file_intelligence"] = {
            "crawl_stats": {
                k: list(v) if isinstance(v, set) else v 
                for k, v in crawl_stats.items()
            },
            "files": context.files,
            "directory_structure": self._build_directory_tree(context.repo_path),
            "file_type_distribution": crawl_stats["file_types"],
            "language_breakdown": {lang: 1 for lang in crawl_stats["languages_detected"]} if crawl_stats["languages_detected"] else {}
        }
        
        logger.info(f"✅ Deep crawl complete: {crawl_stats['files_analyzed']} files, {len(crawl_stats['languages_detected'])} languages")
    
    async def _analyze_file(self, file_path: Path, rel_path: str, stats: Dict[str, Any]) -> FileMetadata:
        """Analyze individual file"""
        try:
            # Get file stats
            stat = file_path.stat()
            file_size = stat.st_size
            stats["total_size_bytes"] += file_size
            
            # Skip large files for content analysis
            if file_size > self.LARGE_FILE_THRESHOLD:
                stats["large_files_skipped"] += 1
                return self._create_file_metadata(file_path, rel_path, file_size, is_large=True)
            
            # Detect if binary
            ext = file_path.suffix.lower()
            is_binary = ext in self.BINARY_EXTENSIONS
            
            if is_binary:
                stats["binary_files"] += 1
                return self._create_file_metadata(file_path, rel_path, file_size, is_binary=True)
            
            # For text files, detect encoding and read content
            encoding = self._detect_encoding(file_path)
            lines = count_file_lines(file_path)
            language = detect_file_language(file_path)
            
            # Update statistics
            stats["content_read_files"] += 1
            stats["languages_detected"].add(language)
            
            # Track file types
            if ext not in stats["file_types"]:
                stats["file_types"][ext] = 0
            stats["file_types"][ext] += 1
            
            return self._create_file_metadata(
                file_path, rel_path, file_size, 
                encoding=encoding, lines=lines, language=language
            )
            
        except Exception as e:
            logger.warning(f"File analysis failed for {rel_path}: {e}")
            return None
    
    def _create_file_metadata(self, file_path: Path, rel_path: str, size: int, 
                             is_binary: bool = False, is_large: bool = False,
                             encoding: str = "unknown", lines: int = 0, 
                             language: str = "Unknown") -> FileMetadata:
        """Create file metadata object"""
        return {
            "path": rel_path,
            "name": file_path.name,
            "extension": file_path.suffix.lower(),
            "size": size,
            "hash": calculate_file_hash(file_path) if not is_large else "large_file",
            "lines": lines,
            "language": language,
            "is_binary": is_binary,
            "encoding": encoding,
            "mtime": file_path.stat().st_mtime.__str__()
        }
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(8192)  # Read first 8KB
                result = chardet.detect(raw_data)
                return result.get('encoding', 'utf-8') or 'utf-8'
        except:
            return 'utf-8'
    
    def _get_directory_size(self, dir_path: str) -> int:
        """Calculate total size of directory"""
        total_size = 0
        try:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                    except:
                        continue
        except:
            pass
        return total_size
    
    def _build_directory_tree(self, repo_path: Path) -> Dict[str, Any]:
        """Build directory tree structure"""
        tree = {"name": repo_path.name, "type": "directory", "children": []}
        
        try:
            for item in repo_path.iterdir():
                if item.name.startswith('.git'):
                    continue
                    
                if item.is_dir():
                    tree["children"].append({
                        "name": item.name,
                        "type": "directory",
                        "path": str(item.relative_to(repo_path))
                    })
                else:
                    tree["children"].append({
                        "name": item.name,
                        "type": "file",
                        "path": str(item.relative_to(repo_path)),
                        "size": item.stat().st_size
                    })
        except Exception as e:
            logger.warning(f"Failed to build directory tree: {e}")
        
        return tree
