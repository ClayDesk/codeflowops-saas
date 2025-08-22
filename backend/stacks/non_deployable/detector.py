"""
Non-Deployable Repository Detector
Identifies repositories that are tools, libraries, or not meant for web deployment
"""
from pathlib import Path
from typing import Optional, Dict, Any
from core.models import StackPlan
from core.utils import find_files, check_file_exists

class NonDeployableDetector:
    """Detects repositories that are not meant for web deployment"""
    
    def detect(self, repo_dir: Path) -> Optional[StackPlan]:
        """
        Detect if repository is not deployable and provide detailed explanation
        """
        
        # Check for CLI tools and infrastructure tools
        non_deployable_result = self._analyze_non_deployable(repo_dir)
        if non_deployable_result:
            return StackPlan(
                stack_key="non_deployable",
                build_cmds=[],
                output_dir=repo_dir,
                config=non_deployable_result
            )
            
        return None
    
    def _analyze_non_deployable(self, repo_dir: Path) -> Optional[Dict[str, Any]]:
        """Analyze if repository is non-deployable and why"""
        
        # Get file counts
        file_counts = self._count_file_types(repo_dir)
        total_files = sum(file_counts.values())
        
        if total_files == 0:
            return None
        
        # 1. Infrastructure-as-Code Tools (Terraform, Pulumi, etc.)
        terraform_result = self._check_terraform(file_counts, repo_dir)
        if terraform_result:
            return terraform_result
            
        # 2. Go CLI Tools
        go_cli_result = self._check_go_cli_tool(file_counts, repo_dir)
        if go_cli_result:
            return go_cli_result
            
        # 3. System Libraries/SDKs
        library_result = self._check_system_library(file_counts, repo_dir)
        if library_result:
            return library_result
            
        # 4. Configuration/Dotfiles
        config_result = self._check_configuration_repo(file_counts, repo_dir)
        if config_result:
            return config_result
            
        return None
    
    def _check_terraform(self, file_counts: Dict[str, int], repo_dir: Path) -> Optional[Dict[str, Any]]:
        """Check if this is Terraform Core or similar IaC tool"""
        
        tf_files = file_counts.get('.tf', 0)
        go_files = file_counts.get('.go', 0) 
        hcl_files = file_counts.get('.hcl', 0)
        
        # Terraform Core pattern: Many Go files + TF files + HCL files
        if go_files > 1000 and tf_files > 500 and hcl_files > 100:
            return {
                "type": "infrastructure_tool",
                "tool_name": "Terraform Core",
                "language": "Go",
                "deployable": False,
                "reason": "Infrastructure-as-Code Engine",
                "explanation": "This repository contains Terraform Core - the CLI tool for infrastructure provisioning. It's not a web application but rather a command-line tool that you install and use to manage cloud infrastructure.",
                "usage_instructions": [
                    "Download pre-built binaries from GitHub Releases",
                    "Install via package manager (brew install terraform, apt install terraform, etc.)",
                    "Use 'terraform init', 'terraform plan', 'terraform apply' commands",
                    "Create your own .tf configuration files to define infrastructure"
                ],
                "what_to_deploy_instead": "Create Terraform configuration files (.tf) that use this tool to deploy your actual infrastructure resources to AWS, Azure, GCP, etc.",
                "codeflowops_message": "CodeFlowOps specializes in deploying WEB APPLICATIONS (React, Next.js, Laravel, Python/Django, Static Sites, APIs). This repository contains infrastructure tooling.",
                "file_breakdown": {
                    "go_files": go_files,
                    "tf_files": tf_files, 
                    "hcl_files": hcl_files,
                    "purpose": "Core engine and test configurations"
                }
            }
        
        # Other IaC tools
        if tf_files > 10 and go_files < 100:
            return {
                "type": "infrastructure_configuration",
                "tool_name": "Terraform Configuration",
                "deployable": False,
                "reason": "Infrastructure Configuration Repository",
                "explanation": "This appears to be a Terraform configuration repository containing infrastructure definitions, not a deployable application.",
                "usage_instructions": [
                    "Install Terraform CLI tool separately",
                    "Run 'terraform init' to initialize",
                    "Run 'terraform plan' to preview changes", 
                    "Run 'terraform apply' to create infrastructure"
                ],
                "codeflowops_message": "CodeFlowOps deploys WEB APPLICATIONS. For infrastructure management, use this Terraform configuration with the Terraform CLI tool."
            }
            
        return None
    
    def _check_go_cli_tool(self, file_counts: Dict[str, int], repo_dir: Path) -> Optional[Dict[str, Any]]:
        """Check if this is a Go CLI tool"""
        
        go_files = file_counts.get('.go', 0)
        total_files = sum(file_counts.values())
        
        # High ratio of Go files suggests CLI tool
        if go_files > 50 and (go_files / total_files) > 0.3:
            
            # Check for CLI indicators
            has_main_go = check_file_exists(repo_dir, "main.go")
            has_cmd_dir = (repo_dir / "cmd").exists()
            
            if has_main_go or has_cmd_dir:
                return {
                    "type": "cli_tool", 
                    "language": "Go",
                    "deployable": False,
                    "reason": "Command-Line Tool",
                    "explanation": "This is a Go-based command-line tool meant to be installed and run locally, not deployed as a web service.",
                    "usage_instructions": [
                        "Install Go programming language",
                        "Clone the repository",
                        "Run 'go build' to compile the binary",
                        "Run the resulting executable from command line"
                    ],
                    "codeflowops_message": "CodeFlowOps specializes in WEB APPLICATION deployment (React, Next.js, Laravel, Python/Django, Static Sites). This is a command-line tool.",
                    "file_breakdown": {
                        "go_files": go_files,
                        "has_main": has_main_go,
                        "has_cmd_structure": has_cmd_dir
                    }
                }
                
        return None
    
    def _check_system_library(self, file_counts: Dict[str, int], repo_dir: Path) -> Optional[Dict[str, Any]]:
        """Check if this is a system library or SDK"""
        
        # Check for library indicators
        has_setup_py = check_file_exists(repo_dir, "setup.py")
        has_lib_dir = (repo_dir / "lib").exists()
        has_src_dir = (repo_dir / "src").exists()
        
        py_files = file_counts.get('.py', 0)
        js_files = file_counts.get('.js', 0)
        
        # Python library pattern
        if has_setup_py and py_files > 20 and not check_file_exists(repo_dir, "app.py") and not check_file_exists(repo_dir, "main.py"):
            return {
                "type": "python_library",
                "language": "Python", 
                "deployable": False,
                "reason": "Python Library/Package",
                "explanation": "This is a Python library or package meant to be installed and imported by other applications, not deployed as a standalone web service.",
                "usage_instructions": [
                    "Install with 'pip install .' or 'pip install git+<repo_url>'",
                    "Import in your Python applications",
                    "Use the library's API in your own code"
                ]
            }
            
        return None
    
    def _check_configuration_repo(self, file_counts: Dict[str, int], repo_dir: Path) -> Optional[Dict[str, Any]]:
        """Check if this is a configuration/dotfiles repository"""
        
        config_extensions = ['.conf', '.config', '.yml', '.yaml', '.toml', '.ini']
        config_file_count = sum(file_counts.get(ext, 0) for ext in config_extensions)
        
        total_files = sum(file_counts.values())
        
        if config_file_count > 10 and (config_file_count / total_files) > 0.5:
            return {
                "type": "configuration_repository",
                "deployable": False,
                "reason": "Configuration Repository", 
                "explanation": "This appears to be a configuration repository (dotfiles, system configs, etc.) rather than a deployable application.",
                "usage_instructions": [
                    "Clone repository to your local machine",
                    "Copy configuration files to appropriate system locations",
                    "Follow repository's specific setup instructions"
                ]
            }
            
        return None
    
    def _count_file_types(self, repo_dir: Path) -> Dict[str, int]:
        """Count files by extension"""
        file_counts = {}
        
        for file_path in repo_dir.rglob('*'):
            if file_path.is_file() and not any(part.startswith('.git') for part in file_path.parts):
                ext = file_path.suffix.lower()
                file_counts[ext] = file_counts.get(ext, 0) + 1
                
        return file_counts
    
    def get_priority(self) -> int:
        """Non-deployable detection should run early to catch obvious cases"""
        return 60  # Higher than all other detectors
