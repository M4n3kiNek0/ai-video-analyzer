// ========================================
// API Communication Module
// ========================================

window.Api = {
    async checkHealth() {
        try {
            const healthUrl = `${AppState.API_BASE}/health`;
            console.log('Health check URL:', healthUrl);
            const response = await fetch(healthUrl);
            const result = response.ok;
            console.log('Health check result:', result, response.status);
            return result;
        } catch (error) {
            console.error('Health check failed:', error);
            console.error('API_BASE is:', AppState.API_BASE);
            return false;
        }
    },

    async getVideos(filter = 'all') {
        try {
            console.log(`Fetching videos from ${AppState.API_BASE}/videos with filter: ${filter}`);
            
            // Suppress extension-related errors by wrapping in try-catch
            let response;
            try {
                // Create AbortController for timeout
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
                
                try {
                    response = await fetch(`${AppState.API_BASE}/videos`, {
                        signal: controller.signal,
                        // Add credentials to avoid CORS issues
                        credentials: 'same-origin'
                    }).catch(err => {
                        // Catch and rethrow fetch errors, but ignore extension errors
                        if (err.message && err.message.includes('message channel closed')) {
                            // This is a browser extension error, ignore it and retry
                            console.warn('Browser extension interference detected, retrying...');
                            // Retry without signal to avoid double abort
                            return fetch(`${AppState.API_BASE}/videos`, {
                                credentials: 'same-origin'
                            });
                        }
                        throw err;
                    });
                    
                    clearTimeout(timeoutId);
                } catch (fetchError) {
                    clearTimeout(timeoutId);
                    // Ignore extension-related errors and retry
                    if (fetchError.name === 'AbortError') {
                        throw new Error('Timeout: la richiesta ha impiegato troppo tempo');
                    }
                    if (fetchError.message && fetchError.message.includes('message channel closed')) {
                        console.warn('Extension error on first attempt, retrying...');
                        // Retry once without timeout
                        response = await fetch(`${AppState.API_BASE}/videos`, {
                            credentials: 'same-origin'
                        });
                    } else {
                        throw new Error(`Errore di connessione: ${fetchError.message}`);
                    }
                }
            } catch (networkError) {
                // Final catch for any network errors
                if (networkError.message && networkError.message.includes('message channel closed')) {
                    console.warn('Extension interference, attempting direct fetch...');
                    // Last resort: direct fetch
                    response = await fetch(`${AppState.API_BASE}/videos`, {
                        credentials: 'same-origin'
                    });
                } else {
                    throw networkError;
                }
            }
            
            if (!response || !response.ok) {
                let errorText = '';
                try {
                    errorText = response ? await response.text() : 'No response received';
                } catch (e) {
                    errorText = response ? response.statusText : 'Network error';
                }
                console.error(`API error ${response?.status || 'unknown'}:`, errorText);
                throw new Error(`Errore server ${response?.status || 'unknown'}: ${errorText || response?.statusText || 'No response'}`);
            }
            
            const data = await response.json();
            console.log('Raw API response:', data);
            
            // Handle different response formats
            // Backend might return { videos: [...] } or { items: [...] } or just [...]
            let videos = [];
            if (data.videos && Array.isArray(data.videos)) {
                videos = data.videos;
            } else if (data.items && Array.isArray(data.items)) {
                videos = data.items;
            } else if (Array.isArray(data)) {
                videos = data;
            } else {
                console.warn('Unexpected API response format:', data);
                videos = [];
            }
            
            // Filter by media type if needed
            if (filter === 'video') {
                videos = videos.filter(v => v.media_type === 'video' || !v.media_type);
            } else if (filter === 'audio') {
                videos = videos.filter(v => v.media_type === 'audio');
            }
            
            console.log(`Processed ${videos.length} videos after filtering`);
            
            // Return in consistent format
            return { videos };
        } catch (error) {
            console.error('Failed to fetch videos:', error);
            const errorMsg = String(error?.message || error || '').toLowerCase();
            
            // Don't throw extension errors, but log them
            if (errorMsg.includes('message channel closed') || 
                errorMsg.includes('asynchronous response') ||
                errorMsg.includes('listener indicated')) {
                console.warn('Browser extension error detected. The API call may have succeeded despite this error.');
                // Try one more direct fetch without any wrapper
                try {
                    const directResponse = await fetch(`${AppState.API_BASE}/videos`, {
                        credentials: 'same-origin'
                    });
                    if (directResponse.ok) {
                        const directData = await directResponse.json();
                        let videos = directData?.videos || directData?.items || (Array.isArray(directData) ? directData : []);
                        if (filter === 'video') {
                            videos = videos.filter(v => v.media_type === 'video' || !v.media_type);
                        } else if (filter === 'audio') {
                            videos = videos.filter(v => v.media_type === 'audio');
                        }
                        return { videos };
                    }
                } catch (retryError) {
                    console.warn('Retry also failed:', retryError);
                }
                // Return empty array if all retries fail
                return { videos: [] };
            }
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

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    const loaded = e.loaded;
                    const total = e.total;
                    const speed = e.loaded / ((Date.now() - (xhr._startTime || Date.now())) / 1000); // bytes per second
                    xhr._startTime = xhr._startTime || Date.now();
                    
                    onProgress({
                        loaded,
                        total,
                        percent: percentComplete,
                        speed: speed || 0,
                        timeRemaining: total > loaded && speed > 0 ? (total - loaded) / speed : 0
                    });
                }
            });
            
            xhr.addEventListener('loadstart', () => {
                xhr._startTime = Date.now();
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (e) {
                        reject(new Error('Invalid response from server'));
                    }
                } else {
                    try {
                        const error = JSON.parse(xhr.responseText);
                        reject(new Error(error.detail || `Upload failed with status ${xhr.status}`));
                    } catch (e) {
                        reject(new Error(`Upload failed with status ${xhr.status}`));
                    }
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('Network error during upload'));
            });
            
            xhr.addEventListener('abort', () => {
                reject(new Error('Upload aborted'));
            });
            
            xhr.open('POST', `${AppState.API_BASE}/upload`);
            xhr.send(formData);
        });
    },

    async uploadAudio(file, context, analysisType, onProgress) {
        const formData = new FormData();
        formData.append('file', file);
        if (context) {
            formData.append('context', context);
        }
        formData.append('analysis_type', analysisType || 'descriptive');

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    const loaded = e.loaded;
                    const total = e.total;
                    const speed = e.loaded / ((Date.now() - (xhr._startTime || Date.now())) / 1000); // bytes per second
                    xhr._startTime = xhr._startTime || Date.now();
                    
                    onProgress({
                        loaded,
                        total,
                        percent: percentComplete,
                        speed: speed || 0,
                        timeRemaining: total > loaded && speed > 0 ? (total - loaded) / speed : 0
                    });
                }
            });
            
            xhr.addEventListener('loadstart', () => {
                xhr._startTime = Date.now();
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (e) {
                        reject(new Error('Invalid response from server'));
                    }
                } else {
                    try {
                        const error = JSON.parse(xhr.responseText);
                        reject(new Error(error.detail || `Upload failed with status ${xhr.status}`));
                    } catch (e) {
                        reject(new Error(`Upload failed with status ${xhr.status}`));
                    }
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('Network error during upload'));
            });
            
            xhr.addEventListener('abort', () => {
                reject(new Error('Upload aborted'));
            });
            
            xhr.open('POST', `${AppState.API_BASE}/upload-audio`);
            xhr.send(formData);
        });
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

