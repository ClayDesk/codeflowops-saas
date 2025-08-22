"""
Documentation-Only Repository Detector
Detects repositories that contain only documentation files (.md, .txt, .rst, etc.)
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class DocumentationDetector:
    """Detect repositories that are documentation-only (not deployable applications)"""
    
    DOCUMENTATION_EXTENSIONS = {'.md', '.txt', '.rst', '.adoc', '.org', '.pdf', '.doc', '.docx'}
    IGNORE_EXTENSIONS = {'.git', '.gitignore', '.gitattributes', '.github'}
    CONFIG_EXTENSIONS = {'.yml', '.yaml', '.json', '.xml', '.ini', '.cfg', '.toml'}
    
    def detect(self, file_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect if repository is documentation-only
        
        Returns:
            Dict with detection results or None if not documentation-only
        """
        file_types = file_analysis.get('file_types', {})
        total_files = file_analysis.get('total_files', 0)
        source_files_count = file_analysis.get('source_files_count', 0)
        
        if total_files == 0:
            return None
            
        # Count documentation files
        doc_files = 0
        config_files = 0
        other_files = 0
        
        for ext, count in file_types.items():
            if ext.lower() in self.DOCUMENTATION_EXTENSIONS:
                doc_files += count
            elif ext.lower() in self.CONFIG_EXTENSIONS:
                config_files += count
            elif ext.lower() not in self.IGNORE_EXTENSIONS:
                other_files += count
        
        # Calculate percentages
        doc_percentage = (doc_files / total_files) * 100 if total_files > 0 else 0
        
        logger.info(f"📄 Documentation analysis: {doc_files} doc files ({doc_percentage:.1f}%), {config_files} config files, {other_files} other files")
        
        # Repository is documentation-only if:
        # 1. >80% of files are documentation files
        # 2. No source code files detected  
        # 3. Remaining files are just config/meta files
        is_documentation_only = (
            doc_percentage >= 80 and
            source_files_count == 0 and
            other_files <= 2  # Allow a few config files
        )
        
        if is_documentation_only:
            return {
                "framework": "documentation",
                "project_type": "documentation_only",
                "detected_framework": "documentation",
                "is_build_ready": False,
                "build_tool": "none",
                "entry_point": None,
                "confidence": 0.95,
                "detection_reason": f"Repository contains {doc_files} documentation files ({doc_percentage:.1f}%) with no deployable source code",
                "recommended_stack": {
                    "stack_type": "documentation_only",
                    "deployment_method": "github_pages",
                    "compute": "Static Site Generator (optional)",
                    "description": "Documentation-only repository - consider GitHub Pages for hosting"
                },
                "deployment_suggestions": [
                    "This repository contains only documentation files",
                    "Consider using GitHub Pages, GitBook, or Docusaurus for hosting",
                    "Not suitable for application deployment",
                    f"Found {doc_files} documentation files (.md, .txt, .rst, etc.)",
                    "No source code or deployable application detected"
                ]
            }
        
        return None
    
    def get_detection_priority(self) -> int:
        """Return detection priority (higher = runs earlier)"""
        return 100  # Run early to catch documentation repos before other detectors
