"""
Analysis Reporter
Orchestrates the complete repository analysis and generates comprehensive reports
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from .repository_analyzer import RepositoryAnalyzer, AnalysisResult
from .project_type_detector import ProjectTypeDetector, ProjectTypeResult
from .dependency_analyzer import DependencyAnalyzer, DependencyAnalysis

logger = logging.getLogger(__name__)

@dataclass
class AnalysisSession:
    """Analysis session tracking"""
    session_id: str
    repository_url: str
    status: str  # 'pending', 'analyzing', 'completed', 'failed'
    progress: float  # 0.0 to 100.0
    current_phase: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

@dataclass
class ComprehensiveAnalysisResult:
    """Complete analysis result combining all analysis components"""
    session_id: str
    repository_url: str
    analysis_timestamp: str
    
    # Repository structure analysis
    repository_analysis: AnalysisResult
    
    # Project type detection results
    project_types: List[ProjectTypeResult]
    primary_project_type: Optional[ProjectTypeResult]
    
    # Dependency analysis
    dependency_analysis: DependencyAnalysis
    
    # Overall assessment
    overall_confidence: float
    deployment_readiness_score: float
    complexity_score: float
    
    # Issues and recommendations
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    
    # Missing files for deployment
    missing_files: List[str]
    
    # Suggested build configuration
    suggested_build_config: Dict[str, Any]
    
    # Performance and resource estimates
    estimated_build_time: str
    estimated_resource_usage: Dict[str, str]

class AnalysisReporter:
    """
    Main orchestrator for comprehensive repository analysis
    """
    
    def __init__(self):
        self.repository_analyzer = RepositoryAnalyzer()
        self.project_type_detector = ProjectTypeDetector()
        self.dependency_analyzer = DependencyAnalyzer()
        self.active_sessions: Dict[str, AnalysisSession] = {}

    async def start_analysis(self, repository_url: str) -> str:
        """
        Start a new analysis session
        """
        session_id = str(uuid.uuid4())
        
        session = AnalysisSession(
            session_id=session_id,
            repository_url=repository_url,
            status='pending',
            progress=0.0,
            current_phase='initializing',
            started_at=datetime.utcnow()
        )
        
        self.active_sessions[session_id] = session
        
        logger.info(f"Started analysis session {session_id} for {repository_url}")
        return session_id

    async def run_comprehensive_analysis(self, session_id: str) -> ComprehensiveAnalysisResult:
        """
        Run complete repository analysis
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Analysis session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        try:
            session.status = 'analyzing'
            session.current_phase = 'repository_structure'
            session.progress = 10.0
            
            logger.info(f"Starting comprehensive analysis for session {session_id}")
            
            # Phase 1: Repository Structure Analysis
            repository_analysis = await self._analyze_repository_structure(session)
            session.progress = 30.0
            
            # Phase 2: Project Type Detection
            session.current_phase = 'project_type_detection'
            project_types, primary_type = await self._detect_project_types(session, repository_analysis)
            session.progress = 50.0
            
            # Phase 3: Dependency Analysis
            session.current_phase = 'dependency_analysis'
            dependency_analysis = await self._analyze_dependencies(session, repository_analysis)
            session.progress = 70.0
            
            # Phase 4: Comprehensive Assessment
            session.current_phase = 'assessment'
            comprehensive_result = await self._generate_comprehensive_assessment(
                session, repository_analysis, project_types, primary_type, dependency_analysis
            )
            session.progress = 100.0
            
            # Complete session
            session.status = 'completed'
            session.current_phase = 'completed'
            session.completed_at = datetime.utcnow()
            
            logger.info(f"Completed analysis for session {session_id}")
            return comprehensive_result
            
        except Exception as e:
            session.status = 'failed'
            session.error_message = str(e)
            logger.error(f"Analysis failed for session {session_id}: {str(e)}")
            raise

    async def get_analysis_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get current analysis status
        """
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        session = self.active_sessions[session_id]
        
        return {
            'session_id': session.session_id,
            'status': session.status,
            'progress': session.progress,
            'current_phase': session.current_phase,
            'started_at': session.started_at.isoformat(),
            'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            'error_message': session.error_message
        }

    async def _analyze_repository_structure(self, session: AnalysisSession) -> AnalysisResult:
        """
        Phase 1: Analyze repository structure
        """
        logger.info(f"Analyzing repository structure for {session.repository_url}")
        
        try:
            result = await self.repository_analyzer.analyze_repository(
                session.repository_url, 
                session.session_id
            )
            return result
        except Exception as e:
            logger.error(f"Repository structure analysis failed: {str(e)}")
            raise

    async def _detect_project_types(self, session: AnalysisSession, 
                                  repository_analysis: AnalysisResult) -> tuple[List[ProjectTypeResult], Optional[ProjectTypeResult]]:
        """
        Phase 2: Detect project types
        """
        logger.info(f"Detecting project types for session {session.session_id}")
        
        try:
            # Convert file tree to format expected by detector
            file_tree = [asdict(f) for f in repository_analysis.file_tree]
            
            # Get package.json content if available
            package_json_content = None
            for dep_info in repository_analysis.dependencies:
                if dep_info.manager == 'npm':
                    # In a real implementation, we'd fetch the actual package.json content
                    # For now, we'll reconstruct it from dependency info
                    package_json_content = json.dumps({
                        'dependencies': dep_info.dependencies,
                        'devDependencies': dep_info.dev_dependencies or {},
                        'scripts': dep_info.scripts or {}
                    })
                    break
            
            project_types = self.project_type_detector.detect_project_types(
                file_tree, package_json_content
            )
            
            primary_type = project_types[0] if project_types else None
            
            return project_types, primary_type
            
        except Exception as e:
            logger.error(f"Project type detection failed: {str(e)}")
            raise

    async def _analyze_dependencies(self, session: AnalysisSession, 
                                  repository_analysis: AnalysisResult) -> DependencyAnalysis:
        """
        Phase 3: Analyze dependencies
        """
        logger.info(f"Analyzing dependencies for session {session.session_id}")
        
        try:
            # Convert file tree to format expected by analyzer
            file_tree = [asdict(f) for f in repository_analysis.file_tree]
            
            # For now, we'll use mock file contents
            # In a real implementation, we'd fetch actual file contents
            file_contents = {}
            
            dependency_analysis = await self.dependency_analyzer.analyze_dependencies(
                file_tree, file_contents
            )
            
            return dependency_analysis
            
        except Exception as e:
            logger.error(f"Dependency analysis failed: {str(e)}")
            raise

    async def _generate_comprehensive_assessment(self, session: AnalysisSession,
                                               repository_analysis: AnalysisResult,
                                               project_types: List[ProjectTypeResult],
                                               primary_type: Optional[ProjectTypeResult],
                                               dependency_analysis: DependencyAnalysis) -> ComprehensiveAnalysisResult:
        """
        Phase 4: Generate comprehensive assessment
        """
        logger.info(f"Generating comprehensive assessment for session {session.session_id}")
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            repository_analysis, project_types, dependency_analysis
        )
        
        # Calculate deployment readiness score
        deployment_readiness = self._calculate_deployment_readiness(
            repository_analysis, primary_type, dependency_analysis
        )
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(
            repository_analysis, dependency_analysis
        )
        
        # Identify critical issues
        critical_issues = self._identify_critical_issues(
            repository_analysis, primary_type, dependency_analysis
        )
        
        # Generate warnings
        warnings = self._generate_warnings(
            repository_analysis, dependency_analysis
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            repository_analysis, primary_type, dependency_analysis
        )
        
        # Suggest build configuration
        build_config = self._suggest_build_configuration(
            primary_type, dependency_analysis
        )
        
        # Estimate build time and resources
        build_estimates = self._estimate_build_requirements(
            repository_analysis, primary_type, dependency_analysis
        )
        
        return ComprehensiveAnalysisResult(
            session_id=session.session_id,
            repository_url=session.repository_url,
            analysis_timestamp=datetime.utcnow().isoformat(),
            repository_analysis=repository_analysis,
            project_types=project_types,
            primary_project_type=primary_type,
            dependency_analysis=dependency_analysis,
            overall_confidence=overall_confidence,
            deployment_readiness_score=deployment_readiness,
            complexity_score=complexity_score,
            critical_issues=critical_issues,
            warnings=warnings,
            recommendations=recommendations,
            missing_files=repository_analysis.missing_files,
            suggested_build_config=build_config,
            estimated_build_time=build_estimates['build_time'],
            estimated_resource_usage=build_estimates['resource_usage']
        )

    def _calculate_overall_confidence(self, repository_analysis: AnalysisResult,
                                    project_types: List[ProjectTypeResult],
                                    dependency_analysis: DependencyAnalysis) -> float:
        """Calculate overall analysis confidence"""
        confidence_factors = []
        
        # Repository analysis confidence
        confidence_factors.append(repository_analysis.confidence_score)
        
        # Project type detection confidence
        if project_types:
            confidence_factors.append(project_types[0].confidence)
        else:
            confidence_factors.append(0.0)
        
        # Dependency analysis confidence (based on number of package managers found)
        dep_confidence = min(len(dependency_analysis.package_managers) * 25, 100)
        confidence_factors.append(dep_confidence)
        
        return sum(confidence_factors) / len(confidence_factors)

    def _calculate_deployment_readiness(self, repository_analysis: AnalysisResult,
                                      primary_type: Optional[ProjectTypeResult],
                                      dependency_analysis: DependencyAnalysis) -> float:
        """Calculate deployment readiness score"""
        score = 0.0
        
        # Base score for having a recognized project type
        if primary_type:
            score += 30.0
        
        # Boost for having build configuration
        if primary_type and primary_type.build_command:
            score += 20.0
        
        # Boost for having dependencies properly configured
        if dependency_analysis.total_dependencies > 0:
            score += 15.0
        
        # Boost for having essential files
        essential_files = ['README.md', '.gitignore']
        found_essential = len([f for f in repository_analysis.config_files if f in essential_files])
        score += (found_essential / len(essential_files)) * 10
        
        # Penalty for missing critical files
        score -= len(repository_analysis.missing_files) * 5
        
        # Penalty for vulnerable dependencies
        score -= dependency_analysis.vulnerable_count * 3
        
        # Penalty for too many warnings
        score -= len(dependency_analysis.analysis_warnings) * 2
        
        return max(0.0, min(100.0, score))

    def _calculate_complexity_score(self, repository_analysis: AnalysisResult,
                                   dependency_analysis: DependencyAnalysis) -> float:
        """Calculate project complexity score"""
        score = 0.0
        
        # Base complexity from file count
        file_count = repository_analysis.total_files
        if file_count > 100:
            score += 30.0
        elif file_count > 50:
            score += 20.0
        elif file_count > 20:
            score += 10.0
        
        # Complexity from dependencies
        dep_count = dependency_analysis.total_dependencies
        if dep_count > 50:
            score += 25.0
        elif dep_count > 20:
            score += 15.0
        elif dep_count > 10:
            score += 10.0
        
        # Complexity from multiple package managers
        if len(dependency_analysis.package_managers) > 1:
            score += 15.0
        
        # Complexity from build tools
        if len(repository_analysis.build_tools) > 1:
            score += 10.0
        
        return min(100.0, score)

    def _identify_critical_issues(self, repository_analysis: AnalysisResult,
                                primary_type: Optional[ProjectTypeResult],
                                dependency_analysis: DependencyAnalysis) -> List[str]:
        """Identify critical issues that prevent deployment"""
        issues = []
        
        # No project type detected
        if not primary_type:
            issues.append("Unable to determine project type - manual configuration required")
        
        # Missing essential files
        if repository_analysis.missing_files:
            issues.extend([f"Missing critical file: {file}" for file in repository_analysis.missing_files[:3]])
        
        # Vulnerable dependencies
        if dependency_analysis.vulnerable_count > 0:
            issues.append(f"{dependency_analysis.vulnerable_count} vulnerable dependencies found")
        
        # No build command for non-static projects
        if primary_type and primary_type.type != 'Static Site' and not primary_type.build_command:
            issues.append("No build command detected - deployment may fail")
        
        return issues

    def _generate_warnings(self, repository_analysis: AnalysisResult,
                         dependency_analysis: DependencyAnalysis) -> List[str]:
        """Generate analysis warnings"""
        warnings = []
        
        # Add dependency analysis warnings
        warnings.extend(dependency_analysis.analysis_warnings)
        
        # Large repository warning
        if repository_analysis.total_files > 500:
            warnings.append("Large repository - consider excluding unnecessary files")
        
        # Many outdated dependencies
        if dependency_analysis.outdated_count > 10:
            warnings.append(f"{dependency_analysis.outdated_count} outdated dependencies detected")
        
        # Multiple package managers
        if len(dependency_analysis.package_managers) > 1:
            warnings.append("Multiple package managers detected - ensure consistency")
        
        return warnings

    def _generate_recommendations(self, repository_analysis: AnalysisResult,
                                primary_type: Optional[ProjectTypeResult],
                                dependency_analysis: DependencyAnalysis) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Add dependency analysis recommendations
        recommendations.extend(dependency_analysis.recommendations)
        
        # Missing README
        if 'README.md' not in repository_analysis.config_files:
            recommendations.append("Add README.md with project documentation")
        
        # Missing .gitignore
        if '.gitignore' not in repository_analysis.config_files:
            recommendations.append("Add .gitignore to exclude build artifacts")
        
        # No tests detected
        test_files = [f for f in repository_analysis.file_tree if f.is_test]
        if not test_files:
            recommendations.append("Consider adding automated tests")
        
        # Performance recommendations
        if dependency_analysis.total_dependencies > 100:
            recommendations.append("Consider reducing dependencies for faster builds")
        
        return recommendations

    def _suggest_build_configuration(self, primary_type: Optional[ProjectTypeResult],
                                   dependency_analysis: DependencyAnalysis) -> Dict[str, Any]:
        """Suggest optimal build configuration"""
        config = {
            'build_command': '',
            'output_directory': '',
            'install_command': '',
            'development_server': '',
            'environment_variables': {},
            'docker_base_image': ''
        }
        
        if not primary_type:
            return config
        
        # Use detected build configuration
        config['build_command'] = primary_type.build_command or ''
        config['output_directory'] = primary_type.output_directory or ''
        config['development_server'] = primary_type.development_server or ''
        
        # Suggest install command based on package manager
        if 'npm' in dependency_analysis.package_managers:
            config['install_command'] = 'npm ci' if 'package-lock.json' in dependency_analysis.package_managers else 'npm install'
            config['docker_base_image'] = 'node:18-alpine'
        elif 'pip' in dependency_analysis.package_managers:
            config['install_command'] = 'pip install -r requirements.txt'
            config['docker_base_image'] = 'python:3.11-slim'
        
        # Suggest environment variables
        if primary_type.type == 'React':
            config['environment_variables']['NODE_ENV'] = 'production'
            config['environment_variables']['GENERATE_SOURCEMAP'] = 'false'
        elif primary_type.type == 'Next.js':
            config['environment_variables']['NODE_ENV'] = 'production'
        
        return config

    def _estimate_build_requirements(self, repository_analysis: AnalysisResult,
                                   primary_type: Optional[ProjectTypeResult],
                                   dependency_analysis: DependencyAnalysis) -> Dict[str, Any]:
        """Estimate build time and resource requirements"""
        
        # Base estimates
        build_time = "2-5 minutes"
        cpu_requirement = "1 vCPU"
        memory_requirement = "1 GB"
        storage_requirement = "2 GB"
        
        # Adjust based on project complexity
        if dependency_analysis.total_dependencies > 50:
            build_time = "5-10 minutes"
            memory_requirement = "2 GB"
        
        if dependency_analysis.total_dependencies > 100:
            build_time = "10-15 minutes"
            cpu_requirement = "2 vCPU"
            memory_requirement = "4 GB"
        
        if repository_analysis.total_files > 500:
            build_time = "10-20 minutes"
            storage_requirement = "4 GB"
        
        # Adjust based on project type
        if primary_type:
            if primary_type.type == 'Next.js':
                memory_requirement = "2 GB"  # Next.js can be memory intensive
            elif primary_type.type == 'Angular':
                build_time = "5-15 minutes"  # Angular builds can be slow
                memory_requirement = "2 GB"
        
        return {
            'build_time': build_time,
            'resource_usage': {
                'cpu': cpu_requirement,
                'memory': memory_requirement,
                'storage': storage_requirement
            }
        }

    def cleanup_session(self, session_id: str):
        """Clean up completed analysis session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up analysis session {session_id}")

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_reporter():
        reporter = AnalysisReporter()
        
        # Start analysis
        session_id = await reporter.start_analysis("https://github.com/facebook/react")
        
        # Run comprehensive analysis
        result = await reporter.run_comprehensive_analysis(session_id)
        
        print(json.dumps(asdict(result), indent=2, default=str))
        
        # Cleanup
        reporter.cleanup_session(session_id)
    
    asyncio.run(test_reporter())
