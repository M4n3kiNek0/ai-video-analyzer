// ========================================
// Terminal Log Module
// ========================================

window.TerminalLog = {
    /**
     * Add a log entry to the terminal
     * @param {string} message - The message to log
     * @param {string} type - Type: 'info', 'success', 'warning', 'error', 'step', 'system'
     */
    log(message, type = 'info') {
        const body = document.getElementById('terminalBody');
        if (!body) return;
        
        const timestamp = new Date().toLocaleTimeString('it-IT', { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
        
        // Remove 'active' class from previous entries
        body.querySelectorAll('.log-entry.active').forEach(el => {
            el.classList.remove('active');
        });
        
        const entry = document.createElement('div');
        entry.className = `log-entry ${type} active`;
        entry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${this._escapeHtml(message)}`;
        
        body.appendChild(entry);
        
        // Auto-scroll to bottom
        body.scrollTop = body.scrollHeight;
    },
    
    /**
     * Log an info message
     */
    info(message) {
        this.log(message, 'info');
    },
    
    /**
     * Log a success message
     */
    success(message) {
        this.log(message, 'success');
    },
    
    /**
     * Log a warning message
     */
    warning(message) {
        this.log(message, 'warning');
    },
    
    /**
     * Log an error message
     */
    error(message) {
        this.log(message, 'error');
    },
    
    /**
     * Log a step/progress message
     */
    step(message) {
        this.log(message, 'step');
    },
    
    /**
     * Log a system message
     */
    system(message) {
        this.log(message, 'system');
    },
    
    /**
     * Clear all log entries
     */
    clear() {
        const body = document.getElementById('terminalBody');
        if (body) {
            body.innerHTML = '';
            this.system('Log cleared.');
        }
    },
    
    /**
     * Initialize terminal with a welcome message
     */
    init() {
        const body = document.getElementById('terminalBody');
        if (body) {
            body.innerHTML = '';
            this.system('Terminal initialized. Ready for processing...');
        }
    },
    
    /**
     * Escape HTML to prevent XSS
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// ========================================
// Upload Module
// ========================================

window.Upload = {
    init() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        
        if (!dropZone || !fileInput) return;
        
        // Click to select file
        dropZone.addEventListener('click', (e) => {
            // Don't trigger if clicking on buttons or labels inside
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'LABEL' || 
                e.target.tagName === 'INPUT' ||
                e.target.closest('button') || e.target.closest('label')) {
                return;
            }
            fileInput.click();
        });
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.showFileSelected(e.target.files[0]);
            }
        });
        
        // Mouse tracking for glow effect
        dropZone.addEventListener('mousemove', (e) => {
            const rect = dropZone.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            dropZone.style.setProperty('--mouse-x', `${x}%`);
            dropZone.style.setProperty('--mouse-y', `${y}%`);
        });
        
        // Drag and drop events
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.showFileSelected(files[0]);
            }
        });
        
        // Optimize prompt button (ID: optimizePromptBtn in HTML)
        const optimizeBtn = document.getElementById('optimizePromptBtn');
        if (optimizeBtn) {
            optimizeBtn.addEventListener('click', () => this.optimizePrompt());
        }
        
        // Context textarea validation (ID: videoContext in HTML)
        const contextInput = document.getElementById('videoContext');
        if (contextInput) {
            contextInput.addEventListener('input', () => this.validateContext());
        }
        
        // Modal buttons
        const useOriginalBtn = document.getElementById('useOriginalBtn');
        const useOptimizedBtn = document.getElementById('useOptimizedBtn');
        
        if (useOriginalBtn) {
            useOriginalBtn.addEventListener('click', () => this.useOriginalContext());
        }
        if (useOptimizedBtn) {
            useOptimizedBtn.addEventListener('click', () => this.useOptimizedContext());
        }
        
        // Initialize analysis type cards
        this.initAnalysisTypeCards();
    },
    
    initAnalysisTypeCards() {
        const cardsContainer = document.getElementById('analysisTypeCards');
        const hiddenSelect = document.getElementById('analysisType');
        
        if (!cardsContainer) return;
        
        // Add click handlers to all cards
        cardsContainer.querySelectorAll('.analysis-type-card').forEach(card => {
            card.addEventListener('click', () => {
                // Remove active from all cards
                cardsContainer.querySelectorAll('.analysis-type-card').forEach(c => {
                    c.classList.remove('active');
                });
                
                // Add active to clicked card
                card.classList.add('active');
                
                // Update hidden select
                const type = card.dataset.type;
                if (hiddenSelect) {
                    hiddenSelect.value = type;
                }
                
                // Check the radio button
                const radio = card.querySelector('input[type="radio"]');
                if (radio) {
                    radio.checked = true;
                }
                
                // Store in AppState
                AppState.selectedAnalysisType = type;
            });
        });
        
        // Set default
        AppState.selectedAnalysisType = 'auto';
    },
    
    updateAnalysisTypeCardsForMedia(mediaType) {
        const cardsContainer = document.getElementById('analysisTypeCards');
        if (!cardsContainer) return;
        
        // Define which types are suitable for each media type
        const videoTypes = ['auto', 'reverse_engineering', 'notes'];
        const audioTypes = ['auto', 'meeting', 'debrief', 'brainstorming', 'notes'];
        const allTypes = ['auto', 'reverse_engineering', 'meeting', 'debrief', 'brainstorming', 'notes'];
        
        cardsContainer.querySelectorAll('.analysis-type-card').forEach(card => {
            const type = card.dataset.type;
            
            if (mediaType === 'video') {
                // For video: show reverse_engineering prominently, hide meeting/debrief/brainstorming
                if (videoTypes.includes(type)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'flex'; // Show all but dim non-recommended
                    card.style.opacity = '0.5';
                }
            } else {
                // For audio: show all meeting-related, dim reverse_engineering
                if (audioTypes.includes(type)) {
                    card.style.display = 'flex';
                    card.style.opacity = '1';
                } else {
                    card.style.display = 'flex';
                    card.style.opacity = '0.5';
                }
            }
        });
        
        // Reset to auto if current selection is not suitable
        const currentType = this.getSelectedAnalysisType();
        const suitableTypes = mediaType === 'video' ? videoTypes : audioTypes;
        
        if (!suitableTypes.includes(currentType)) {
            // Select auto
            const autoCard = cardsContainer.querySelector('[data-type="auto"]');
            if (autoCard) {
                cardsContainer.querySelectorAll('.analysis-type-card').forEach(c => c.classList.remove('active'));
                autoCard.classList.add('active');
                const radio = autoCard.querySelector('input[type="radio"]');
                if (radio) radio.checked = true;
                AppState.selectedAnalysisType = 'auto';
            }
        }
    },
    
    getSelectedAnalysisType() {
        // First check AppState
        if (AppState.selectedAnalysisType) {
            return AppState.selectedAnalysisType;
        }
        
        // Then check the hidden select
        const hiddenSelect = document.getElementById('analysisType');
        if (hiddenSelect) {
            return hiddenSelect.value;
        }
        
        // Then check the active card
        const activeCard = document.querySelector('.analysis-type-card.active');
        if (activeCard) {
            return activeCard.dataset.type;
        }
        
        return 'auto';
    },
    
    showFileSelected(file) {
        AppState.selectedFile = file;
        
        // Detect media type from file extension
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (AppState.VIDEO_FORMATS.includes(ext)) {
            AppState.currentMediaType = 'video';
        } else if (AppState.AUDIO_FORMATS.includes(ext)) {
            AppState.currentMediaType = 'audio';
        } else {
            Toast.error('Formato file non supportato');
            return;
        }
        
        // Update the drop zone to show selected file
        const dropZone = document.getElementById('dropZone');
        const iconName = AppState.currentMediaType === 'audio' ? 'music' : 'video';
        
        dropZone.innerHTML = `
            <div class="file-selected">
                <div class="upload-icon"><i data-lucide="${iconName}"></i></div>
                <h3>${Utils.escapeHtml(file.name)}</h3>
                <p>${Utils.formatFileSize(file.size)}</p>
                <span class="file-type-badge">${AppState.currentMediaType.toUpperCase()}</span>
                <button class="btn btn-primary" id="startAnalysisBtn">
                    <i data-lucide="rocket"></i> Avvia Analisi
                </button>
                <button class="btn btn-ghost" id="changeFileBtn">
                    <i data-lucide="x"></i> Cambia file
                </button>
            </div>
        `;
        
        // Re-initialize Lucide icons
        if (typeof lucide !== 'undefined') lucide.createIcons();
        
        // Add event listeners to new buttons
        document.getElementById('startAnalysisBtn')?.addEventListener('click', () => this.startAnalysis());
        document.getElementById('changeFileBtn')?.addEventListener('click', () => this.resetFileSelection());
        
        // Update toggle buttons
        document.querySelectorAll('.toggle-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.type === AppState.currentMediaType);
        });
        
        // Show analysis type section for all media types
        const analysisTypeSection = document.getElementById('analysisTypeSection');
        if (analysisTypeSection) {
            analysisTypeSection.style.display = 'block';
        }
        
        // Update card visibility based on media type
        this.updateAnalysisTypeCardsForMedia(AppState.currentMediaType);
        
        this.validateContext();
    },
    
    resetFileSelection() {
        AppState.selectedFile = null;
        AppState.originalContext = '';
        AppState.optimizedContext = '';
        
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const iconName = AppState.currentMediaType === 'audio' ? 'music' : 'video';
        const title = AppState.currentMediaType === 'audio' ? 'Trascina qui il tuo audio' : 'Trascina qui il tuo video';
        const formats = AppState.currentMediaType === 'audio' ? AppState.AUDIO_FORMATS : AppState.VIDEO_FORMATS;
        const hint = AppState.currentMediaType === 'audio' 
            ? 'Formati supportati: MP3, WAV, M4A, OGG, FLAC, AAC' 
            : 'Formati supportati: MP4, MOV, AVI, MKV, WEBM';
        
        // Restore original dropzone HTML
        if (dropZone) {
            dropZone.innerHTML = `
                <div class="upload-icon" id="uploadIcon"><i data-lucide="${iconName}"></i></div>
                <h3 id="uploadTitle">${title}</h3>
                <p>oppure</p>
                <label class="btn btn-primary" onclick="event.stopPropagation()">
                    <input type="file" id="fileInput" accept="${formats.join(',')}" hidden>
                    <i data-lucide="upload"></i>
                    Seleziona File
                </label>
                <p class="upload-hint" id="uploadHint">${hint}</p>
            `;
            
            // Re-initialize Lucide icons
            if (typeof lucide !== 'undefined') lucide.createIcons();
            
            // Re-attach file input listener
            const newFileInput = document.getElementById('fileInput');
            if (newFileInput) {
                newFileInput.addEventListener('change', (e) => {
                    if (e.target.files.length > 0) {
                        this.showFileSelected(e.target.files[0]);
                    }
                });
            }
        }
        
        // Close optimize modal if open
        const optimizedModal = document.getElementById('optimizedPromptModal');
        if (optimizedModal) optimizedModal.style.display = 'none';
    },
    
    validateContext() {
        const contextInput = document.getElementById('videoContext');
        const charCount = document.getElementById('charCount');
        const startAnalysisBtn = document.getElementById('startAnalysisBtn');
        const optimizeBtn = document.getElementById('optimizePromptBtn');
        
        if (!contextInput) return false;
        
        const length = contextInput.value.trim().length;
        const isValid = length >= AppState.MIN_CONTEXT_CHARS;
        
        if (charCount) {
            charCount.textContent = `${length} / ${AppState.MIN_CONTEXT_CHARS} caratteri minimi`;
            charCount.classList.toggle('valid', isValid);
            charCount.classList.toggle('invalid', !isValid && length > 0);
        }
        
        // Update textarea visual state
        contextInput.classList.toggle('valid', isValid);
        contextInput.classList.toggle('invalid', !isValid && length > 0);
        
        if (startAnalysisBtn) {
            startAnalysisBtn.disabled = !isValid || !AppState.selectedFile;
        }
        
        if (optimizeBtn) {
            optimizeBtn.disabled = !isValid;
        }
        
        return isValid;
    },
    
    async optimizePrompt() {
        const contextInput = document.getElementById('videoContext');
        const optimizeBtn = document.getElementById('optimizePromptBtn');
        const modal = document.getElementById('optimizedPromptModal');
        const originalPreview = document.getElementById('originalPromptPreview');
        const optimizedPreview = document.getElementById('optimizedPromptPreview');
        const improvementsList = document.getElementById('improvementsList');
        
        if (!contextInput || !this.validateContext()) return;
        
        AppState.originalContext = contextInput.value.trim();
        
        // Show loading state
        if (optimizeBtn) {
            optimizeBtn.disabled = true;
            optimizeBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Ottimizzazione...';
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }
        
        try {
            const result = await Api.optimizePrompt(AppState.originalContext);
            
            AppState.optimizedContext = result.optimized_context;
            
            // Show modal with comparison
            if (originalPreview) {
                originalPreview.textContent = AppState.originalContext;
            }
            if (optimizedPreview) {
                optimizedPreview.value = result.optimized_context;
            }
            
            // Show improvements
            if (improvementsList && result.improvements && result.improvements.length > 0) {
                improvementsList.innerHTML = `
                    <h4>Miglioramenti applicati:</h4>
                    <ul>
                        ${result.improvements.map(imp => `<li>${Utils.escapeHtml(imp)}</li>`).join('')}
                    </ul>
                `;
            } else if (improvementsList) {
                improvementsList.innerHTML = '';
            }
            
            // Show modal
            if (modal) {
                modal.style.display = 'flex';
            }
            
        } catch (error) {
            Toast.error('Errore durante l\'ottimizzazione: ' + error.message);
        } finally {
            if (optimizeBtn) {
                optimizeBtn.disabled = false;
                optimizeBtn.innerHTML = '<i data-lucide="sparkles"></i> Ottimizza con AI';
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
        }
    },
    
    useOriginalContext() {
        const contextInput = document.getElementById('videoContext');
        const modal = document.getElementById('optimizedPromptModal');
        
        if (contextInput && AppState.originalContext) {
            contextInput.value = AppState.originalContext;
        }
        if (modal) {
            modal.style.display = 'none';
        }
        
        AppState.optimizedContext = '';
        this.validateContext();
    },
    
    useOptimizedContext() {
        const contextInput = document.getElementById('videoContext');
        const modal = document.getElementById('optimizedPromptModal');
        const optimizedPreview = document.getElementById('optimizedPromptPreview');
        
        // Use the (possibly edited) value from the preview textarea
        const optimizedValue = optimizedPreview ? optimizedPreview.value : AppState.optimizedContext;
        
        if (contextInput && optimizedValue) {
            contextInput.value = optimizedValue;
        }
        if (modal) {
            modal.style.display = 'none';
        }
        
        this.validateContext();
    },
    
    async startAnalysis() {
        if (!AppState.selectedFile) {
            Toast.warning('Seleziona un file prima di procedere');
            return;
        }
        
        if (!this.validateContext()) {
            Toast.warning(`Inserisci una descrizione di almeno ${AppState.MIN_CONTEXT_CHARS} caratteri`);
            const contextInput = document.getElementById('videoContext');
            if (contextInput) contextInput.focus();
            return;
        }
        
        const contextInput = document.getElementById('videoContext');
        const context = contextInput ? contextInput.value.trim() : '';
        const startBtn = document.getElementById('startAnalysisBtn');
        const dropZone = document.getElementById('dropZone');
        const contextSection = document.getElementById('contextSection');
        const mediaTypeToggle = document.getElementById('mediaTypeToggle');
        const analysisTypeSection = document.getElementById('analysisTypeSection');
        const uploadProgress = document.getElementById('uploadProgress');
        const processingContainer = document.getElementById('processingContainer');
        
        // Show loading state on button
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Caricamento...';
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }
        
        // Initialize terminal log
        TerminalLog.init();
        TerminalLog.info(`Uploading ${AppState.selectedFile.name} (${Utils.formatFileSize(AppState.selectedFile.size)})...`);
        
        try {
            let result;
            
            // Get selected analysis type (works for both video and audio)
            const analysisType = this.getSelectedAnalysisType();
            TerminalLog.system(`Analysis type: ${analysisType}`);
            TerminalLog.system(`Media type: ${AppState.currentMediaType}`);
            
            if (AppState.currentMediaType === 'audio') {
                result = await Api.uploadAudio(AppState.selectedFile, context, analysisType);
                AppState.currentVideoId = result.audio_id;
            } else {
                result = await Api.uploadVideo(AppState.selectedFile, context, analysisType);
                AppState.currentVideoId = result.video_id;
            }
            
            TerminalLog.success('Upload complete! Starting analysis...');
            TerminalLog.info(`Media ID: ${AppState.currentVideoId}`);
            
            // Hide upload elements
            if (dropZone) dropZone.style.display = 'none';
            if (contextSection) contextSection.style.display = 'none';
            if (mediaTypeToggle) mediaTypeToggle.style.display = 'none';
            if (analysisTypeSection) analysisTypeSection.style.display = 'none';
            
            // Show processing container (split view with terminal)
            if (processingContainer) {
                processingContainer.style.display = 'grid';
                
                // Show correct processing steps based on media type
                const videoSteps = document.getElementById('videoProcessingSteps');
                const audioSteps = document.getElementById('audioProcessingSteps');
                const processingTitle = document.getElementById('processingTitle');
                
                if (AppState.currentMediaType === 'audio') {
                    if (videoSteps) videoSteps.style.display = 'none';
                    if (audioSteps) audioSteps.style.display = 'block';
                    if (processingTitle) processingTitle.textContent = 'Analisi audio in corso...';
                } else {
                    if (videoSteps) videoSteps.style.display = 'block';
                    if (audioSteps) audioSteps.style.display = 'none';
                    if (processingTitle) processingTitle.textContent = 'Analisi video in corso...';
                }
                
                // Re-init Lucide icons
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
            
            // Start polling for status
            this.startProcessingPolling(AppState.currentVideoId);
            
        } catch (error) {
            TerminalLog.error(`Upload failed: ${error.message}`);
            Toast.error('Errore durante il caricamento: ' + error.message);
            if (startBtn) {
                startBtn.disabled = false;
                startBtn.innerHTML = '<i data-lucide="rocket"></i> Avvia Analisi';
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
        }
    },
    
    startProcessingPolling(mediaId) {
        let stepIndex = 0;
        const startTime = Date.now();
        const MAX_POLLING_TIME = 30 * 60 * 1000; // 30 minutes max
        
        // Different steps for video vs audio
        const videoSteps = ['step1', 'step2', 'step3', 'step4', 'step5'];
        const audioSteps = ['audioStep1', 'audioStep2', 'audioStep3', 'audioStep4'];
        const steps = AppState.currentMediaType === 'audio' ? audioSteps : videoSteps;
        
        // Step messages for terminal log
        const videoStepMessages = [
            'Extracting audio track from video...',
            'Transcribing audio with Whisper API...',
            'Extracting keyframes from video...',
            'Analyzing frames with GPT-4 Vision...',
            'Generating final analysis report...'
        ];
        const audioStepMessages = [
            'Preparing audio for processing...',
            'Transcribing audio with Whisper API...',
            'Enriching transcription with semantic analysis...',
            'Generating structured report...'
        ];
        const stepMessages = AppState.currentMediaType === 'audio' ? audioStepMessages : videoStepMessages;
        
        // Store reference to this for use in callbacks
        const self = this;
        
        TerminalLog.step('Processing started...');
        
        // Animate steps (visual feedback only, not tied to actual progress)
        const stepInterval = setInterval(() => {
            if (stepIndex < steps.length) {
                const step = document.getElementById(steps[stepIndex]);
                if (step) {
                    step.classList.add('active');
                    
                    // Log step message to terminal
                    TerminalLog.step(`[Step ${stepIndex + 1}/${steps.length}] ${stepMessages[stepIndex]}`);
                    
                    if (stepIndex > 0) {
                        const prevStep = document.getElementById(steps[stepIndex - 1]);
                        if (prevStep) {
                            prevStep.classList.remove('active');
                            prevStep.classList.add('completed');
                            // Update icon to check
                            const status = prevStep.querySelector('.step-status');
                            if (status) {
                                status.innerHTML = '<i data-lucide="check"></i>';
                                if (typeof lucide !== 'undefined') lucide.createIcons();
                            }
                            TerminalLog.success(`Step ${stepIndex} completed.`);
                        }
                    }
                }
                stepIndex++;
            } else {
                // Animation complete - clear this interval
                clearInterval(stepInterval);
            }
        }, 3000);
        
        // Poll API for actual status
        AppState.pollingInterval = setInterval(async () => {
            try {
                // Check for timeout
                const elapsedTime = Date.now() - startTime;
                const elapsedMinutes = Math.floor(elapsedTime / 60000);
                const elapsedSeconds = Math.floor((elapsedTime % 60000) / 1000);
                
                if (elapsedTime > MAX_POLLING_TIME) {
                    console.error('Polling timeout reached after', Math.round(elapsedTime / 60000), 'minutes');
                    TerminalLog.error(`Timeout reached after ${elapsedMinutes}m ${elapsedSeconds}s`);
                    TerminalLog.warning('Processing is taking too long. Check Media Library for status.');
                    clearInterval(AppState.pollingInterval);
                    AppState.pollingInterval = null;
                    if (typeof Toast !== 'undefined' && Toast.error) {
                        Toast.error('Timeout: l\'elaborazione sta richiedendo troppo tempo. Controlla la Media Library per lo stato.');
                    }
                    // Navigate to library so user can check status
                    setTimeout(() => {
                        Navigation.showView('videos');
                        if (typeof Videos !== 'undefined') Videos.loadVideos();
                    }, 2000);
                    return;
                }
                
                const response = await fetch(`${AppState.API_BASE}/videos/${mediaId}`);
                
                // Check if response is ok
                if (!response.ok) {
                    console.error('Polling response error:', response.status, response.statusText);
                    TerminalLog.warning(`API response error: ${response.status}`);
                    return;
                }
                
                const data = await response.json();
                
                // Validate response structure
                if (!data || !data.video) {
                    console.error('Invalid response structure:', data);
                    return;
                }
                
                const status = data.video.status;
                console.log('Polling status:', status, '- elapsed:', Math.round(elapsedTime / 1000), 's');
                
                // Log periodic status updates
                if (elapsedTime % 15000 < 5000) { // Every ~15 seconds
                    TerminalLog.system(`Status: ${status} (${elapsedMinutes}m ${elapsedSeconds}s elapsed)`);
                }
                
                if (status === 'completed') {
                    console.log('=== PROCESSING COMPLETED ===');
                    
                    // Log success to terminal
                    TerminalLog.success('========================================');
                    TerminalLog.success('ANALYSIS COMPLETED SUCCESSFULLY!');
                    TerminalLog.success('========================================');
                    TerminalLog.info(`Total time: ${elapsedMinutes}m ${elapsedSeconds}s`);
                    TerminalLog.info('Redirecting to results...');
                    
                    // Clear intervals first
                    clearInterval(AppState.pollingInterval);
                    AppState.pollingInterval = null;
                    clearInterval(stepInterval);
                    console.log('Intervals cleared');
                    
                    // Mark all steps as completed
                    steps.forEach(stepId => {
                        const step = document.getElementById(stepId);
                        if (step) {
                            step.classList.remove('active');
                            step.classList.add('completed');
                            const statusEl = step.querySelector('.step-status');
                            if (statusEl) {
                                statusEl.innerHTML = '<i data-lucide="check"></i>';
                            }
                        }
                    });
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                    console.log('All steps marked completed');
                    
                    // Show success toast
                    try {
                        if (typeof Toast !== 'undefined' && Toast.success) {
                            Toast.success('Analisi completata!');
                            console.log('Toast shown');
                        }
                    } catch (toastError) {
                        console.error('Toast error:', toastError);
                    }
                    
                    // Navigate to detail view after short delay
                    console.log('Scheduling navigation to detail view for media ID:', mediaId);
                    setTimeout(() => {
                        console.log('Attempting navigation now...');
                        try {
                            if (typeof Videos !== 'undefined' && Videos.showVideoDetail) {
                                console.log('Calling Videos.showVideoDetail');
                                Videos.showVideoDetail(mediaId);
                            } else {
                                console.log('Videos.showVideoDetail not available, falling back to library');
                                Navigation.showView('videos');
                                if (typeof Videos !== 'undefined') Videos.loadVideos();
                            }
                        } catch (navError) {
                            console.error('Navigation error:', navError);
                            // Fallback: reload page
                            console.log('Reloading page as fallback');
                            window.location.reload();
                        }
                    }, 1500);
                    
                } else if (status === 'failed') {
                    // Log failure to terminal
                    TerminalLog.error('========================================');
                    TerminalLog.error('PROCESSING FAILED!');
                    TerminalLog.error('========================================');
                    TerminalLog.error('Check server logs for details.');
                    
                    clearInterval(AppState.pollingInterval);
                    AppState.pollingInterval = null;
                    clearInterval(stepInterval);
                    
                    if (typeof Toast !== 'undefined' && Toast.error) {
                        Toast.error('Elaborazione fallita. Controlla i log del server.');
                    }
                    self.resetUploadView();
                }
            } catch (error) {
                console.error('Polling error:', error);
                TerminalLog.warning(`Polling error: ${error.message}`);
                // Don't stop polling on error - might be temporary network issue
            }
        }, 5000);
    },
    
    resetUploadView() {
        // Reset state
        AppState.selectedFile = null;
        AppState.originalContext = '';
        AppState.optimizedContext = '';
        
        // Show elements
        const dropZone = document.getElementById('dropZone');
        const contextSection = document.getElementById('contextSection');
        const mediaTypeToggle = document.getElementById('mediaTypeToggle');
        const processingContainer = document.getElementById('processingContainer');
        const uploadProgress = document.getElementById('uploadProgress');
        
        if (dropZone) dropZone.style.display = 'block';
        if (contextSection) contextSection.style.display = 'block';
        if (mediaTypeToggle) mediaTypeToggle.style.display = 'flex';
        if (processingContainer) processingContainer.style.display = 'none';
        if (uploadProgress) uploadProgress.style.display = 'none';
        
        // Reset context
        const videoContext = document.getElementById('videoContext');
        if (videoContext) {
            videoContext.value = '';
            videoContext.classList.remove('valid', 'invalid');
        }
        
        // Reset steps
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active', 'completed');
            const status = step.querySelector('.step-status');
            if (status) {
                status.innerHTML = '<i data-lucide="loader-2" class="spin"></i>';
            }
        });
        
        // Reset file selection display
        this.resetFileSelection();
        
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
};

// Expose global functions for HTML onclick handlers
window.resetFileSelection = () => Upload.resetFileSelection();
window.useOriginalContext = () => Upload.useOriginalContext();
window.useOptimizedContext = () => Upload.useOptimizedContext();
window.closeOptimizeModal = () => {
    const modal = document.getElementById('optimizedPromptModal');
    if (modal) modal.style.display = 'none';
};
window.startAnalysis = () => Upload.startAnalysis();

