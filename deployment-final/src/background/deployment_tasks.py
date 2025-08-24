"""
Deployment background tasks for CodeFlowOps
Handles AWS infrastructure provisioning and deployment processes
"""

import logging
import asyncio
import json
import os
import tempfile
import shutil
from typing import Dict, Any, Optional
from pathlib import Path

from ..config.env import get_settings
from dependencies.session import get_session_manager
from controllers.deploymentController import DeploymentController

logger = logging.getLogger(__name__)
settings = get_settings()


async def start_deployment_task(
    session_id: str,
    deployment_config: Dict[str, Any],
    is_retry: bool = False,
    force_rebuild: bool = False
):
    """
    Main deployment task that orchestrates the complete deployment workflow
    
    Args:
        session_id: Session identifier
        deployment_config: Deployment configuration
        is_retry: Whether this is a retry attempt
        force_rebuild: Whether to force rebuild
    """
    session_manager = await get_session_manager()
    deployment_controller = DeploymentController()
    
    try:
        logger.info(f"Starting deployment task for session {session_id}")
        
        # Update session status
        await session_manager.update_session_status(
            session_id,
            "deploying",
            current_step="initializing",
            progress_percentage=5
        )
        
        # Send progress update
        await session_manager.send_progress_update(
            session_id,
            step="deploying",
            progress=5,
            message="Initializing deployment process..."
        )
        
        # Step 1: Prepare deployment environment
        await session_manager.send_progress_update(
            session_id,
            step="deploying",
            progress=10,
            message="Preparing deployment environment..."
        )
        
        deployment_env = await deployment_controller.prepare_deployment_environment(
            session_id,
            deployment_config
        )
        
        # Step 2: Build project (if needed)
        project_type = deployment_config.get("project_type", "static")
        if project_type in ["react", "vue", "angular", "nextjs", "gatsby", "svelte"] or force_rebuild:
            await session_manager.send_progress_update(
                session_id,
                step="building",
                progress=20,
                message="Building project..."
            )
            
            build_result = await start_build_task(session_id, deployment_config)
            if not build_result.get("success"):
                raise Exception(f"Build failed: {build_result.get('error')}")
        
        # Step 3: Provision infrastructure
        await session_manager.send_progress_update(
            session_id,
            step="provisioning",
            progress=40,
            message="Provisioning AWS infrastructure..."
        )
        
        infrastructure_result = await start_infrastructure_task(session_id, deployment_config)
        if not infrastructure_result.get("success"):
            raise Exception(f"Infrastructure provisioning failed: {infrastructure_result.get('error')}")
        
        # Step 4: Deploy files
        await session_manager.send_progress_update(
            session_id,
            step="deploying",
            progress=70,
            message="Deploying files to AWS..."
        )
        
        deploy_result = await deployment_controller.deploy_files(
            session_id,
            deployment_env,
            infrastructure_result["infrastructure"]
        )
        
        if not deploy_result.get("success"):
            raise Exception(f"File deployment failed: {deploy_result.get('error')}")
        
        # Step 5: Finalize deployment
        await session_manager.send_progress_update(
            session_id,
            step="finalizing",
            progress=90,
            message="Finalizing deployment..."
        )
        
        finalization_result = await start_finalization_task(session_id, {
            **deployment_config,
            "infrastructure": infrastructure_result["infrastructure"],
            "deployment": deploy_result
        })
        
        # Complete deployment
        await session_manager.update_session_status(
            session_id,
            "completed",
            current_step="completed",
            progress_percentage=100,
            deployment_url=finalization_result.get("site_url")
        )
        
        await session_manager.send_progress_update(
            session_id,
            step="completed",
            progress=100,
            message=f"Deployment completed successfully! Site available at: {finalization_result.get('site_url')}"
        )
        
        logger.info(f"Deployment completed successfully for session {session_id}")
        
    except Exception as e:
        logger.error(f"Deployment failed for session {session_id}: {str(e)}")
        
        await session_manager.update_session_status(
            session_id,
            "failed",
            error_details=str(e)
        )
        
        await session_manager.send_progress_update(
            session_id,
            step="failed",
            progress=0,
            message=f"Deployment failed: {str(e)}"
        )


