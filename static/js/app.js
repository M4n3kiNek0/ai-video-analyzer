// ========================================
// Media Analyzer - Main Application Module
// ========================================

window.Navigation = {
    init() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const view = item.dataset.view;
                this.showView(view);
                
                // Close mobile sidebar
                MobileMenu.close();
                
                // Load data if needed
                if (view === 'videos') {
                    Videos.loadVideos();
                } else if (view === 'settings') {
                    if (typeof Settings !== 'undefined') {
                        // Always reload settings when navigating to settings view
                        if (Settings.reload) {
                            Settings.reload();
                        } else if (Settings.init) {
                            Settings.init();
                        }
                    }
                }
            });
        });
    },
    
    showView(viewName) {
        document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));
        const targetView = document.getElementById(`${viewName}View`);
        if (targetView) {
            targetView.classList.add('active');
        }
        
        // Update nav
        document.querySelectorAll('.nav-item').forEach(nav => {
            nav.classList.toggle('active', nav.dataset.view === viewName);
        });
        
        // Re-initialize Lucide icons for dynamic content
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
};

// ========================================
// Mobile Menu Handler
// ========================================

window.MobileMenu = {
    init() {
        const menuBtn = document.getElementById('mobileMenuBtn');
        const overlay = document.getElementById('sidebarOverlay');
        const sidebar = document.getElementById('sidebar');
        
        if (menuBtn) {
            menuBtn.addEventListener('click', () => this.toggle());
        }
        
        if (overlay) {
            overlay.addEventListener('click', () => this.close());
        }
        
        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.close();
        });
        
        // Touch swipe to close
        let touchStartX = 0;
        if (sidebar) {
            sidebar.addEventListener('touchstart', (e) => {
                touchStartX = e.touches[0].clientX;
            });
            
            sidebar.addEventListener('touchmove', (e) => {
                const touchX = e.touches[0].clientX;
                const diff = touchStartX - touchX;
                if (diff > 50) {
                    this.close();
                }
            });
        }
    },
    
    toggle() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        const isOpen = sidebar?.classList.contains('open');
        
        if (isOpen) {
            this.close();
        } else {
            this.open();
        }
    },
    
    open() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        sidebar?.classList.add('open');
        overlay?.classList.add('active');
        document.body.style.overflow = 'hidden';
    },
    
    close() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        sidebar?.classList.remove('open');
        overlay?.classList.remove('active');
        document.body.style.overflow = '';
    }
};

window.MediaType = {
    setMediaType(type) {
        // If file is already selected and type changes, reset file selection
        if (AppState.selectedFile && AppState.currentMediaType !== type) {
            Upload.resetFileSelection();
        }
        
        AppState.currentMediaType = type;
        
        // Update toggle buttons
        document.querySelectorAll('.toggle-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.type === type);
        });
        
        // Update upload zone
        const uploadIcon = document.getElementById('uploadIcon');
        const uploadTitle = document.getElementById('uploadTitle');
        const uploadHint = document.getElementById('uploadHint');
        const fileInput = document.getElementById('fileInput');
        const analysisTypeSection = document.getElementById('analysisTypeSection');
        const contextHint = document.getElementById('contextHint');
        
        if (type === 'audio') {
            if (uploadIcon) uploadIcon.innerHTML = '<i data-lucide="music"></i>';
            if (uploadTitle) uploadTitle.textContent = 'Trascina qui il tuo audio';
            if (uploadHint) uploadHint.textContent = 'Formati supportati: MP3, WAV, M4A, OGG, FLAC, AAC';
            if (fileInput) fileInput.accept = AppState.AUDIO_FORMATS.join(',');
            if (analysisTypeSection) analysisTypeSection.style.display = 'block';
            if (contextHint) contextHint.innerHTML = `
                <strong>Come descrivere il tuo audio:</strong><br>
                • Tipo di registrazione (meeting, intervista, podcast, brainstorming)<br>
                • Partecipanti e loro ruoli<br>
                • Argomenti principali discussi<br>
                • Contesto/obiettivo della registrazione<br>
                <em>Esempio: "Meeting settimanale del team marketing. Partecipanti: Marco (PM), Laura (Design), 
                Paolo (Dev). Discussione su lancio nuovo prodotto e timeline Q1 2025."</em>
            `;
        } else {
            if (uploadIcon) uploadIcon.innerHTML = '<i data-lucide="video"></i>';
            if (uploadTitle) uploadTitle.textContent = 'Trascina qui il tuo video';
            if (uploadHint) uploadHint.textContent = 'Formati supportati: MP4, MOV, AVI, MKV, WEBM';
            if (fileInput) fileInput.accept = AppState.VIDEO_FORMATS.join(',');
            if (analysisTypeSection) analysisTypeSection.style.display = 'none';
            if (contextHint) contextHint.innerHTML = `
                <strong>Come descrivere il tuo video:</strong><br>
                • Nome dell'applicazione mostrata<br>
                • Tipo di applicazione (POS, CRM, e-commerce, etc.)<br>
                • Funzionalità dimostrate nel video<br>
                • Settore/contesto d'uso<br>
                <em>Esempio: "Demo dell'app Tilby POS. Video mostra gestione tavoli ristorante: 
                creazione sale, aggiunta tavoli con drag&drop, modifica coperti. 
                Target: gestori ristoranti/bar."</em>
            `;
        }
        
        // Re-initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
};

