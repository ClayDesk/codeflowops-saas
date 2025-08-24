/**
 * ProjectAnalyzer.js - Intelligent React vs Static site detection
 */

class ProjectAnalyzer {
  constructor() {
    this.detectionRules = {
      react: {
        files: ['package.json', 'src/App.js', 'src/index.js', 'public/index.html'],
        packageJsonSignatures: ['react', 'react-dom', 'react-scripts'],
        folderStructure: ['src/', 'public/'],
        buildCommands: ['npm run build', 'yarn build']
      },
      static: {
        files: ['index.html', '*.html'],
        excludes: ['package.json with react'],
        patterns: ['.html', '.css', '.js', '.png', '.jpg', '.svg']
      }
    };
  }

  async analyzeProject(repoPath, sessionId) {
    console.log(`[${sessionId}] Starting project analysis...`);
    
    const analysis = {
      sessionId,
      projectType: null,
      buildRequired: false,
      dependencies: [],
      buildCommand: null,
      buildOutputDir: null,
      recommendedStack: null,
      confidence: 0
    };

    try {
      // Check for React project
      if (await this.isReactProject(repoPath)) {
        analysis.projectType = 'react';
        analysis.buildRequired = true;
        analysis.buildCommand = await this.detectBuildCommand(repoPath);
        analysis.buildOutputDir = await this.detectBuildOutputDir(repoPath);
        analysis.dependencies = await this.extractDependencies(repoPath);
        analysis.recommendedStack = 'react-app'; // S3 + CloudFront + CodeBuild
        analysis.confidence = 0.95;
      }
      // Check for static site
      else if (await this.isStaticSite(repoPath)) {
        analysis.projectType = 'static';
        analysis.buildRequired = false;
        analysis.recommendedStack = 'static-site'; // S3 + CloudFront + IAM
        analysis.confidence = 0.90;
      }
      else {
        throw new Error('Unsupported project type. Only React apps and static sites are supported.');
      }

      console.log(`[${sessionId}] Analysis complete: ${analysis.projectType} project detected`);
      return analysis;
      
    } catch (error) {
      console.error(`[${sessionId}] Analysis failed:`, error.message);
      throw error;
    }
  }

  async isReactProject(repoPath) {
    const fs = require('fs').promises;
    const path = require('path');

    try {
      // Check package.json for React dependencies
      const packageJsonPath = path.join(repoPath, 'package.json');
      const packageJson = JSON.parse(await fs.readFile(packageJsonPath, 'utf8'));
      
      const dependencies = { ...packageJson.dependencies, ...packageJson.devDependencies };
      const hasReact = dependencies.react || dependencies['react-dom'];
      
      if (!hasReact) return false;

      // Check for typical React structure
      const srcExists = await this.dirExists(path.join(repoPath, 'src'));
      const publicExists = await this.dirExists(path.join(repoPath, 'public'));
      
      return srcExists && publicExists;
      
    } catch (error) {
      return false;
    }
  }

  async isStaticSite(repoPath) {
    const fs = require('fs').promises;
    const path = require('path');

    try {
      // Check for HTML files in root
      const files = await fs.readdir(repoPath);
      const hasHtmlFiles = files.some(file => file.endsWith('.html'));
      
      // Ensure it's not a React project
      const packageJsonExists = await this.fileExists(path.join(repoPath, 'package.json'));
      if (packageJsonExists) {
        const isReact = await this.isReactProject(repoPath);
        if (isReact) return false;
      }
      
      return hasHtmlFiles;
      
    } catch (error) {
      return false;
    }
  }

  async detectBuildCommand(repoPath) {
    const fs = require('fs').promises;
    const path = require('path');
    
    try {
      const packageJsonPath = path.join(repoPath, 'package.json');
      const packageJson = JSON.parse(await fs.readFile(packageJsonPath, 'utf8'));
      
      const scripts = packageJson.scripts || {};
      
      if (scripts.build) return 'npm run build';
      if (scripts['build:prod']) return 'npm run build:prod';
      if (scripts.start) return 'npm run start'; // Fallback
      
      return 'npm run build'; // Default
      
    } catch (error) {
      return 'npm run build';
    }
  }

  async detectBuildOutputDir(repoPath) {
    const fs = require('fs').promises;
    const path = require('path');
    
    // Common React build output directories
    const commonDirs = ['build', 'dist', 'out', 'public'];
    
    for (const dir of commonDirs) {
      if (await this.dirExists(path.join(repoPath, dir))) {
        return dir;
      }
    }
    
    return 'build'; // Default for React
  }

  async extractDependencies(repoPath) {
    const fs = require('fs').promises;
    const path = require('path');
    
    try {
      const packageJsonPath = path.join(repoPath, 'package.json');
      const packageJson = JSON.parse(await fs.readFile(packageJsonPath, 'utf8'));
      
      return {
        dependencies: packageJson.dependencies || {},
        devDependencies: packageJson.devDependencies || {},
        engines: packageJson.engines || {}
      };
      
    } catch (error) {
      return { dependencies: {}, devDependencies: {}, engines: {} };
    }
  }

  async fileExists(filePath) {
    const fs = require('fs').promises;
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  async dirExists(dirPath) {
    const fs = require('fs').promises;
    try {
      const stats = await fs.stat(dirPath);
      return stats.isDirectory();
    } catch {
      return false;
    }
  }
}

module.exports = ProjectAnalyzer;
