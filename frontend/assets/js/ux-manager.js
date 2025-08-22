/**
 * UX Manager - Handles user experience enhancements
 * - Smart contextual help
 * - Session persistence
 * - Progressive loading states
 * - Error recovery suggestions
 */

class UXManager {
    constructor() {
        this.sessionKey = 'codeflowops_session';
        this.helpSuggestions = new Map();
        this.retryAttempts = new Map();
        this.maxRetries = 3;
        this.init();
    }

    init() {
        this.loadSavedSession();
        this.initializeHelpers();
        this.setupErrorRecovery();
        this.setupProgressTracking();
    }

    // Session Persistence - Resume incomplete sessions
    loadSavedSession() {
        const savedSession = localStorage.getItem(this.sessionKey);
        if (savedSession) {
            try {
                const session = JSON.parse(savedSession);
                if (this.isValidSession(session)) {
                    this.resumeSession(session);
                }
            } catch (error) {
                console.warn('Failed to load saved session:', error);
                this.clearSavedSession();
            }
        }
    }

    isValidSession(session) {
        const maxAge = 24 * 60 * 60 * 1000; // 24 hours
        const sessionAge = Date.now() - session.timestamp;
        return sessionAge < maxAge && session.sessionId && session.step;
    }

    saveSession(sessionData) {
        const sessionToSave = {
            ...sessionData,
            timestamp: Date.now()
        };
        localStorage.setItem(this.sessionKey, JSON.stringify(sessionToSave));
    }

    resumeSession(session) {
        console.log(`Resuming session from step: ${session.step}`);
        
        // Show resume notification
        this.showResumeNotification(session);
        
        // Redirect to appropriate step
        this.navigateToStep(session.step, session);
    }

    showResumeNotification(session) {
        const notification = document.createElement('div');
        notification.className = 'resume-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">RESUME</div>
                <div class="notification-text">
                    <h4>Resume Previous Deployment</h4>
                    <p>Continue your deployment for "${session.projectName || 'project'}" from ${session.step}</p>
                </div>
                <div class="notification-actions">
                    <button onclick="uxManager.resumeFromSaved()" class="btn-resume">Continue</button>
                    <button onclick="uxManager.startFresh()" class="btn-fresh">Start Fresh</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        setTimeout(() => notification.classList.add('show'), 100);
    }

    // Smart Contextual Help
    initializeHelpers() {
        this.helpSuggestions.set('invalid_repo', {
            message: 'Repository not found or not accessible',
            suggestions: [
                'Check if the repository is public',
                'Verify the GitHub URL format',
                'Try: https://github.com/username/repository'
            ],
            autoFix: this.suggestRepoCorrections.bind(this)
        });

        this.helpSuggestions.set('build_failed', {
            message: 'Build process failed',
            suggestions: [
                'Check if package.json exists',
                'Verify build script is defined',
                'Ensure dependencies are compatible'
            ],
            autoFix: this.suggestBuildFixes.bind(this)
        });

        this.helpSuggestions.set('timeout_error', {
            message: 'Process timed out',
            suggestions: [
                'Large repositories may take longer',
                'Check your internet connection',
                'Try again with a smaller repository first'
            ],
            autoFix: this.offerRetryOptions.bind(this)
        });
    }

    // Progressive Loading States
    showProgressState(step, message, progress = 0) {
        const progressContainer = document.getElementById('progressContainer') || this.createProgressContainer();
        
        progressContainer.innerHTML = `
            <div class="progress-header">
                <h3>${this.getStepTitle(step)}</h3>
                <div class="progress-status">${message}</div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${progress}%"></div>
            </div>
            <div class="progress-details">
                <div class="current-step">${step}</div>
                <div class="estimated-time">${this.getEstimatedTime(step)}</div>
            </div>
        `;

        // Update session with current progress
        this.saveSession({
            sessionId: window.sessionManager?.sessionId,
            step: step,
            progress: progress,
            message: message,
            projectName: this.getCurrentProjectName()
        });
    }

    createProgressContainer() {
        const container = document.createElement('div');
        container.id = 'progressContainer';
        container.className = 'progress-container';
        
        const main = document.querySelector('.main');
        if (main) {
            main.appendChild(container);
        }
        
        return container;
    }

    getStepTitle(step) {
        const titles = {
            'analyzing': 'Analyzing Repository',
            'building': 'Building Project',
            'deploying': 'Deploying to AWS',
            'finalizing': 'Finalizing Setup'
        };
        return titles[step] || 'Processing';
    }

