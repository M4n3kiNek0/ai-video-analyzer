// ========================================
// Utility Functions Module
// ========================================

window.Utils = {
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    formatDuration(seconds) {
        if (!seconds || isNaN(seconds)) return 'N/A';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    },

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('it-IT', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    isVideoFormat(filename) {
        if (!filename) return false;
        const ext = '.' + filename.split('.').pop().toLowerCase();
        return AppState.VIDEO_FORMATS.includes(ext);
    },
    
    isAudioFormat(filename) {
        if (!filename) return false;
        const ext = '.' + filename.split('.').pop().toLowerCase();
        return AppState.AUDIO_FORMATS.includes(ext);
    },
    
    // Legacy message function - redirects to Toast
    showMessage(message, type = 'info') {
        Toast.show(message, type);
    },
    
    // Toast wrapper for settings module
    showToast(message, type = 'info') {
        if (typeof Toast !== 'undefined' && Toast.show) {
            Toast.show(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
};

// ========================================
// Toast Notification System
// ========================================

window.Toast = {
    container: null,
    
    getContainer() {
        if (!this.container) {
            this.container = document.getElementById('toastContainer');
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.id = 'toastContainer';
                this.container.className = 'toast-container';
                document.body.appendChild(this.container);
            }
        }
        return this.container;
    },
    
    show(message, type = 'info', duration = 5000) {
        const container = this.getContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        // Icon based on type
        const icons = {
            success: 'check-circle',
            error: 'x-circle',
            warning: 'alert-triangle',
            info: 'info'
        };
        
        toast.innerHTML = `
            <span class="toast-icon"><i data-lucide="${icons[type] || 'info'}"></i></span>
            <span class="toast-message">${Utils.escapeHtml(message)}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i data-lucide="x"></i>
            </button>
        `;
        
        container.appendChild(toast);
        
        // Initialize Lucide icons in the toast
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                toast.classList.add('toast-exit');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
        
        return toast;
    },
    
    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    },
    
    error(message, duration = 7000) {
        return this.show(message, 'error', duration);
    },
    
    warning(message, duration = 5000) {
        return this.show(message, 'warning', duration);
    },
    
    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }
};

// Global toast function for easy access
window.showToast = (message, type, duration) => Toast.show(message, type, duration);

