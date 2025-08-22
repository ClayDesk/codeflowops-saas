/**
 * AWSDeployer.js - Complete AWS deployment orchestration
 */

const { spawn } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

class AWSDeployer {
  constructor() {
    this.deploymentTimeout = 20 * 60 * 1000; // 20 minutes timeout
  }

  async deployStack(terraformPath, stackType, projectFiles, sessionId) {
    console.log(`[${sessionId}] Starting AWS deployment...`);
    
    const deployment = {
      sessionId,
      stackType,
      success: false,
      terraformOutputs: {},
      siteUrl: null,
      deploymentTime: 0,
      logs: [],
      errors: []
    };

    const startTime = Date.now();

    try {
      // Step 1: Initialize Terraform
      await this.runTerraformInit(terraformPath, sessionId, deployment);
      
      // Step 2: Plan deployment
      await this.runTerraformPlan(terraformPath, sessionId, deployment);
      
      // Step 3: Apply infrastructure
      await this.runTerraformApply(terraformPath, sessionId, deployment);
      
      // Step 4: Get Terraform outputs
      await this.getTerraformOutputs(terraformPath, sessionId, deployment);
      
      // Step 5: Deploy application files
      if (stackType === 'static-site') {
        await this.deployStaticFiles(projectFiles, deployment, sessionId);
      } else if (stackType === 'react-app') {
        await this.deployReactApp(projectFiles, deployment, sessionId);
      }
      
      // Step 6: Invalidate CloudFront cache
      await this.invalidateCloudFront(deployment, sessionId);
      
      deployment.success = true;
      deployment.deploymentTime = Date.now() - startTime;
      deployment.siteUrl = deployment.terraformOutputs.site_url;
      
      console.log(`[${sessionId}] Deployment completed successfully in ${deployment.deploymentTime}ms`);
      console.log(`[${sessionId}] Site URL: ${deployment.siteUrl}`);
      
      return deployment;
      
    } catch (error) {
      deployment.success = false;
      deployment.errors.push(error.message);
      deployment.deploymentTime = Date.now() - startTime;
      
      console.error(`[${sessionId}] Deployment failed:`, error.message);
      throw error;
    }
  }

