/**
 * Enhanced App Controller with UX Integration
 * Handles form submission with smart error recovery and session persistence
 */

class AppController {
    constructor() {
        this.init();
    }

    init() {
        this.setupFormHandling();
        this.setupSmartInputs();
        this.initializeUXFeatures();
    }

    setupFormHandling() {
        const deployForm = document.getElementById('deployForm');
        if (deployForm) {
            deployForm.addEventListener('submit', this.handleFormSubmit.bind(this));
        }
    }

    setupSmartInputs() {
        const githubInput = document.getElementById('githubUrl');
        const projectNameInput = document.getElementById('projectName');

        if (githubInput) {
            // Smart URL validation and suggestions
            githubInput.addEventListener('input', this.handleGithubUrlInput.bind(this));
            githubInput.addEventListener('blur', this.autoFillProjectName.bind(this));
            
            // Auto-complete functionality
            githubInput.addEventListener('keyup', this.showUrlSuggestions.bind(this));
        }

        if (projectNameInput) {
            // Smart project name validation
            projectNameInput.addEventListener('input', this.validateProjectName.bind(this));
        }
    }

    initializeUXFeatures() {
        // Initialize smart defaults
        if (window.uxManager) {
            window.uxManager.setupSmartDefaults();
        }
    }

    async handleFormSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const githubUrl = formData.get('githubUrl');
        const projectName = formData.get('projectName');
        
        // Validate inputs
        if (!this.validateGithubUrl(githubUrl)) {
            this.showValidationError('Please enter a valid GitHub repository URL');
            return;
        }

        // Generate session ID if not exists
        const sessionId = window.sessionManager?.sessionId || this.generateSessionId();
        
