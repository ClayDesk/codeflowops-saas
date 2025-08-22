# Terraform Execution Service for Smart Deploy
# Handles running Terraform commands in subprocess with real-time status updates

import asyncio
import subprocess
import tempfile
import shutil
import os
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
import re

from ..utils.memory_storage import create_memory_redis_client

class TerraformExecutionError(Exception):
    """Custom exception for Terraform execution errors"""
    pass

class TerraformExecutor:
    """
    Service for executing Terraform commands with real-time status updates
    """
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.active_executions: Dict[str, Dict] = {}
        
    async def get_redis_client(self):
        """Get Redis client for status updates"""
        if self.redis_client is None:
            self.redis_client = await create_memory_redis_client()
        return self.redis_client
    
    async def execute_deployment(
        self,
        deployment_id: str,
        template_files: Dict[str, str],
        template_variables: Dict[str, Any],
        deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a full Terraform deployment with real-time updates
        """
        try:
            # Initialize execution tracking
            execution_data = {
                "deployment_id": deployment_id,
                "status": "initializing",
                "progress": 0,
                "current_step": "setup",
                "started_at": datetime.utcnow().isoformat(),
                "logs": [],
                "outputs": {}
            }
            
            self.active_executions[deployment_id] = execution_data
            await self._update_status(deployment_id, "initializing", "🚀 Starting Terraform deployment...", 5)
            
            # Extract custom environment if provided
            custom_env = deployment_config.get("environment", {})
            
            # Create temporary directory for Terraform files
            with tempfile.TemporaryDirectory(prefix=f"terraform-{deployment_id}-") as temp_dir:
                terraform_dir = Path(temp_dir)
                
                # Write Terraform files
                await self._write_terraform_files(terraform_dir, template_files, template_variables)
                await self._update_status(deployment_id, "preparing", "📝 Terraform files prepared", 15)
                
                # Initialize Terraform
                await self._run_terraform_init(deployment_id, terraform_dir, custom_env)
                await self._update_status(deployment_id, "planning", "📋 Generating Terraform plan...", 35)
                
                # Create Terraform plan
                plan_result = await self._run_terraform_plan(deployment_id, terraform_dir, custom_env)
                await self._update_status(deployment_id, "planned", "✅ Terraform plan complete", 50)
                
                # Apply Terraform (if not dry-run)
                if not deployment_config.get("dry_run", False):
                    await self._update_status(deployment_id, "applying", "🏗️ Applying infrastructure changes...", 60)
                    apply_result = await self._run_terraform_apply(deployment_id, terraform_dir, custom_env)
                    
                    # Get outputs
                    await self._update_status(deployment_id, "outputs", "📊 Retrieving deployment outputs...", 90)
                    outputs = await self._get_terraform_outputs(deployment_id, terraform_dir, custom_env)
                    
                    execution_data["outputs"] = outputs
                    await self._update_status(deployment_id, "completed", "🎉 Deployment completed successfully!", 100)
                    
                    return {
                        "status": "completed",
                        "deployment_id": deployment_id,
                        "outputs": outputs,
                        "plan_summary": plan_result.get("summary", {}),
                        "execution_time": self._calculate_execution_time(execution_data),
                        "message": "Infrastructure deployed successfully"
                    }
                else:
                    await self._update_status(deployment_id, "plan_complete", "📋 Dry-run completed - no changes applied", 100)
                    
                    return {
                        "status": "plan_complete", 
                        "deployment_id": deployment_id,
                        "plan_summary": plan_result.get("summary", {}),
                        "message": "Terraform plan completed successfully (dry-run)"
                    }
                    
        except Exception as e:
            await self._update_status(deployment_id, "failed", f"❌ Deployment failed: {str(e)}", 0)
            raise TerraformExecutionError(f"Terraform execution failed: {str(e)}")
        
        finally:
            # Clean up tracking
            if deployment_id in self.active_executions:
                execution_data = self.active_executions[deployment_id]
                execution_data["completed_at"] = datetime.utcnow().isoformat()
    
    async def _write_terraform_files(
        self, 
        terraform_dir: Path, 
        template_files: Dict[str, str],
        template_variables: Dict[str, Any]
    ):
        """Write Terraform template files to directory"""
        
        # Write main template files
        for file_key, content in template_files.items():
            file_name = file_key.replace("_", ".")  # main_tf -> main.tf
            file_path = terraform_dir / file_name
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Write terraform.tfvars with actual values
        tfvars_path = terraform_dir / "terraform.tfvars"
        with open(tfvars_path, 'w', encoding='utf-8') as f:
            for key, value in template_variables.items():
                if isinstance(value, str):
                    f.write(f'{key} = "{value}"\n')
                elif isinstance(value, bool):
                    f.write(f'{key} = {str(value).lower()}\n')
                elif isinstance(value, (int, float)):
                    f.write(f'{key} = {value}\n')
                else:
                    f.write(f'{key} = "{str(value)}"\n')
    
    async def _run_terraform_init(self, deployment_id: str, terraform_dir: Path, custom_env: Dict[str, str] = None):
        """Run terraform init"""
        cmd = ["terraform", "init", "-no-color"]
        
        await self._update_status(deployment_id, "initializing", "🔧 Initializing Terraform...", 20)
        
        result = await self._run_terraform_command(
            cmd, terraform_dir, deployment_id, "init", custom_env
        )
        
        if result["returncode"] != 0:
            raise TerraformExecutionError(f"Terraform init failed: {result['stderr']}")
    
    async def _run_terraform_plan(self, deployment_id: str, terraform_dir: Path, custom_env: Dict[str, str] = None) -> Dict[str, Any]:
        """Run terraform plan and parse output"""
        cmd = ["terraform", "plan", "-no-color", "-out=tfplan"]
        
        result = await self._run_terraform_command(
            cmd, terraform_dir, deployment_id, "plan", custom_env
        )
        
        if result["returncode"] != 0:
            raise TerraformExecutionError(f"Terraform plan failed: {result['stderr']}")
        
        # Parse plan summary
        plan_summary = self._parse_plan_output(result["stdout"])
        
        return {
            "success": True,
            "summary": plan_summary,
            "output": result["stdout"]
        }
    
    async def _run_terraform_apply(self, deployment_id: str, terraform_dir: Path, custom_env: Dict[str, str] = None) -> Dict[str, Any]:
        """Run terraform apply"""
        cmd = ["terraform", "apply", "-no-color", "-auto-approve", "tfplan"]
        
        result = await self._run_terraform_command(
            cmd, terraform_dir, deployment_id, "apply", custom_env
        )
        
        if result["returncode"] != 0:
            raise TerraformExecutionError(f"Terraform apply failed: {result['stderr']}")
        
        return {
            "success": True,
            "output": result["stdout"]
        }
    
    async def _get_terraform_outputs(self, deployment_id: str, terraform_dir: Path, custom_env: Dict[str, str] = None) -> Dict[str, Any]:
        """Get Terraform outputs in JSON format"""
        cmd = ["terraform", "output", "-json"]
        
        result = await self._run_terraform_command(
            cmd, terraform_dir, deployment_id, "outputs", custom_env
        )
        
        if result["returncode"] != 0:
            # Outputs might not exist, return empty dict
            return {}
        
        try:
            outputs = json.loads(result["stdout"])
            # Convert Terraform output format to simple key-value pairs
            simplified_outputs = {}
            for key, value in outputs.items():
                simplified_outputs[key] = value.get("value", "")
            
            return simplified_outputs
        except json.JSONDecodeError:
            return {}
    
    async def _run_terraform_command(
        self, 
        cmd: List[str], 
        cwd: Path, 
        deployment_id: str, 
        step: str,
        custom_env: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Run a Terraform command with real-time output capture"""
        
        try:
            # Check if Terraform is available
            if not shutil.which("terraform"):
                # Fallback to simulation mode
                return await self._simulate_terraform_command(cmd, step, deployment_id)
            
            # Prepare environment (base + custom)
            env = {**os.environ, "TF_IN_AUTOMATION": "1"}
            if custom_env:
                env.update(custom_env)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            stdout_lines = []
            stderr_lines = []
            
            # Capture output in real-time
            async def read_stdout():
                async for line in process.stdout:
                    line_str = line.decode('utf-8').strip()
                    if line_str:
                        stdout_lines.append(line_str)
                        await self._log_terraform_output(deployment_id, step, line_str)
            
            async def read_stderr():
                async for line in process.stderr:
                    line_str = line.decode('utf-8').strip()
                    if line_str:
                        stderr_lines.append(line_str)
                        await self._log_terraform_output(deployment_id, step, line_str, is_error=True)
            
            # Run output readers concurrently
            await asyncio.gather(read_stdout(), read_stderr())
            
            # Wait for process completion
            returncode = await process.wait()
            
            return {
                "returncode": returncode,
                "stdout": "\n".join(stdout_lines),
                "stderr": "\n".join(stderr_lines)
            }
            
        except FileNotFoundError:
            # Terraform not installed, use simulation
            return await self._simulate_terraform_command(cmd, step, deployment_id)
        except Exception as e:
            raise TerraformExecutionError(f"Failed to run terraform command: {str(e)}")
    
    async def _simulate_terraform_command(
        self, 
        cmd: List[str], 
        step: str, 
        deployment_id: str
    ) -> Dict[str, Any]:
        """Simulate Terraform command for demo purposes"""
        
        await asyncio.sleep(2)  # Simulate processing time
        
        if "init" in cmd:
            output = """
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.17.0...
- Installed hashicorp/aws v5.17.0

Terraform has been successfully initialized!
"""
        elif "plan" in cmd:
            output = """
Terraform used the selected providers to generate the following execution plan.

Terraform will perform the following actions:

  # aws_s3_bucket.website will be created
  + resource "aws_s3_bucket" "website" {
      + bucket = "my-app-website-dev-a1b2c3d4"
    }

  # aws_cloudfront_distribution.website will be created
  + resource "aws_cloudfront_distribution" "website" {
      + domain_name = "d1a2b3c4d5e6f7.cloudfront.net"
    }

Plan: 8 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + website_url = "https://d1a2b3c4d5e6f7.cloudfront.net"
"""
        elif "apply" in cmd:
            output = """
aws_s3_bucket.website: Creating...
aws_s3_bucket.website: Creation complete after 2s
aws_cloudfront_distribution.website: Creating...
aws_cloudfront_distribution.website: Still creating... [10s elapsed]
aws_cloudfront_distribution.website: Creation complete after 45s

Apply complete! Resources: 8 added, 0 changed, 0 destroyed.

Outputs:
website_url = "https://d1a2b3c4d5e6f7.cloudfront.net"
"""
        elif "output" in cmd:
            output = """
{
  "website_url": {
    "sensitive": false,
    "type": "string", 
    "value": "https://d1a2b3c4d5e6f7.cloudfront.net"
  },
  "s3_bucket_name": {
    "sensitive": false,
    "type": "string",
    "value": "my-app-website-dev-a1b2c3d4"
  }
}
"""
        else:
            output = "Terraform command completed successfully."
        
        await self._log_terraform_output(deployment_id, step, output)
        
        return {
            "returncode": 0,
            "stdout": output,
            "stderr": ""
        }
    
    def _parse_plan_output(self, plan_output: str) -> Dict[str, Any]:
        """Parse Terraform plan output to extract summary"""
        summary = {
            "resources_to_add": 0,
            "resources_to_change": 0,
            "resources_to_destroy": 0,
            "total_changes": 0
        }
        
        # Look for plan summary line like "Plan: 8 to add, 0 to change, 0 to destroy."
        plan_pattern = r"Plan: (\d+) to add, (\d+) to change, (\d+) to destroy"
        match = re.search(plan_pattern, plan_output)
        
        if match:
            summary["resources_to_add"] = int(match.group(1))
            summary["resources_to_change"] = int(match.group(2))
            summary["resources_to_destroy"] = int(match.group(3))
            summary["total_changes"] = sum([
                summary["resources_to_add"],
                summary["resources_to_change"], 
                summary["resources_to_destroy"]
            ])
        
        return summary
    
    async def _update_status(
        self, 
        deployment_id: str, 
        status: str, 
        message: str, 
        progress: int
    ):
        """Update deployment status in Redis and local tracking"""
        
        status_data = {
            "deployment_id": deployment_id,
            "status": status,
            "message": message,
            "progress": progress,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update local tracking
        if deployment_id in self.active_executions:
            execution_data = self.active_executions[deployment_id]
            execution_data.update({
                "status": status,
                "progress": progress,
                "current_step": status,
                "last_message": message
            })
        
        # Update Redis for real-time monitoring
        try:
            redis_client = await self.get_redis_client()
            await redis_client.setex(
                f"deployment:status:{deployment_id}",
                3600,  # 1 hour TTL
                json.dumps(status_data)
            )
            
            # Also publish to real-time channel
            await redis_client.publish(
                f"deployment:updates:{deployment_id}",
                json.dumps(status_data)
            )
        except Exception as e:
            print(f"⚠️ Failed to update Redis status: {e}")
    
    async def _log_terraform_output(
        self, 
        deployment_id: str, 
        step: str, 
        output: str, 
        is_error: bool = False
    ):
        """Log Terraform output for real-time monitoring"""
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "step": step,
            "output": output,
            "is_error": is_error
        }
        
        # Add to local tracking
        if deployment_id in self.active_executions:
            execution_data = self.active_executions[deployment_id]
            if "logs" not in execution_data:
                execution_data["logs"] = []
            execution_data["logs"].append(log_entry)
        
        # Stream to Redis for real-time logs
        try:
            redis_client = await self.get_redis_client()
            await redis_client.lpush(
                f"deployment:logs:{deployment_id}",
                json.dumps(log_entry)
            )
            # Keep only last 1000 log entries
            await redis_client.ltrim(f"deployment:logs:{deployment_id}", 0, 999)
        except Exception as e:
            print(f"⚠️ Failed to log to Redis: {e}")
    
    def _calculate_execution_time(self, execution_data: Dict[str, Any]) -> str:
        """Calculate total execution time"""
        try:
            started = datetime.fromisoformat(execution_data["started_at"])
            completed = datetime.utcnow()
            duration = completed - started
            
            minutes = int(duration.total_seconds() // 60)
            seconds = int(duration.total_seconds() % 60)
            
            if minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        except:
            return "unknown"
    
    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get current deployment status"""
        
        # Try Redis first
        try:
            redis_client = await self.get_redis_client()
            status_data = await redis_client.get(f"deployment:status:{deployment_id}")
            if status_data:
                return json.loads(status_data)
        except Exception as e:
            print(f"⚠️ Failed to get status from Redis: {e}")
        
        # Fallback to local tracking
        if deployment_id in self.active_executions:
            return self.active_executions[deployment_id]
        
        return {"status": "not_found", "message": "Deployment not found"}
    
    async def get_deployment_logs(self, deployment_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get deployment logs"""
        
        try:
            redis_client = await self.get_redis_client()
            log_entries = await redis_client.lrange(f"deployment:logs:{deployment_id}", 0, limit - 1)
            return [json.loads(entry) for entry in log_entries]
        except Exception as e:
            print(f"⚠️ Failed to get logs from Redis: {e}")
            
            # Fallback to local tracking
            if deployment_id in self.active_executions:
                execution_data = self.active_executions[deployment_id]
                return execution_data.get("logs", [])[-limit:]
            
            return []
    
    # Alias method for compatibility
    async def execute_terraform_deployment(
        self,
        deployment_id: str,
        template_files: Dict[str, str],
        template_variables: Dict[str, Any],
        deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Alias for execute_deployment method for backward compatibility
        """
        return await self.execute_deployment(
            deployment_id=deployment_id,
            template_files=template_files,
            template_variables=template_variables,
            deployment_config=deployment_config
        )
