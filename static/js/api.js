// ========================================
// API Communication Module
// ========================================

window.Api = {
    async checkHealth() {
        try {
            const response = await fetch(`${AppState.API_BASE}/health`);
            return response.ok;
        } catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    },

    async getVideos(filter = 'all') {
        try {
            const response = await fetch(`${AppState.API_BASE}/videos`);
            if (!response.ok) throw new Error('Failed to fetch videos');
            const data = await response.json();
            
            // Filter by media type if needed
            if (filter === 'video') {
                data.videos = data.videos.filter(v => v.media_type === 'video' || !v.media_type);
            } else if (filter === 'audio') {
                data.videos = data.videos.filter(v => v.media_type === 'audio');
            }
            
            return data;
        } catch (error) {
            console.error('Failed to fetch videos:', error);
            throw error;
        }
    },

    async getVideoDetail(videoId) {
        try {
            const response = await fetch(`${AppState.API_BASE}/videos/${videoId}`);
            if (!response.ok) throw new Error('Failed to fetch video detail');
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch video detail:', error);
            throw error;
        }
    },

    async uploadVideo(file, context, analysisType, onProgress) {
        const formData = new FormData();
        formData.append('file', file);
        if (context) {
            formData.append('context', context);
        }
        formData.append('analysis_type', analysisType || 'auto');

        try {
            const response = await fetch(`${AppState.API_BASE}/upload`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Upload failed:', error);
            throw error;
        }
    },

    async uploadAudio(file, context, analysisType, onProgress) {
        const formData = new FormData();
        formData.append('file', file);
        if (context) {
            formData.append('context', context);
        }
        formData.append('analysis_type', analysisType || 'descriptive');

        try {
            const response = await fetch(`${AppState.API_BASE}/upload-audio`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Audio upload failed:', error);
            throw error;
        }
    },

    async optimizePrompt(context) {
        try {
            const response = await fetch(`${AppState.API_BASE}/optimize-prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ context })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Optimization failed');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Optimize prompt failed:', error);
            throw error;
        }
    },

    async deleteVideo(videoId) {
        try {
            const response = await fetch(`${AppState.API_BASE}/videos/${videoId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error('Delete failed');
            return await response.json();
        } catch (error) {
            console.error('Delete failed:', error);
            throw error;
        }
    },

    getExportPdfUrl(videoId) {
        return `${AppState.API_BASE}/videos/${videoId}/export/pdf`;
    },

    getExportZipUrl(videoId) {
        return `${AppState.API_BASE}/videos/${videoId}/export/zip`;
    },

    getExportHtmlUrl(videoId) {
        return `${AppState.API_BASE}/videos/${videoId}/export/html`;
    },

    getExportMarkdownUrl(videoId) {
        return `${AppState.API_BASE}/videos/${videoId}/export/markdown`;
    }
};

