// Report Scripts - External JS for HTML Reports

// Initialize Mermaid
mermaid.initialize({ 
    startOnLoad: true,
    theme: 'default',
    securityLevel: 'loose'
});

// Tab navigation
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // Remove active class from all tabs and contents
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Add active class to clicked tab and corresponding content
        tab.classList.add('active');
        const tabId = tab.getAttribute('data-tab');
        document.getElementById(tabId).classList.add('active');
    });
});

// Theme toggle
const themeToggle = document.getElementById('themeToggle');
if (themeToggle) {
    const sunIcon = themeToggle.querySelector('.icon-sun');
    const moonIcon = themeToggle.querySelector('.icon-moon');

    themeToggle.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
        if (sunIcon) sunIcon.style.display = isDark ? 'inline' : 'none';
        if (moonIcon) moonIcon.style.display = isDark ? 'none' : 'inline';
        
        // Reinitialize Mermaid with new theme
        mermaid.initialize({ 
            startOnLoad: false,
            theme: isDark ? 'default' : 'dark'
        });
        document.querySelectorAll('.mermaid').forEach(el => {
            el.removeAttribute('data-processed');
        });
        mermaid.init();
    });
}

// Lightbox
const lightbox = document.getElementById('lightbox');
const lightboxImg = document.getElementById('lightbox-img');
const lightboxCaption = document.getElementById('lightbox-caption');

document.querySelectorAll('.keyframe-image').forEach(img => {
    img.addEventListener('click', () => {
        if (lightbox && lightboxImg) {
            lightbox.classList.add('active');
            lightboxImg.src = img.src;
            if (lightboxCaption) lightboxCaption.textContent = img.alt;
        }
    });
});

const lightboxClose = document.querySelector('.lightbox-close');
if (lightboxClose) {
    lightboxClose.addEventListener('click', () => {
        if (lightbox) lightbox.classList.remove('active');
    });
}

if (lightbox) {
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) {
            lightbox.classList.remove('active');
        }
    });
}

// Keyboard navigation
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && lightbox) {
        lightbox.classList.remove('active');
    }
});

// Search functionality
const searchInput = document.getElementById('searchInput');

if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        
        // Remove previous highlights
        document.querySelectorAll('.highlight').forEach(el => {
            el.outerHTML = el.textContent;
        });
        
        if (query.length < 2) return;
        
        // Search and highlight in all text content
        const contentEl = document.querySelector('.content');
        if (!contentEl) return;
        
        const walker = document.createTreeWalker(
            contentEl,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        const matches = [];
        while (walker.nextNode()) {
            const node = walker.currentNode;
            const text = node.textContent;
            const lowerText = text.toLowerCase();
            
            if (lowerText.includes(query)) {
                matches.push(node);
            }
        }
        
        matches.forEach(node => {
            const text = node.textContent;
            const regex = new RegExp(`(${query})`, 'gi');
            const newHTML = text.replace(regex, '<span class="highlight">$1</span>');
            
            const span = document.createElement('span');
            span.innerHTML = newHTML;
            node.parentNode.replaceChild(span, node);
        });
        
        // Scroll to first match
        const firstHighlight = document.querySelector('.highlight');
        if (firstHighlight) {
            firstHighlight.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
}