// ========================================
// Lightbox for Keyframes
// ========================================

window.Lightbox = {
    currentIndex: 0,
    images: [],
    
    open(index, images) {
        this.currentIndex = index;
        this.images = images;
        this.show();
    },
    
    show() {
        const lightbox = document.getElementById('lightbox');
        const img = document.getElementById('lightboxImg');
        const caption = document.getElementById('lightboxCaption');
        
        if (!lightbox || !this.images[this.currentIndex]) return;
        
        const current = this.images[this.currentIndex];
        img.src = current.url;
        caption.textContent = current.caption || `Keyframe ${this.currentIndex + 1}`;
        
        lightbox.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Re-initialize icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    },
    
    close() {
        const lightbox = document.getElementById('lightbox');
        lightbox?.classList.remove('active');
        document.body.style.overflow = '';
    },
    
    prev() {
        this.currentIndex = (this.currentIndex - 1 + this.images.length) % this.images.length;
        this.show();
    },
    
    next() {
        this.currentIndex = (this.currentIndex + 1) % this.images.length;
        this.show();
    }
};

// Global lightbox functions
window.closeLightbox = () => Lightbox.close();
window.lightboxPrev = () => Lightbox.prev();
window.lightboxNext = () => Lightbox.next();

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    // Log API base for debugging
    console.log('App initialized. API_BASE:', AppState.API_BASE);
    console.log('Current origin:', window.location.origin);
    
    // Initialize Lucide Icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    Navigation.init();
    MobileMenu.init();
    Upload.init();
    
    // Initial API health check
    checkApiStatus().then(() => {
        console.log('Initial API health check completed');
    });
    
    // Check API status periodically
    setInterval(checkApiStatus, 30000);
    
    // Keyboard navigation for lightbox
    document.addEventListener('keydown', (e) => {
        const lightbox = document.getElementById('lightbox');
        if (!lightbox?.classList.contains('active')) return;
        
        if (e.key === 'Escape') Lightbox.close();
        if (e.key === 'ArrowLeft') Lightbox.prev();
        if (e.key === 'ArrowRight') Lightbox.next();
    });
});

// API Status Check
async function checkApiStatus() {
    const statusDot = document.getElementById('apiStatus');
    const statusText = document.getElementById('apiStatusText');
    if (!statusDot) return;
    
    const isOnline = await Api.checkHealth();
    
    statusDot.classList.toggle('online', isOnline);
    statusDot.classList.toggle('offline', !isOnline);
    if (statusText) {
        statusText.textContent = isOnline ? 'Sistema online' : 'Connessione fallita';
    }
}

// Expose global functions for HTML onclick handlers
window.showView = (viewName) => Navigation.showView(viewName);
window.setMediaType = (type) => MediaType.setMediaType(type);
window.checkApiStatus = checkApiStatus;