  async runTerraformInit(terraformPath, sessionId, deployment) {
    console.log(`[${sessionId}] Initializing Terraform...`);
    
    return new Promise((resolve, reject) => {
      const init = spawn('terraform', ['init'], {
        cwd: terraformPath,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let initLogs = '';

      init.stdout.on('data', (data) => {
        const log = data.toString();
        initLogs += log;
        deployment.logs.push(`[INIT] ${log.trim()}`);
        console.log(`[${sessionId}] terraform init: ${log.trim()}`);
      });

      init.stderr.on('data', (data) => {
        const log = data.toString();
        initLogs += log;
        deployment.logs.push(`[INIT ERROR] ${log.trim()}`);
        console.error(`[${sessionId}] terraform init error: ${log.trim()}`);
      });

      init.on('close', (code) => {
        if (code === 0) {
          console.log(`[${sessionId}] Terraform init completed`);
          resolve();
        } else {
          reject(new Error(`Terraform init failed with exit code ${code}`));
        }
      });

      init.on('error', (error) => {
        reject(new Error(`Terraform init process error: ${error.message}`));
      });
    });
  }

  async runTerraformPlan(terraformPath, sessionId, deployment) {
    console.log(`[${sessionId}] Planning Terraform deployment...`);
    
    return new Promise((resolve, reject) => {
      const plan = spawn('terraform', ['plan', '-var-file=terraform.tfvars'], {
        cwd: terraformPath,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let planLogs = '';

      plan.stdout.on('data', (data) => {
        const log = data.toString();
        planLogs += log;
        deployment.logs.push(`[PLAN] ${log.trim()}`);
        console.log(`[${sessionId}] terraform plan: ${log.trim()}`);
      });

      plan.stderr.on('data', (data) => {
        const log = data.toString();
        planLogs += log;
        deployment.logs.push(`[PLAN ERROR] ${log.trim()}`);
        console.error(`[${sessionId}] terraform plan error: ${log.trim()}`);
      });

      plan.on('close', (code) => {
        if (code === 0) {
          console.log(`[${sessionId}] Terraform plan completed`);
          resolve();
        } else {
          reject(new Error(`Terraform plan failed with exit code ${code}`));
        }
      });

      plan.on('error', (error) => {
        reject(new Error(`Terraform plan process error: ${error.message}`));
      });
    });
  }

  async runTerraformApply(terraformPath, sessionId, deployment) {
    console.log(`[${sessionId}] Applying Terraform configuration...`);
    
    return new Promise((resolve, reject) => {
      const apply = spawn('terraform', ['apply', '-auto-approve', '-var-file=terraform.tfvars'], {
        cwd: terraformPath,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let applyLogs = '';

      apply.stdout.on('data', (data) => {
        const log = data.toString();
        applyLogs += log;
        deployment.logs.push(`[APPLY] ${log.trim()}`);
        console.log(`[${sessionId}] terraform apply: ${log.trim()}`);
      });

      apply.stderr.on('data', (data) => {
        const log = data.toString();
        applyLogs += log;
        deployment.logs.push(`[APPLY ERROR] ${log.trim()}`);
        console.error(`[${sessionId}] terraform apply error: ${log.trim()}`);
      });

      apply.on('close', (code) => {
        if (code === 0) {
          console.log(`[${sessionId}] Terraform apply completed`);
          resolve();
        } else {
          reject(new Error(`Terraform apply failed with exit code ${code}`));
        }
      });

      apply.on('error', (error) => {
        reject(new Error(`Terraform apply process error: ${error.message}`));
      });

      // Timeout handling
      setTimeout(() => {
        apply.kill();
        reject(new Error('Terraform apply timeout after 20 minutes'));
      }, this.deploymentTimeout);
    });
  }

  async getTerraformOutputs(terraformPath, sessionId, deployment) {
    console.log(`[${sessionId}] Getting Terraform outputs...`);
    
    return new Promise((resolve, reject) => {
      const output = spawn('terraform', ['output', '-json'], {
        cwd: terraformPath,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let outputData = '';

      output.stdout.on('data', (data) => {
        outputData += data.toString();
      });

      output.stderr.on('data', (data) => {
        const log = data.toString();
        deployment.logs.push(`[OUTPUT ERROR] ${log.trim()}`);
        console.error(`[${sessionId}] terraform output error: ${log.trim()}`);
      });

      output.on('close', (code) => {
        if (code === 0) {
          try {
            const outputs = JSON.parse(outputData);
            deployment.terraformOutputs = {};
            
            // Extract values from Terraform output format
            for (const [key, value] of Object.entries(outputs)) {
              deployment.terraformOutputs[key] = value.value;
            }
            
            console.log(`[${sessionId}] Terraform outputs retrieved`);
            resolve();
          } catch (error) {
            reject(new Error(`Failed to parse Terraform outputs: ${error.message}`));
          }
        } else {
          reject(new Error(`Terraform output failed with exit code ${code}`));
        }
      });

      output.on('error', (error) => {
        reject(new Error(`Terraform output process error: ${error.message}`));
      });
    });
  }

  async deployStaticFiles(projectFiles, deployment, sessionId) {
    console.log(`[${sessionId}] Deploying static files to S3...`);
    
    const bucketName = deployment.terraformOutputs.s3_bucket_name;
    if (!bucketName) {
      throw new Error('S3 bucket name not found in Terraform outputs');
    }

    // Upload all files to S3
    await this.uploadToS3(projectFiles, bucketName, sessionId, deployment);
  }

  async deployReactApp(projectFiles, deployment, sessionId) {
    console.log(`[${sessionId}] Deploying React build files to S3...`);
    
    const bucketName = deployment.terraformOutputs.s3_bucket_name;
    if (!bucketName) {
      throw new Error('S3 bucket name not found in Terraform outputs');
    }

    // Upload build files to S3
    await this.uploadToS3(projectFiles, bucketName, sessionId, deployment);
  }

  async uploadToS3(projectFiles, bucketName, sessionId, deployment) {
    console.log(`[${sessionId}] Uploading files to S3 bucket: ${bucketName}`);
    
    return new Promise((resolve, reject) => {
      const sync = spawn('aws', ['s3', 'sync', projectFiles, `s3://${bucketName}`, '--delete'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let syncLogs = '';

      sync.stdout.on('data', (data) => {
        const log = data.toString();
        syncLogs += log;
        deployment.logs.push(`[S3 SYNC] ${log.trim()}`);
        console.log(`[${sessionId}] s3 sync: ${log.trim()}`);
      });

      sync.stderr.on('data', (data) => {
        const log = data.toString();
        syncLogs += log;
        deployment.logs.push(`[S3 SYNC ERROR] ${log.trim()}`);
        console.error(`[${sessionId}] s3 sync error: ${log.trim()}`);
      });

      sync.on('close', (code) => {
        if (code === 0) {
          console.log(`[${sessionId}] S3 sync completed`);
          resolve();
        } else {
          reject(new Error(`S3 sync failed with exit code ${code}`));
        }
      });

      sync.on('error', (error) => {
        reject(new Error(`S3 sync process error: ${error.message}`));
      });
    });
  }

  async invalidateCloudFront(deployment, sessionId) {
    const distributionId = deployment.terraformOutputs.cloudfront_distribution_id;
    if (!distributionId) {
      console.log(`[${sessionId}] No CloudFront distribution ID found, skipping invalidation`);
      return;
    }

    console.log(`[${sessionId}] Invalidating CloudFront cache...`);
    
    return new Promise((resolve, reject) => {
      const invalidate = spawn('aws', ['cloudfront', 'create-invalidation', '--distribution-id', distributionId, '--paths', '/*'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let invalidateLogs = '';

      invalidate.stdout.on('data', (data) => {
        const log = data.toString();
        invalidateLogs += log;
        deployment.logs.push(`[CLOUDFRONT] ${log.trim()}`);
        console.log(`[${sessionId}] cloudfront invalidation: ${log.trim()}`);
      });

      invalidate.stderr.on('data', (data) => {
        const log = data.toString();
        invalidateLogs += log;
        deployment.logs.push(`[CLOUDFRONT ERROR] ${log.trim()}`);
        console.error(`[${sessionId}] cloudfront invalidation error: ${log.trim()}`);
      });

      invalidate.on('close', (code) => {
        if (code === 0) {
          console.log(`[${sessionId}] CloudFront invalidation completed`);
          resolve();
        } else {
          console.warn(`[${sessionId}] CloudFront invalidation failed, but continuing...`);
          resolve(); // Don't fail deployment for invalidation issues
        }
      });

      invalidate.on('error', (error) => {
        console.warn(`[${sessionId}] CloudFront invalidation error: ${error.message}`);
        resolve(); // Don't fail deployment for invalidation issues
      });
    });
  }

  async destroyStack(terraformPath, sessionId) {
    console.log(`[${sessionId}] Destroying Terraform stack...`);
    
    return new Promise((resolve, reject) => {
      const destroy = spawn('terraform', ['destroy', '-auto-approve', '-var-file=terraform.tfvars'], {
        cwd: terraformPath,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      destroy.stdout.on('data', (data) => {
        console.log(`[${sessionId}] terraform destroy: ${data.toString().trim()}`);
      });

      destroy.stderr.on('data', (data) => {
        console.error(`[${sessionId}] terraform destroy error: ${data.toString().trim()}`);
      });

      destroy.on('close', (code) => {
        if (code === 0) {
          console.log(`[${sessionId}] Terraform destroy completed`);
          resolve();
        } else {
          reject(new Error(`Terraform destroy failed with exit code ${code}`));
        }
      });

      destroy.on('error', (error) => {
        reject(new Error(`Terraform destroy process error: ${error.message}`));
      });
    });
  }
}

module.exports = AWSDeployer;
