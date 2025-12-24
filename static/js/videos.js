// ========================================
// Videos Module
// ========================================

window.Videos = {
    async loadVideos() {
        const videosList = document.getElementById('videosList');
        if (!videosList) return;
        
        // Show skeleton loading
        this.showSkeletonLoading(videosList, 6);
        
        try {
            const data = await Api.getVideos(AppState.currentMediaFilter);
            this.renderVideosList(data.videos);
        } catch (error) {
            videosList.innerHTML = `
                <div class="error-message">
                    <p><i data-lucide="alert-circle"></i> Errore nel caricamento dei media</p>
                    <button onclick="Videos.loadVideos()" class="btn btn-secondary retry-btn">
                        <i data-lucide="refresh-cw"></i> Riprova
                    </button>
                </div>
            `;
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }
    },
    
    renderVideosList(videos) {
        const videosList = document.getElementById('videosList');
        if (!videosList) return;
        
        if (!videos || videos.length === 0) {
            videosList.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon"><i data-lucide="folder-open"></i></span>
                    <p>Nessun media trovato</p>
                    <p class="empty-hint">Carica un video o audio per iniziare</p>
                </div>
            `;
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }
        
        videosList.innerHTML = videos.map(video => {
            const isAudio = video.media_type === 'audio';
            const iconName = isAudio ? 'music' : 'video';
            const statusClass = video.status === 'completed' ? 'status-completed' : 
                               video.status === 'processing' ? 'status-processing' : 
                               video.status === 'failed' ? 'status-failed' : 'status-pending';
            
            // Check for thumbnail from first keyframe
            const thumbnailUrl = video.thumbnail_url || (video.keyframes && video.keyframes[0]?.s3_url);
            const thumbnailHtml = thumbnailUrl 
                ? `<img src="${thumbnailUrl}" alt="${Utils.escapeHtml(video.filename)}" loading="lazy">`
                : `<i data-lucide="${iconName}"></i>`;
            
            // Build tooltip if summary is available
            const tooltipHtml = video.summary 
                ? `<div class="video-tooltip">${Utils.escapeHtml(video.summary.substring(0, 150))}${video.summary.length > 150 ? '...' : ''}</div>`
                : '';
            
            return `
                <div class="video-card" onclick="Videos.showVideoDetail(${video.id})" tabindex="0" role="button">
                    ${tooltipHtml}
                    <div class="video-thumbnail">
                        ${thumbnailHtml}
                        <div class="play-overlay"><i data-lucide="play"></i></div>
                        <span class="video-status-badge ${statusClass}">${video.status}</span>
                        <span class="media-type-indicator ${video.media_type || 'video'}">${isAudio ? 'AUDIO' : 'VIDEO'}</span>
                    </div>
                    <div class="video-info">
                        <h3 class="video-title">${Utils.escapeHtml(video.filename)}</h3>
                        <div class="video-meta">
                            <span><i data-lucide="clock"></i> ${Utils.formatDuration(video.duration)}</span>
                            <span><i data-lucide="calendar"></i> ${Utils.formatDate(video.created_at)}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        // Initialize Lucide icons
        if (typeof lucide !== 'undefined') lucide.createIcons();
    },
    
    async showVideoDetail(videoId) {
        AppState.currentVideoId = videoId;
        
        Navigation.showView('detail');
        
        const detailContent = document.getElementById('detailContent');
        if (detailContent) {
            detailContent.innerHTML = '<div class="loading-container"><span class="loading-spinner"></span> Caricamento dettagli...</div>';
        }
        
        try {
            const data = await Api.getVideoDetail(videoId);
            this.renderVideoDetail(data);
        } catch (error) {
            if (detailContent) {
                detailContent.innerHTML = `
                    <div class="error-message">
                        <p>Errore nel caricamento dei dettagli</p>
                        <button onclick="Videos.showVideoDetail(${videoId})" class="retry-btn">Riprova</button>
                    </div>
                `;
            }
        }
    },
    
    renderVideoDetail(data) {
        const detailContent = document.getElementById('detailContent');
        if (!detailContent) return;
        
        const video = data.video;
        const isAudio = video.media_type === 'audio';
        const analysis = data.analysis || {};
        const iconName = isAudio ? 'music' : 'video';
        
        let html = `
            <div class="detail-header">
                <h2><i data-lucide="${iconName}"></i> ${Utils.escapeHtml(video.filename)}</h2>
                <div class="detail-actions">
                    <button onclick="Export.downloadPDF()" class="btn btn-primary" ${video.status !== 'completed' ? 'disabled' : ''}>
                        <i data-lucide="file-text"></i> PDF
                    </button>
                    <button onclick="Export.downloadZip()" class="btn btn-secondary" ${video.status !== 'completed' ? 'disabled' : ''}>
                        <i data-lucide="package"></i> ZIP
                    </button>
                    <button onclick="Videos.deleteCurrentVideo()" class="btn btn-danger">
                        <i data-lucide="trash-2"></i> Elimina
                    </button>
                </div>
            </div>
            
            <div class="detail-meta">
                <span class="meta-item"><i data-lucide="clock"></i> ${Utils.formatDuration(video.duration)}</span>
                <span class="meta-item"><i data-lucide="calendar"></i> ${Utils.formatDate(video.created_at)}</span>
                <span class="meta-item status-badge status-${video.status}">${video.status}</span>
            </div>
        `;
        
        if (video.status === 'processing') {
            html += `
                <div class="processing-indicator">
                    <span class="loading-spinner"></span>
                    <p>Analisi in corso...</p>
                    <p class="processing-hint">Questa operazione può richiedere alcuni minuti</p>
                </div>
            `;
            this.startPolling(video.id);
        } else if (video.status === 'completed') {
            html += this.renderAnalysis(data, isAudio);
        } else if (video.status === 'failed') {
            html += `
                <div class="error-state">
                    <p>❌ Analisi fallita</p>
                    <p class="error-hint">Si è verificato un errore durante l'elaborazione</p>
                </div>
            `;
        }
        
        detailContent.innerHTML = html;
        
        // Initialize Lucide icons
        if (typeof lucide !== 'undefined') lucide.createIcons();
    },
    
    renderAnalysis(data, isAudio) {
        const analysis = data.analysis || {};
        const transcript = data.transcript || {};
        const keyframes = data.keyframes || [];
        
        let html = '<div class="analysis-tabs">';
        
        // Summary tab
        html += `
            <div class="tab-section">
                <h3><i data-lucide="clipboard-list"></i> Riepilogo</h3>
                <div class="summary-content">
                    <p>${Utils.escapeHtml(analysis.summary || 'Nessun riepilogo disponibile')}</p>
                </div>
        `;
        
        if (analysis.app_type || analysis.audio_type) {
            const typeIcon = isAudio ? 'headphones' : 'smartphone';
            html += `
                <div class="type-badge">
                    <i data-lucide="${typeIcon}"></i> ${Utils.escapeHtml(analysis.app_type || analysis.audio_type || 'N/A')}
                </div>
            `;
        }
        
        html += '</div>';
        
        // Modules section (for video)
        if (!isAudio && analysis.modules && analysis.modules.length > 0) {
            html += `
                <div class="tab-section">
                    <h3><i data-lucide="package"></i> Moduli (${analysis.modules.length})</h3>
                    <div class="modules-list">
                        ${analysis.modules.map(mod => `
                            <div class="module-card">
                                <h4>${Utils.escapeHtml(mod.name || 'Modulo')}</h4>
                                <p>${Utils.escapeHtml(mod.description || '')}</p>
                                ${mod.key_features ? `
                                    <ul class="features-list">
                                        ${mod.key_features.map(f => `<li>${Utils.escapeHtml(f)}</li>`).join('')}
                                    </ul>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Audio-specific sections
        if (isAudio) {
            html += this.renderAudioSpecificData(data);
        }
        
        // Transcript section
        if (transcript.full_text) {
            html += `
                <div class="tab-section">
                    <h3><i data-lucide="file-text"></i> Trascrizione</h3>
                    <div class="transcript-content">
                        <pre>${Utils.escapeHtml(transcript.full_text)}</pre>
                    </div>
                </div>
            `;
        }
        
        // Keyframes section (for video) - with lightbox support
        if (!isAudio && keyframes && keyframes.length > 0) {
            // Store keyframes for lightbox
            window._currentKeyframes = keyframes.map((kf, idx) => ({
                url: kf.s3_url,
                caption: `Frame #${idx + 1} di ${keyframes.length} — Timestamp: ${Utils.formatDuration(kf.timestamp)}`
            }));
            
            html += `
                <div class="tab-section">
                    <h3><i data-lucide="image"></i> Keyframes (${keyframes.length})</h3>
                    <div class="keyframes-grid">
                        ${keyframes.map((kf, idx) => `
                            <div class="keyframe-card" data-frame="#${idx + 1}" onclick="Lightbox.open(${idx}, window._currentKeyframes)" tabindex="0" role="button">
                                <img src="${kf.s3_url}" alt="Frame ${idx + 1}" loading="lazy" onerror="this.parentElement.classList.add('error'); this.style.display='none';">
                                <div class="keyframe-info">
                                    <span class="timestamp">${Utils.formatDuration(kf.timestamp)}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Issues section
        if (analysis.issues_and_observations && analysis.issues_and_observations.length > 0) {
            html += `
                <div class="tab-section">
                    <h3><i data-lucide="alert-triangle"></i> Osservazioni (${analysis.issues_and_observations.length})</h3>
                    <div class="issues-list">
                        ${analysis.issues_and_observations.map(issue => `
                            <div class="issue-card severity-${issue.severity || 'medium'}">
                                <span class="issue-type">${Utils.escapeHtml(issue.type || 'Osservazione')}</span>
                                <p>${Utils.escapeHtml(issue.description || '')}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Recommendations section
        if (analysis.recommendations && analysis.recommendations.length > 0) {
            html += `
                <div class="tab-section">
                    <h3><i data-lucide="lightbulb"></i> Raccomandazioni (${analysis.recommendations.length})</h3>
                    <div class="recommendations-list">
                        ${analysis.recommendations.map(rec => {
                            const recText = typeof rec === 'string' ? rec : (rec.description || JSON.stringify(rec));
                            return `<div class="recommendation-card"><p>${Utils.escapeHtml(recText)}</p></div>`;
                        }).join('')}
                    </div>
                </div>
            `;
        }
        
        return html;
    },
    
    renderAudioSpecificData(data) {
        const analysis = data.analysis || {};
        const audioAnalysis = data.audio_analysis || {};
        let html = '';
        
        // Speakers section
        const speakers = analysis.speakers || audioAnalysis.speakers || [];
        if (speakers.length > 0) {
            html += `
                <div class="tab-section">
                    <h3><i data-lucide="users"></i> Parlanti (${speakers.length})</h3>
                    <div class="speakers-list">
                        ${speakers.map(speaker => `
                            <div class="speaker-card">
                                <h4><i data-lucide="user"></i> ${Utils.escapeHtml(speaker.inferred_name || speaker.id || 'Parlante')}</h4>
                                ${speaker.role ? `<span class="speaker-role">${Utils.escapeHtml(speaker.role)}</span>` : ''}
                                ${speaker.characteristics ? `<p>${Utils.escapeHtml(speaker.characteristics)}</p>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Action items section
        const actionItems = analysis.action_items || audioAnalysis.action_items || [];
        if (actionItems.length > 0) {
            html += `
                <div class="tab-section">
                    <h3><i data-lucide="check-square"></i> Action Items (${actionItems.length})</h3>
                    <div class="action-items-list">
                        ${actionItems.map(item => `
                            <div class="action-item-card priority-${item.priority || 'medium'}">
                                <span class="action-priority">${item.priority || 'medium'}</span>
                                <p>${Utils.escapeHtml(item.item || '')}</p>
                                ${item.assignee ? `<span class="assignee"><i data-lucide="user"></i> ${Utils.escapeHtml(item.assignee)}</span>` : ''}
                                ${item.deadline ? `<span class="deadline"><i data-lucide="calendar"></i> ${Utils.escapeHtml(item.deadline)}</span>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Decisions section
        const decisions = analysis.decisions || audioAnalysis.decisions || [];
        if (decisions.length > 0) {
            html += `
                <div class="tab-section">
                    <h3><i data-lucide="target"></i> Decisioni (${decisions.length})</h3>
                    <div class="decisions-list">
                        ${decisions.map(decision => `
                            <div class="decision-card">
                                <p>${Utils.escapeHtml(decision.decision || '')}</p>
                                ${decision.made_by ? `<span class="decision-by"><i data-lucide="user"></i> ${Utils.escapeHtml(decision.made_by)}</span>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Topics section
        const topics = analysis.topics || audioAnalysis.topics || [];
        if (topics.length > 0) {
            html += `
                <div class="tab-section">
                    <h3><i data-lucide="bookmark"></i> Argomenti (${topics.length})</h3>
                    <div class="topics-list">
                        ${topics.map(topic => `
                            <div class="topic-card">
                                <h4>${Utils.escapeHtml(topic.name || topic.topic || 'Argomento')}</h4>
                                ${topic.summary ? `<p>${Utils.escapeHtml(topic.summary)}</p>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        return html;
    },
    
    startPolling(videoId) {
        // Clear existing interval
        if (AppState.pollingInterval) {
            clearInterval(AppState.pollingInterval);
        }
        
        AppState.pollingInterval = setInterval(async () => {
            try {
                const data = await Api.getVideoDetail(videoId);
                
                if (data.video.status === 'completed' || data.video.status === 'failed') {
                    clearInterval(AppState.pollingInterval);
                    AppState.pollingInterval = null;
                    this.renderVideoDetail(data);
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 3000); // Poll every 3 seconds
    },
    
    async deleteCurrentVideo() {
        if (!AppState.currentVideoId) return;
        
        if (!confirm('Sei sicuro di voler eliminare questo media e tutti i dati associati?')) {
            return;
        }
        
        try {
            await Api.deleteVideo(AppState.currentVideoId);
            Toast.success('Media eliminato con successo');
            Navigation.showView('videos');
            this.loadVideos();
        } catch (error) {
            Toast.error('Errore durante l\'eliminazione: ' + error.message);
        }
    },
    
    // Show skeleton loading state
    showSkeletonLoading(container, count = 6) {
        if (!container) return;
        
        const skeletons = Array(count).fill(0).map(() => `
            <div class="video-card skeleton-card">
                <div class="video-thumbnail skeleton skeleton-thumbnail"></div>
                <div class="video-info">
                    <div class="skeleton skeleton-text medium"></div>
                    <div class="skeleton skeleton-text short"></div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = skeletons;
    }
};

// Expose global functions for HTML onclick handlers  
window.loadVideos = () => Videos.loadVideos();
window.filterMedia = (filter) => {
    AppState.currentMediaFilter = filter;
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === filter);
    });
    Videos.loadVideos();
};