async def start_build_task(session_id: str, build_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build project files for deployment
    
    Args:
        session_id: Session identifier
        build_config: Build configuration
        
    Returns:
        Build results
    """
    session_manager = await get_session_manager()
    deployment_controller = DeploymentController()
    
    try:
        logger.info(f"Starting build task for session {session_id}")
        
        # Update session status
        await session_manager.update_session_status(
            session_id,
            "building",
            current_step="building_project",
            progress_percentage=15
        )
        
        # Clone repository
        await session_manager.send_progress_update(
            session_id,
            step="building",
            progress=20,
            message="Cloning repository..."
        )
        
        repo_info = build_config.get("repository_info", {})
        github_url = f"https://github.com/{repo_info.get('owner')}/{repo_info.get('repo')}.git"
        
        # Create temporary directory for build
        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = Path(temp_dir) / "build"
            
            # Clone repository
            clone_result = await deployment_controller.clone_repository(
                github_url,
                build_dir,
                repo_info.get("default_branch", "main")
            )
            
            if not clone_result.get("success"):
                return {
                    "success": False,
                    "error": f"Repository clone failed: {clone_result.get('error')}"
                }
            
            # Install dependencies
            await session_manager.send_progress_update(
                session_id,
                step="building",
                progress=40,
                message="Installing dependencies..."
            )
            
            install_result = await deployment_controller.install_dependencies(
                build_dir,
                build_config.get("build_config", {})
            )
            
            if not install_result.get("success"):
                return {
                    "success": False,
                    "error": f"Dependencies installation failed: {install_result.get('error')}"
                }
            
            # Run build
            await session_manager.send_progress_update(
                session_id,
                step="building",
                progress=70,
                message="Building project..."
            )
            
            build_result = await deployment_controller.build_project(
                build_dir,
                build_config.get("build_config", {})
            )
            
            if not build_result.get("success"):
                return {
                    "success": False,
                    "error": f"Project build failed: {build_result.get('error')}"
                }
            
            # Package build artifacts
            await session_manager.send_progress_update(
                session_id,
                step="building",
                progress=90,
                message="Packaging build artifacts..."
            )
            
            package_result = await deployment_controller.package_build_artifacts(
                session_id,
                build_dir,
                build_result["build_output"]
            )
            
            return {
                "success": True,
                "build_artifacts": package_result["artifacts_path"],
                "build_output": build_result["build_output"],
                "build_size": package_result["size"]
            }
    
    except Exception as e:
        logger.error(f"Build task failed for session {session_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def start_infrastructure_task(session_id: str, stack_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Provision AWS infrastructure using CloudFormation/Terraform
    
    Args:
        session_id: Session identifier
        stack_config: Infrastructure configuration
        
    Returns:
        Infrastructure provisioning results
    """
    session_manager = await get_session_manager()
    deployment_controller = DeploymentController()
    
    try:
        logger.info(f"Starting infrastructure provisioning for session {session_id}")
        
        # Update session status
        await session_manager.update_session_status(
            session_id,
            "deploying",
            current_step="provisioning_infrastructure",
            progress_percentage=45
        )
        
        # Generate infrastructure templates
        await session_manager.send_progress_update(
            session_id,
            step="provisioning",
            progress=45,
            message="Generating infrastructure templates..."
        )
        
        template_result = await deployment_controller.generate_infrastructure_templates(
            session_id,
            stack_config
        )
        
        if not template_result.get("success"):
            return {
                "success": False,
                "error": f"Template generation failed: {template_result.get('error')}"
            }
        
        # Validate AWS credentials and permissions
        await session_manager.send_progress_update(
            session_id,
            step="provisioning",
            progress=50,
            message="Validating AWS credentials..."
        )
        
        aws_validation = await deployment_controller.validate_aws_access(stack_config)
        if not aws_validation.get("valid"):
            return {
                "success": False,
                "error": f"AWS validation failed: {aws_validation.get('error')}"
            }
        
        # Deploy infrastructure stack
        await session_manager.send_progress_update(
            session_id,
            step="provisioning",
            progress=60,
            message="Deploying infrastructure stack..."
        )
        
        stack_result = await deployment_controller.deploy_infrastructure_stack(
            session_id,
            template_result["templates"],
            stack_config
        )
        
        if not stack_result.get("success"):
            return {
                "success": False,
                "error": f"Stack deployment failed: {stack_result.get('error')}"
            }
        
        # Wait for stack completion
        await session_manager.send_progress_update(
            session_id,
            step="provisioning",
            progress=75,
            message="Waiting for stack completion..."
        )
        
        completion_result = await deployment_controller.wait_for_stack_completion(
            session_id,
            stack_result["stack_id"]
        )
        
        return {
            "success": True,
            "infrastructure": {
                "stack_id": stack_result["stack_id"],
                "resources": completion_result["resources"],
                "outputs": completion_result["outputs"]
            }
        }
    
    except Exception as e:
        logger.error(f"Infrastructure provisioning failed for session {session_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def start_finalization_task(session_id: str, finalization_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Finalize deployment with configuration and cleanup
    
    Args:
        session_id: Session identifier
        finalization_config: Finalization configuration
        
    Returns:
        Finalization results
    """
    session_manager = await get_session_manager()
    deployment_controller = DeploymentController()
    
    try:
        logger.info(f"Starting deployment finalization for session {session_id}")
        
        # Configure CDN and DNS
        await session_manager.send_progress_update(
            session_id,
            step="finalizing",
            progress=92,
            message="Configuring CDN and DNS..."
        )
        
        cdn_result = await deployment_controller.configure_cdn_and_dns(
            session_id,
            finalization_config["infrastructure"]
        )
        
        # Set up monitoring and alerts
        await session_manager.send_progress_update(
            session_id,
            step="finalizing",
            progress=95,
            message="Setting up monitoring..."
        )
        
        monitoring_result = await deployment_controller.setup_monitoring(
            session_id,
            finalization_config["infrastructure"]
        )
        
        # Generate deployment summary
        await session_manager.send_progress_update(
            session_id,
            step="finalizing",
            progress=98,
            message="Generating deployment summary..."
        )
        
        summary_result = await deployment_controller.generate_deployment_summary(
            session_id,
            finalization_config
        )
        
        # Cleanup temporary resources
        await deployment_controller.cleanup_temporary_resources(session_id)
        
        return {
            "success": True,
            "site_url": cdn_result.get("site_url"),
            "cdn_distribution": cdn_result.get("distribution_id"),
            "monitoring": monitoring_result,
            "summary": summary_result
        }
    
    except Exception as e:
        logger.error(f"Deployment finalization failed for session {session_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def cleanup_failed_deployment(session_id: str, cleanup_config: Dict[str, Any]):
    """
    Cleanup resources from failed deployment
    
    Args:
        session_id: Session identifier
        cleanup_config: Cleanup configuration
    """
    try:
        logger.info(f"Cleaning up failed deployment for session {session_id}")
        
        deployment_controller = DeploymentController()
        
        # Cleanup AWS resources
        await deployment_controller.cleanup_aws_resources(session_id, cleanup_config)
        
        # Cleanup temporary files
        await deployment_controller.cleanup_temporary_resources(session_id)
        
        logger.info(f"Cleanup completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"Cleanup failed for session {session_id}: {str(e)}")


async def start_destroy_task(session_id: str):
    """
    Destroy AWS resources for a deployed project
    
    Args:
        session_id: Session identifier for the deployment to destroy
    """
    session_manager = await get_session_manager()
    deployment_controller = DeploymentController()
    
    try:
        logger.info(f"Starting destroy task for session {session_id}")
        
        # Get session info
        session_info = await session_manager.get_session(session_id)
        if not session_info or not session_info.deployment_result:
            raise ValueError("No deployment found to destroy")
        
        # Update session status
        await session_manager.update_session_status(
            session_id,
            "destroying",
            current_step="initializing_destruction",
            progress_percentage=10
        )
        
        # Get deployment details
        deployment_result = session_info.deployment_result
        
        # Step 1: Prepare terraform workspace
        await session_manager.update_session_status(
            session_id,
            "destroying",
            current_step="preparing_terraform",
            progress_percentage=20
        )
        
        # Create temporary directory for terraform operations
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir) / "terraform"
            workspace_path.mkdir(parents=True, exist_ok=True)
            
            # Step 2: Download terraform state from S3
            await session_manager.update_session_status(
                session_id,
                "destroying",
                current_step="downloading_state",
                progress_percentage=30
            )
            
            state_key = f"terraform-state/{session_id}/terraform.tfstate"
            await deployment_controller.download_terraform_state(
                state_key, 
                workspace_path / "terraform.tfstate"
            )
            
            # Step 3: Generate destroy terraform configuration
            await session_manager.update_session_status(
                session_id,
                "destroying",
                current_step="generating_destroy_config",
                progress_percentage=40
            )
            
            # Recreate the terraform configuration
            terraform_config = await deployment_controller.generate_terraform_config(
                session_info.analysis_result,
                deployment_result.get("infrastructure_config", {})
            )
            
            # Write terraform files
            tf_file_path = workspace_path / "main.tf"
            with open(tf_file_path, 'w') as f:
                f.write(terraform_config)
            
            # Step 4: Initialize terraform
            await session_manager.update_session_status(
                session_id,
                "destroying",
                current_step="initializing_terraform",
                progress_percentage=50
            )
            
            await deployment_controller.run_terraform_command(
                workspace_path,
                ["init"],
                session_id
            )
            
            # Step 5: Plan destruction
            await session_manager.update_session_status(
                session_id,
                "destroying",
                current_step="planning_destruction",
                progress_percentage=60
            )
            
            plan_result = await deployment_controller.run_terraform_command(
                workspace_path,
                ["plan", "-destroy", "-out=destroy.tfplan"],
                session_id
            )
            
            # Step 6: Execute destruction
            await session_manager.update_session_status(
                session_id,
                "destroying",
                current_step="destroying_resources",
                progress_percentage=70
            )
            
            destroy_result = await deployment_controller.run_terraform_command(
                workspace_path,
                ["apply", "-auto-approve", "destroy.tfplan"],
                session_id
            )
            
            # Step 7: Cleanup S3 bucket contents (if any)
            await session_manager.update_session_status(
                session_id,
                "destroying",
                current_step="cleaning_storage",
                progress_percentage=85
            )
            
            if deployment_result.get("s3_bucket"):
                await deployment_controller.cleanup_s3_bucket(
                    deployment_result["s3_bucket"]
                )
            
            # Step 8: Remove terraform state
            await session_manager.update_session_status(
                session_id,
                "destroying",
                current_step="cleaning_state",
                progress_percentage=95
            )
            
            await deployment_controller.delete_terraform_state(state_key)
        
        # Final step: Mark as destroyed
        await session_manager.update_session_status(
            session_id,
            "destroyed",
            current_step="completed",
            progress_percentage=100
        )
        
        # Update deployment result to mark as destroyed
        deployment_result["status"] = "destroyed"
        deployment_result["destroyed_at"] = deployment_controller.get_current_timestamp()
        
        await session_manager.update_deployment_result(session_id, deployment_result)
        
        logger.info(f"Successfully destroyed resources for session {session_id}")
        
    except Exception as e:
        logger.error(f"Destroy task failed for session {session_id}: {str(e)}")
        
        # Update session with error status
        await session_manager.update_session_status(
            session_id,
            "destroy_failed",
            current_step="error",
            error_message=str(e)
        )
        
        # Log the full error for debugging
        logger.exception(f"Full destroy error for session {session_id}")
        
        raise