        try {
            // Show initial progress
            this.showDeploymentProgress('starting', 'Initializing deployment...', 0);
            
            // Save session for persistence
            if (window.uxManager) {
                window.uxManager.saveSession({
                    sessionId: sessionId,
                    step: 'starting',
                    githubUrl: githubUrl,
                    projectName: projectName || this.extractProjectNameFromUrl(githubUrl),
                    progress: 0
                });
            }

            // Start deployment process
            await this.startDeployment({
                sessionId: sessionId,
                githubUrl: githubUrl,
                projectName: projectName
            });

        } catch (error) {
            console.error('Deployment failed:', error);
            
            // Use UX Manager for smart error handling
            if (window.uxManager) {
                window.uxManager.handleError(error, {
                    sessionId: sessionId,
                    githubUrl: githubUrl,
                    step: 'initialization'
                });
            } else {
                this.showGenericError(error);
            }
        }
    }

    async startDeployment(params) {
        const { sessionId, githubUrl, projectName } = params;
        
        // Step 1: Repository Analysis
        this.showDeploymentProgress('analyzing', 'Downloading and analyzing repository...', 15);
        
        try {
            const analysisResult = await this.analyzeRepository(sessionId, githubUrl);
            
            // Step 2: Project Type Detection
            this.showDeploymentProgress('detecting', 'Detecting project type and dependencies...', 35);
            
            const projectType = analysisResult.projectType;
            const buildConfig = analysisResult.buildConfig;
            
            // Step 3: Build Process (if needed)
            if (projectType === 'react') {
                this.showDeploymentProgress('building', 'Running npm install and build...', 50);
                await this.buildProject(sessionId, buildConfig);
            }
            
            // Step 4: Infrastructure Setup
            this.showDeploymentProgress('infrastructure', 'Provisioning AWS infrastructure...', 70);
            await this.setupInfrastructure(sessionId, projectType, projectName);
            
            // Step 5: Deployment
            this.showDeploymentProgress('deploying', 'Deploying files to AWS...', 85);
            const deploymentResult = await this.deployFiles(sessionId);
            
            // Step 6: Finalization
            this.showDeploymentProgress('finalizing', 'Configuring CDN and final setup...', 95);
            await this.finalizeDeployment(sessionId);
            
            // Success
            this.showDeploymentSuccess(deploymentResult);
            
        } catch (error) {
            throw error; // Re-throw for UX Manager handling
        }
    }

    async analyzeRepository(sessionId, githubUrl) {
        const response = await fetch('/api/analyze-repo', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                repository_url: githubUrl,
                branch: 'main'
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Repository analysis failed');
        }

        return await response.json();
    }

    async buildProject(sessionId, buildConfig) {
        const response = await fetch('/api/build', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sessionId: sessionId,
                buildConfig: buildConfig
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Build process failed');
        }

        return await response.json();
    }

    async setupInfrastructure(sessionId, projectType, projectName) {
        const response = await fetch('/api/infrastructure', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sessionId: sessionId,
                projectType: projectType,
                projectName: projectName
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Infrastructure setup failed');
        }

        return await response.json();
    }

    async deployFiles(sessionId) {
        const response = await fetch('/api/deploy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sessionId: sessionId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'File deployment failed');
        }

        return await response.json();
    }

    async finalizeDeployment(sessionId) {
        const response = await fetch('/api/finalize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sessionId: sessionId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Deployment finalization failed');
        }

        return await response.json();
    }

    // Smart Input Handlers
    handleGithubUrlInput(event) {
        const url = event.target.value;
        const isValid = this.validateGithubUrl(url);
        
        // Visual feedback
        event.target.classList.toggle('valid', isValid && url.length > 0);
        event.target.classList.toggle('invalid', !isValid && url.length > 0);
    }

    autoFillProjectName(event) {
        const githubUrl = event.target.value;
        const projectNameInput = document.getElementById('projectName');
        
        if (githubUrl && !projectNameInput.value) {
            const extractedName = this.extractProjectNameFromUrl(githubUrl);
            if (extractedName) {
                projectNameInput.value = extractedName;
                
                // Show helpful notification
                if (window.uxManager) {
                    window.uxManager.showAutoFillNotification('Project name auto-filled from repository');
                }
            }
        }
    }

    showUrlSuggestions(event) {
        const input = event.target;
        const value = input.value.toLowerCase();
        
        // Don't show suggestions for complete URLs
        if (value.startsWith('https://github.com/') && value.length > 25) {
            this.hideSuggestions(input);
            return;
        }
        
        // Show popular repository suggestions
        if (value.length > 3) {
            const suggestions = this.getPopularRepoSuggestions(value);
            this.showSuggestionDropdown(input, suggestions);
        } else {
            this.hideSuggestions(input);
        }
    }

    getPopularRepoSuggestions(query) {
        const popularRepos = [
            { url: 'https://github.com/facebook/create-react-app', name: 'Create React App', description: 'Official React starter template' },
            { url: 'https://github.com/vercel/next.js', name: 'Next.js', description: 'React framework for production' },
            { url: 'https://github.com/mui/material-ui', name: 'Material-UI', description: 'React UI framework' },
            { url: 'https://github.com/tailwindlabs/tailwindcss', name: 'Tailwind CSS', description: 'Utility-first CSS framework' },
            { url: 'https://github.com/vuejs/vue', name: 'Vue.js', description: 'Progressive JavaScript framework' },
            { url: 'https://github.com/angular/angular', name: 'Angular', description: 'Platform for mobile and desktop web apps' }
        ];
        
        return popularRepos.filter(repo => 
            repo.name.toLowerCase().includes(query) || 
            repo.description.toLowerCase().includes(query) ||
            repo.url.toLowerCase().includes(query)
        ).slice(0, 5);
    }

    showSuggestionDropdown(input, suggestions) {
        // Remove existing dropdown
        this.hideSuggestions(input);
        
        if (suggestions.length === 0) return;
        
        const dropdown = document.createElement('div');
        dropdown.className = 'input-suggestion';
        
        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.innerHTML = `
                <div class="suggestion-main">${suggestion.name}</div>
                <div class="suggestion-helper">${suggestion.description}</div>
            `;
            
            item.addEventListener('click', () => {
                input.value = suggestion.url;
                this.hideSuggestions(input);
                input.dispatchEvent(new Event('blur')); // Trigger auto-fill
            });
            
            dropdown.appendChild(item);
        });
        
        // Position dropdown
        const inputGroup = input.closest('.input-group');
        inputGroup.style.position = 'relative';
        inputGroup.appendChild(dropdown);
    }

    hideSuggestions(input) {
        const inputGroup = input.closest('.input-group');
        const existing = inputGroup.querySelector('.input-suggestion');
        if (existing) {
            existing.remove();
        }
    }

    validateProjectName(event) {
        const value = event.target.value;
        const isValid = /^[a-zA-Z0-9-]+$/.test(value) || value === '';
        
        event.target.classList.toggle('valid', isValid && value.length > 0);
        event.target.classList.toggle('invalid', !isValid && value.length > 0);
    }

    // Progress Display
    showDeploymentProgress(step, message, progress) {
        if (window.uxManager) {
            window.uxManager.showProgressState(step, message, progress);
        } else {
            // Fallback progress display
            this.updateProgressFallback(step, message, progress);
        }
    }

    updateProgressFallback(step, message, progress) {
        const deployBtn = document.getElementById('deployBtn');
        if (deployBtn) {
            const btnText = deployBtn.querySelector('.btn-text');
            const btnLoader = deployBtn.querySelector('.btn-loader');
            
            if (btnText && btnLoader) {
                btnText.style.display = 'none';
                btnLoader.style.display = 'flex';
                btnLoader.innerHTML = `
                    <div class="spinner"></div>
                    ${message}
                `;
            }
        }
    }

    showDeploymentSuccess(result) {
        if (window.uxManager) {
            window.uxManager.showSuccess('deployment', {
                url: result.siteUrl,
                cloudfront: result.cloudfrontUrl,
                s3: result.s3Bucket
            });
        } else {
            // Fallback success display
            alert(`Deployment successful! Your site is live at: ${result.siteUrl}`);
        }
    }

    // Utility Methods
    validateGithubUrl(url) {
        const githubPattern = /^https:\/\/github\.com\/[^\/]+\/[^\/]+\/?$/;
        return githubPattern.test(url);
    }

    extractProjectNameFromUrl(url) {
        const match = url.match(/github\.com\/[^\/]+\/([^\/\?]+)/);
        if (match) {
            return match[1].replace(/[^a-zA-Z0-9-]/g, '-').toLowerCase();
        }
        return null;
    }

    generateSessionId() {
        return 'sess_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
    }

    showValidationError(message) {
        // Simple validation error display
        const errorDiv = document.createElement('div');
        errorDiv.className = 'validation-error';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--error-color);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 1000;
            font-size: 14px;
        `;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    showGenericError(error) {
        console.error('Deployment error:', error);
        
        const errorMessage = error.message || 'An unexpected error occurred. Please try again.';
        this.showValidationError(errorMessage);
        
        // Reset form state
        const deployBtn = document.getElementById('deployBtn');
        if (deployBtn) {
            const btnText = deployBtn.querySelector('.btn-text');
            const btnLoader = deployBtn.querySelector('.btn-loader');
            
            if (btnText && btnLoader) {
                btnText.style.display = 'block';
                btnLoader.style.display = 'none';
            }
        }
    }
}

// Initialize App Controller when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new AppController();
    });
} else {
    new AppController();
}