    getEstimatedTime(step) {
        const estimates = {
            'analyzing': '30-60 seconds',
            'building': '2-5 minutes',
            'deploying': '3-8 minutes',
            'finalizing': '1-2 minutes'
        };
        return `Est. ${estimates[step] || '1-3 minutes'}`;
    }

    // Error Recovery and Smart Suggestions
    handleError(error, context = {}) {
        const errorType = this.categorizeError(error);
        const helper = this.helpSuggestions.get(errorType);
        
        if (helper) {
            this.showSmartErrorDialog(error, helper, context);
        } else {
            this.showGenericErrorDialog(error, context);
        }

        // Track retry attempts
        const retryCount = this.retryAttempts.get(context.sessionId) || 0;
        this.retryAttempts.set(context.sessionId, retryCount + 1);
    }

    categorizeError(error) {
        const message = error.message || error.toString().toLowerCase();
        
        if (message.includes('repository') || message.includes('not found')) {
            return 'invalid_repo';
        }
        if (message.includes('build') || message.includes('npm')) {
            return 'build_failed';
        }
        if (message.includes('timeout') || message.includes('time')) {
            return 'timeout_error';
        }
        
        return 'unknown_error';
    }

    showSmartErrorDialog(error, helper, context) {
        const dialog = document.createElement('div');
        dialog.className = 'smart-error-dialog';
        dialog.innerHTML = `
            <div class="dialog-overlay">
                <div class="dialog-content">
                    <div class="error-header">
                        <div class="error-icon">ERROR</div>
                        <h3>${helper.message}</h3>
                    </div>
                    
                    <div class="error-details">
                        <p>${error.message}</p>
                    </div>
                    
                    <div class="suggestions">
                        <h4>Let's try to fix this:</h4>
                        <ul>
                            ${helper.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                        </ul>
                    </div>
                    
                    <div class="auto-fix-section" id="autoFixSection">
                        <!-- Auto-fix suggestions will be inserted here -->
                    </div>
                    
                    <div class="dialog-actions">
                        <button onclick="uxManager.retryWithFix('${context.sessionId}')" class="btn-retry">
                            Try Again
                        </button>
                        <button onclick="uxManager.contactSupport()" class="btn-support">
                            Get Help
                        </button>
                        <button onclick="uxManager.closeDialog()" class="btn-cancel">
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
        
        // Run auto-fix helper
        if (helper.autoFix) {
            helper.autoFix(context).then(fixes => {
                this.displayAutoFixes(fixes);
            });
        }
        
        setTimeout(() => dialog.classList.add('show'), 100);
    }

    // Smart Auto-Fix Suggestions
    async suggestRepoCorrections(context) {
        const url = context.githubUrl;
        if (!url) return [];

        const fixes = [];
        
        // Common URL corrections
        if (!url.startsWith('https://github.com/')) {
            if (url.includes('github.com')) {
                fixes.push({
                    type: 'url_correction',
                    suggestion: 'Add https:// prefix',
                    correctedUrl: `https://github.com/${url.split('github.com/')[1]}`
                });
            }
        }
        
        // Check for typos in popular repositories
        const popularRepos = await this.getPopularRepoSuggestions(url);
        fixes.push(...popularRepos);
        
        return fixes;
    }

    async suggestBuildFixes(context) {
        const fixes = [];
        
        // Common build script fixes
        fixes.push({
            type: 'build_script',
            suggestion: 'Add missing build script to package.json',
            command: 'npm run build',
            autoApply: true
        });
        
        fixes.push({
            type: 'dependency_update',
            suggestion: 'Update dependencies to compatible versions',
            command: 'npm update',
            autoApply: false
        });
        
        return fixes;
    }

    async offerRetryOptions(context) {
        const retryCount = this.retryAttempts.get(context.sessionId) || 0;
        const fixes = [];
        
        if (retryCount < this.maxRetries) {
            fixes.push({
                type: 'retry',
                suggestion: `Retry with extended timeout (attempt ${retryCount + 1}/${this.maxRetries})`,
                timeout: Math.min(600000, 300000 * (retryCount + 1)) // Progressive timeout increase
            });
        }
        
        fixes.push({
            type: 'alternative',
            suggestion: 'Try deploying a smaller test repository first',
            testRepos: [
                'https://github.com/facebook/create-react-app',
                'https://github.com/vercel/next.js'
            ]
        });
        
        return fixes;
    }

    displayAutoFixes(fixes) {
        const autoFixSection = document.getElementById('autoFixSection');
        if (!autoFixSection || fixes.length === 0) return;
        
        autoFixSection.innerHTML = `
            <h4>Suggested Fixes:</h4>
            <div class="auto-fixes">
                ${fixes.map((fix, index) => `
                    <div class="fix-option" data-fix-index="${index}">
                        <div class="fix-description">${fix.suggestion}</div>
                        ${fix.correctedUrl ? `
                            <div class="fix-action">
                                <input type="text" value="${fix.correctedUrl}" readonly>
                                <button onclick="uxManager.applyFix(${index})" class="btn-apply">Use This</button>
                            </div>
                        ` : ''}
                        ${fix.autoApply ? `
                            <button onclick="uxManager.applyFix(${index})" class="btn-auto-apply">Apply Automatically</button>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    // Retry Mechanism with Context
    retryWithFix(sessionId) {
        const retryCount = this.retryAttempts.get(sessionId) || 0;
        
        if (retryCount >= this.maxRetries) {
            this.showMaxRetriesDialog();
            return;
        }
        
        // Close current dialog
        this.closeDialog();
        
        // Show retry progress
        this.showProgressState('retrying', `Retry attempt ${retryCount + 1}`, 0);
        
        // Trigger retry with current session context
        const savedSession = JSON.parse(localStorage.getItem(this.sessionKey));
        if (savedSession) {
            this.resumeFromStep(savedSession.step, savedSession);
        }
    }

    // Success States with Clear Next Steps
    showSuccess(type, data) {
        const successDialog = document.createElement('div');
        successDialog.className = 'success-dialog';
        successDialog.innerHTML = `
            <div class="dialog-overlay">
                <div class="dialog-content success">
                    <div class="success-header">
                        <div class="success-icon">SUCCESS</div>
                        <h3>${this.getSuccessTitle(type)}</h3>
                    </div>
                    
                    <div class="success-details">
                        ${this.getSuccessDetails(type, data)}
                    </div>
                    
                    <div class="next-steps">
                        <h4>What's Next?</h4>
                        ${this.getNextSteps(type, data)}
                    </div>
                    
                    <div class="dialog-actions">
                        <button onclick="uxManager.visitSite('${data.url}')" class="btn-primary">
                            Visit Your Site
                        </button>
                        <button onclick="uxManager.deployAnother()" class="btn-secondary">
                            Deploy Another
                        </button>
                        <button onclick="uxManager.closeDialog()" class="btn-cancel">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(successDialog);
        setTimeout(() => successDialog.classList.add('show'), 100);
        
        // Clear saved session on success
        this.clearSavedSession();
    }

    // Utility Methods
    getCurrentProjectName() {
        const projectNameInput = document.getElementById('projectName');
        const githubUrlInput = document.getElementById('githubUrl');
        
        if (projectNameInput?.value) {
            return projectNameInput.value;
        }
        
        if (githubUrlInput?.value) {
            const match = githubUrlInput.value.match(/github\.com\/[^\/]+\/([^\/]+)/);
            return match ? match[1] : 'project';
        }
        
        return 'project';
    }

    clearSavedSession() {
        localStorage.removeItem(this.sessionKey);
    }

    closeDialog() {
        const dialogs = document.querySelectorAll('.smart-error-dialog, .success-dialog, .resume-notification');
        dialogs.forEach(dialog => {
            dialog.classList.remove('show');
            setTimeout(() => dialog.remove(), 300);
        });
    }

    visitSite(url) {
        window.open(url, '_blank');
        this.closeDialog();
    }

    deployAnother() {
        this.clearSavedSession();
        window.location.href = '/';
    }

    // Advanced UX Features
    setupSmartDefaults() {
        // Auto-complete GitHub URLs
        const githubInput = document.getElementById('githubUrl');
        if (githubInput) {
            githubInput.addEventListener('input', this.handleGithubInputSuggestions.bind(this));
        }
        
        // Smart project name extraction
        const projectNameInput = document.getElementById('projectName');
        if (projectNameInput && githubInput) {
            githubInput.addEventListener('blur', () => {
                if (!projectNameInput.value && githubInput.value) {
                    const suggested = this.extractProjectName(githubInput.value);
                    if (suggested) {
                        projectNameInput.value = suggested;
                        this.showAutoFillNotification('Project name auto-filled');
                    }
                }
            });
        }
    }

    extractProjectName(githubUrl) {
        const match = githubUrl.match(/github\.com\/[^\/]+\/([^\/\?]+)/);
        if (match) {
            return match[1].replace(/[^a-zA-Z0-9-]/g, '-').toLowerCase();
        }
        return null;
    }

    showAutoFillNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'auto-fill-notification';
        notification.textContent = message;
        
        document.body.appendChild(notification);
        setTimeout(() => notification.classList.add('show'), 100);
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize UX Manager
const uxManager = new UXManager();
