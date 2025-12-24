// ========================================
// Export Module
// ========================================

window.Export = {
    downloadPDF() {
        if (!AppState.currentVideoId) return;
        window.open(Api.getExportPdfUrl(AppState.currentVideoId), '_blank');
    },
    
    downloadZip() {
        if (!AppState.currentVideoId) return;
        window.open(Api.getExportZipUrl(AppState.currentVideoId), '_blank');
    },
    
    downloadHtml() {
        if (!AppState.currentVideoId) return;
        window.open(Api.getExportHtmlUrl(AppState.currentVideoId), '_blank');
    },
    
    downloadMarkdown() {
        if (!AppState.currentVideoId) return;
        window.open(Api.getExportMarkdownUrl(AppState.currentVideoId), '_blank');
    }
};

// Expose global functions for HTML onclick handlers
window.downloadPDF = () => Export.downloadPDF();
window.downloadZip = () => Export.downloadZip();
window.downloadExportZip = () => Export.downloadZip();

