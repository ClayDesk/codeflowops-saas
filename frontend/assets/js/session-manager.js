/**
 * Session Manager - Handles unique session IDs across the application
 */
class SessionManager {
    static generateSessionId() {
        // Generate a UUID v4
        return 'sess_' + 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    static getSessionId() {
        let sessionId = sessionStorage.getItem('codeflowops_session_id');
        if (!sessionId) {
            sessionId = this.generateSessionId();
            sessionStorage.setItem('codeflowops_session_id', sessionId);
        }
        return sessionId;
    }

    static setSessionId(sessionId) {
        sessionStorage.setItem('codeflowops_session_id', sessionId);
    }

    static clearSession() {
        sessionStorage.removeItem('codeflowops_session_id');
        sessionStorage.removeItem('githubUrl');
        sessionStorage.removeItem('projectName');
        sessionStorage.removeItem('analysisResults');
        sessionStorage.removeItem('stackConfig');
        sessionStorage.removeItem('deploymentResults');
    }

    static storeProjectData(githubUrl, projectName) {
        sessionStorage.setItem('githubUrl', githubUrl);
        if (projectName) {
            sessionStorage.setItem('projectName', projectName);
        }
    }

    static getProjectData() {
        return {
            githubUrl: sessionStorage.getItem('githubUrl'),
            projectName: sessionStorage.getItem('projectName'),
            sessionId: this.getSessionId()
        };
    }

    static trackStep(step) {
        sessionStorage.setItem('current_step', step);
        sessionStorage.setItem('step_timestamp', Date.now().toString());
    }

    static getCurrentStep() {
        return sessionStorage.getItem('current_step') || 'index';
    }

    static getSessionInfo() {
        return {
            sessionId: this.getSessionId(),
            currentStep: this.getCurrentStep(),
            timestamp: sessionStorage.getItem('step_timestamp'),
            projectData: this.getProjectData()
        };
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SessionManager;
}
