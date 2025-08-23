/**
 * ReactBuilder.js - Automated npm install & build for React projects
 */

const { spawn } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

class ReactBuilder {
  constructor() {
    this.buildTimeout = 10 * 60 * 1000; // 10 minutes timeout
  }

  async buildReactProject(repoPath, sessionId, analysis) {
    console.log(`[${sessionId}] Starting React build process...`);
    
    const buildResult = {
      sessionId,
      success: false,
      buildOutputPath: null,
      buildLogs: [],
      buildTime: 0,
      builtFiles: [],
      errors: []
    };

    const startTime = Date.now();

    try {
      // Step 1: Install dependencies
      await this.installDependencies(repoPath, sessionId, buildResult);
      
      // Step 2: Run build command
      await this.runBuild(repoPath, sessionId, analysis.buildCommand, buildResult);
      
      // Step 3: Verify build output
      await this.verifyBuildOutput(repoPath, analysis.buildOutputDir, buildResult);
      
      // Step 4: Prepare for deployment
      await this.prepareBuildForDeployment(repoPath, analysis.buildOutputDir, buildResult);
      
      buildResult.success = true;
      buildResult.buildTime = Date.now() - startTime;
      
      console.log(`[${sessionId}] React build completed successfully in ${buildResult.buildTime}ms`);
      return buildResult;
      
    } catch (error) {
      buildResult.success = false;
      buildResult.errors.push(error.message);
      buildResult.buildTime = Date.now() - startTime;
      
      console.error(`[${sessionId}] React build failed:`, error.message);
      throw error;
    }
  }

  async installDependencies(repoPath, sessionId, buildResult) {
    console.log(`[${sessionId}] Installing npm dependencies...`);
    
    return new Promise((resolve, reject) => {
      const npmInstall = spawn('npm', ['install'], {
        cwd: repoPath,
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true
      });

      let installLogs = '';

      npmInstall.stdout.on('data', (data) => {
        const log = data.toString();
        installLogs += log;
        buildResult.buildLogs.push(`[INSTALL] ${log.trim()}`);
        console.log(`[${sessionId}] npm install: ${log.trim()}`);
      });

      npmInstall.stderr.on('data', (data) => {
        const log = data.toString();
        installLogs += log;
        buildResult.buildLogs.push(`[INSTALL ERROR] ${log.trim()}`);
        console.error(`[${sessionId}] npm install error: ${log.trim()}`);
      });

      npmInstall.on('close', (code) => {
        if (code === 0) {
          console.log(`[${sessionId}] npm install completed successfully`);
          resolve();
        } else {
          reject(new Error(`npm install failed with exit code ${code}`));
        }
      });

      npmInstall.on('error', (error) => {
        reject(new Error(`npm install process error: ${error.message}`));
      });

      // Timeout handling
      setTimeout(() => {
        npmInstall.kill();
        reject(new Error('npm install timeout after 10 minutes'));
      }, this.buildTimeout);
    });
  }

  async runBuild(repoPath, sessionId, buildCommand, buildResult) {
    console.log(`[${sessionId}] Running build command: ${buildCommand}`);
    
    const [command, ...args] = buildCommand.split(' ');
    
    return new Promise((resolve, reject) => {
      const buildProcess = spawn(command, args, {
        cwd: repoPath,
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true
      });

      let buildLogs = '';

      buildProcess.stdout.on('data', (data) => {
        const log = data.toString();
        buildLogs += log;
        buildResult.buildLogs.push(`[BUILD] ${log.trim()}`);
        console.log(`[${sessionId}] build: ${log.trim()}`);
      });

      buildProcess.stderr.on('data', (data) => {
        const log = data.toString();
        buildLogs += log;
        buildResult.buildLogs.push(`[BUILD ERROR] ${log.trim()}`);
        console.error(`[${sessionId}] build error: ${log.trim()}`);
      });

      buildProcess.on('close', (code) => {
        if (code === 0) {
          console.log(`[${sessionId}] Build completed successfully`);
          resolve();
        } else {
          reject(new Error(`Build failed with exit code ${code}`));
        }
      });

      buildProcess.on('error', (error) => {
        reject(new Error(`Build process error: ${error.message}`));
      });

      // Timeout handling
      setTimeout(() => {
        buildProcess.kill();
        reject(new Error('Build timeout after 10 minutes'));
      }, this.buildTimeout);
    });
  }

  async verifyBuildOutput(repoPath, buildOutputDir, buildResult) {
    const buildPath = path.join(repoPath, buildOutputDir);
    
    try {
      const stats = await fs.stat(buildPath);
      if (!stats.isDirectory()) {
        throw new Error(`Build output directory ${buildOutputDir} not found`);
      }

      // List all files in build directory
      const files = await this.getAllFiles(buildPath);
      buildResult.builtFiles = files;
      buildResult.buildOutputPath = buildPath;
      
      // Check for essential files
      const hasIndexHtml = files.some(file => file.endsWith('index.html'));
      if (!hasIndexHtml) {
        throw new Error('Build output missing index.html file');
      }
      
      console.log(`Build verification successful. Found ${files.length} files.`);
      
    } catch (error) {
      throw new Error(`Build verification failed: ${error.message}`);
    }
  }

  async prepareBuildForDeployment(repoPath, buildOutputDir, buildResult) {
    const buildPath = path.join(repoPath, buildOutputDir);
    const deploymentPath = path.join(repoPath, 'deployment-ready');
    
    try {
      // Create deployment-ready directory
      await fs.mkdir(deploymentPath, { recursive: true });
      
      // Copy build files to deployment directory
      await this.copyDirectory(buildPath, deploymentPath);
      
      buildResult.deploymentPath = deploymentPath;
      
      console.log('Build prepared for deployment');
      
    } catch (error) {
      throw new Error(`Failed to prepare build for deployment: ${error.message}`);
    }
  }

  async getAllFiles(dirPath, filesList = []) {
    const files = await fs.readdir(dirPath);
    
    for (const file of files) {
      const filePath = path.join(dirPath, file);
      const stats = await fs.stat(filePath);
      
      if (stats.isDirectory()) {
        await this.getAllFiles(filePath, filesList);
      } else {
        filesList.push(filePath);
      }
    }
    
    return filesList;
  }

  async copyDirectory(src, dest) {
    await fs.mkdir(dest, { recursive: true });
    const files = await fs.readdir(src);
    
    for (const file of files) {
      const srcPath = path.join(src, file);
      const destPath = path.join(dest, file);
      const stats = await fs.stat(srcPath);
      
      if (stats.isDirectory()) {
        await this.copyDirectory(srcPath, destPath);
      } else {
        await fs.copyFile(srcPath, destPath);
      }
    }
  }
}

module.exports = ReactBuilder;
