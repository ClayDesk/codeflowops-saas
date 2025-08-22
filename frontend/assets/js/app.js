/**
 * CodeFlowOps SaaS - Main Application JavaScript
 * Handles form submission and navigation
 */

class CodeFlowOpsApp {
    constructor() {
        this.sessionManager = SessionManager;
        this.currentSessionId = this.sessionManager.getSessionId();
        
        this.init();
    }

    init() {
        this.displaySessionId();
        this.setupEventListeners();
        this.setupFormValidation();
    }

    displaySessionId() {
        const sessionElement = document.getElementById('sessionId');
        if (sessionElement) {
            sessionElement.textContent = this.currentSessionId.slice(0, 8);
        }

        // Show session info in debug mode
        if (window.location.search.includes('debug=true')) {
            const sessionInfo = document.getElementById('sessionInfo');
            if (sessionInfo) {
                sessionInfo.style.display = 'block';
                sessionInfo.querySelector('#sessionId').textContent = this.currentSessionId;
            }
        }
    }

    setupEventListeners() {
        // Deploy form submission
        const deployForm = document.getElementById('deployForm');
        if (deployForm) {
            deployForm.addEventListener('submit', this.handleDeploySubmit.bind(this));
        }

        // GitHub URL input validation
        const githubUrlInput = document.getElementById('githubUrl');
        if (githubUrlInput) {
            githubUrlInput.addEventListener('input', this.validateGitHubUrl.bind(this));
            githubUrlInput.addEventListener('paste', this.handleUrlPaste.bind(this));
        }

        // Project name input validation
        const projectNameInput = document.getElementById('projectName');
        if (projectNameInput) {
            projectNameInput.addEventListener('input', this.validateProjectName.bind(this));
        }

        // Auto-populate project name from GitHub URL
        if (githubUrlInput && projectNameInput) {
            githubUrlInput.addEventListener('input', () => {
                if (!projectNameInput.value) {
                    this.autoPopulateProjectName(githubUrlInput.value, projectNameInput);
                }
            });
        }
    }

    setupFormValidation() {
        // Real-time form validation
        const inputs = document.querySelectorAll('input[required]');
        inputs.forEach(input => {
            input.addEventListener('blur', this.validateInput.bind(this));
            input.addEventListener('input', this.clearValidationError.bind(this));
        });
    }

    async handleDeploySubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const githubUrl = formData.get('githubUrl');
        const projectName = formData.get('projectName');

        // Validate form
        if (!this.validateForm(githubUrl, projectName)) {
            return;
        }

        // Show loading state
        this.setLoadingState(true);

        try {
            // Store project data in session
            this.sessionManager.storeProjectData(githubUrl, projectName);
            this.sessionManager.trackStep('repository-analysis');

            // Navigate to analysis page
            const analysisUrl = `repository-analysis.html?repo=${encodeURIComponent(githubUrl)}`;
            
            // Add a small delay to show the loading state
            setTimeout(() => {
                window.location.href = analysisUrl;
            }, 1000);

        } catch (error) {
            console.error('Error starting deployment:', error);
            this.showError('Failed to start deployment. Please try again.');
            this.setLoadingState(false);
        }
    }

    validateForm(githubUrl, projectName) {
        let isValid = true;

        // Validate GitHub URL
        if (!this.validateGitHubUrl({ target: { value: githubUrl } })) {
            isValid = false;
        }

        // Validate project name if provided
        if (projectName && !this.validateProjectName({ target: { value: projectName } })) {
            isValid = false;
        }

        return isValid;
    }

    validateGitHubUrl(event) {
        const input = event.target;
        const url = input.value.trim();
        
        if (!url) {
            this.showInputError(input, 'GitHub URL is required');
            return false;
        }

        const githubPattern = /^https:\/\/github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\/?$/;
        
        if (!githubPattern.test(url)) {
            this.showInputError(input, 'Please enter a valid GitHub repository URL');
            return false;
        }

        this.clearInputError(input);
        return true;
    }

    validateProjectName(event) {
        const input = event.target;
        const name = input.value.trim();
        
        if (!name) {
            this.clearInputError(input);
            return true; // Project name is optional
        }

        const namePattern = /^[a-zA-Z0-9-]+$/;
        
        if (!namePattern.test(name) || name.length > 50) {
            this.showInputError(input, 'Project name must contain only letters, numbers, and hyphens (max 50 chars)');
            return false;
        }

        this.clearInputError(input);
        return true;
    }

    validateInput(event) {
        const input = event.target;
        
        if (input.id === 'githubUrl') {
            this.validateGitHubUrl(event);
        } else if (input.id === 'projectName') {
            this.validateProjectName(event);
        }
    }

    clearValidationError(event) {
        this.clearInputError(event.target);
    }

    showInputError(input, message) {
        // Remove existing error
        this.clearInputError(input);
        
        // Add error styling
        input.style.borderColor = '#e53e3e';
        input.style.boxShadow = '0 0 0 3px rgba(229, 62, 62, 0.1)';
        
        // Create error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'input-error';
        errorDiv.style.color = '#e53e3e';
        errorDiv.style.fontSize = '0.9rem';
        errorDiv.style.marginTop = '5px';
        errorDiv.textContent = message;
        
        // Insert error message
        input.parentNode.appendChild(errorDiv);
    }

    clearInputError(input) {
        // Reset styling
        input.style.borderColor = '';
        input.style.boxShadow = '';
        
        // Remove error message
        const existingError = input.parentNode.querySelector('.input-error');
        if (existingError) {
            existingError.remove();
        }
    }

    autoPopulateProjectName(githubUrl, projectNameInput) {
        const match = githubUrl.match(/github\.com\/[^\/]+\/([^\/]+)/);
        if (match) {
            let projectName = match[1];
            // Clean up the project name
            projectName = projectName.replace(/\.git$/, ''); // Remove .git extension
            projectName = projectName.replace(/[^a-zA-Z0-9-]/g, '-'); // Replace invalid chars
            projectName = projectName.replace(/-+/g, '-'); // Remove multiple dashes
            projectName = projectName.replace(/^-|-$/g, ''); // Remove leading/trailing dashes
            
            if (projectName && projectName.length <= 50) {
                projectNameInput.value = projectName;
            }
        }
    }

    handleUrlPaste(event) {
        // Allow some time for the paste to complete
        setTimeout(() => {
            this.validateGitHubUrl(event);
            
            const projectNameInput = document.getElementById('projectName');
            if (projectNameInput && !projectNameInput.value) {
                this.autoPopulateProjectName(event.target.value, projectNameInput);
            }
        }, 100);
    }

    setLoadingState(isLoading) {
        const deployBtn = document.getElementById('deployBtn');
        const btnText = deployBtn.querySelector('.btn-text');
        const btnLoader = deployBtn.querySelector('.btn-loader');
        
        if (isLoading) {
            btnText.style.display = 'none';
            btnLoader.style.display = 'flex';
            deployBtn.disabled = true;
        } else {
            btnText.style.display = 'block';
            btnLoader.style.display = 'none';
            deployBtn.disabled = false;
        }
    }

    showError(message) {
        // Create a toast notification or modal
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-toast';
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #fed7d7;
            border: 1px solid #fc8181;
            color: #c53030;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            max-width: 400px;
        `;
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }

    // Utility methods
    static formatSessionId(sessionId) {
        return sessionId.slice(0, 8);
    }

    static isValidGitHubUrl(url) {
        const pattern = /^https:\/\/github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\/?$/;
        return pattern.test(url);
    }

    static extractRepoInfo(githubUrl) {
        const match = githubUrl.match(/github\.com\/([^\/]+)\/([^\/]+)/);
        if (match) {
            return {
                owner: match[1],
                repo: match[2].replace(/\.git$/, '')
            };
        }
        return null;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CodeFlowOpsApp();
});

// Global utility functions
window.CodeFlowOps = {
    formatSessionId: CodeFlowOpsApp.formatSessionId,
    isValidGitHubUrl: CodeFlowOpsApp.isValidGitHubUrl,
    extractRepoInfo: CodeFlowOpsApp.extractRepoInfo
};
