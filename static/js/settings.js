// ========================================
// Settings Module - API Configuration Management
// Optimized version with dynamic provider cards, real-time validation, and improved UX
// ========================================

// Centralized provider configuration
const PROVIDER_CONFIG = {
    transcription: {
        icon: 'mic',
        label: 'Trascrizione Audio',
        desc: 'Conversione audio in testo',
        options: [
            { provider: 'openai', model: 'whisper-1', label: 'OpenAI Whisper (whisper-1)' },
            { provider: 'local_whisper', model: 'large-v3', label: 'Faster-Whisper Locale (large-v3)' }
        ],
        apiKeyOptional: true
    },
    vision: {
        icon: 'eye',
        label: 'Analisi Visiva',
        desc: 'Analisi frame e screenshot',
        options: [
            { provider: 'openai', model: 'gpt-4o', label: 'OpenAI GPT-4o (gpt-4o)' },
            { provider: 'openai', model: 'gpt-4o-mini', label: 'OpenAI GPT-4o-mini (gpt-4o-mini)' },
            { provider: 'ollama', model: 'llava:13b', label: 'Ollama LLaVA (llava:13b)' },
            { provider: 'together', model: 'meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo', label: 'Together AI Llama Vision' },
            { provider: 'google', model: 'gemini-1.5-flash', label: 'Google Gemini 1.5 Flash' }
        ],
        apiKeyOptional: false
    },
    analysis: {
        icon: 'brain',
        label: 'Analisi Contenuto',
        desc: 'Analisi finale e report strutturato',
        options: [
            { provider: 'openai', model: 'gpt-4o', label: 'OpenAI GPT-4o (gpt-4o)' },
            { provider: 'openai', model: 'gpt-4o-mini', label: 'OpenAI GPT-4o-mini (gpt-4o-mini)' },
            { provider: 'groq', model: 'llama-3.1-70b-versatile', label: 'Groq Llama 3.1 70B' },
            { provider: 'groq', model: 'llama-3.1-8b-instant', label: 'Groq Llama 3.1 8B' },
            { provider: 'ollama', model: 'llama3.1:8b', label: 'Ollama Llama 3.1 8B' },
            { provider: 'together', model: 'meta-llama/Llama-3.1-70B-Instruct-Turbo', label: 'Together AI Llama 3.1 70B' },
            { provider: 'google', model: 'gemini-1.5-flash', label: 'Google Gemini 1.5 Flash' },
            { provider: 'anthropic', model: 'claude-3-haiku-20240307', label: 'Anthropic Claude Haiku' }
        ],
        apiKeyOptional: false
    },
    enrichment: {
        icon: 'zap',
        label: 'Arricchimento',
        desc: 'Arricchimento semantico trascrizione',
        options: [
            { provider: 'openai', model: 'gpt-4o-mini', label: 'OpenAI GPT-4o-mini (gpt-4o-mini)' },
            { provider: 'groq', model: 'llama-3.1-8b-instant', label: 'Groq Llama 3.1 8B' },
            { provider: 'ollama', model: 'llama3.1:8b', label: 'Ollama Llama 3.1 8B' }
        ],
        apiKeyOptional: false
    }
};

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// API Key validation patterns
const API_KEY_PATTERNS = {
    openai: /^sk-[a-zA-Z0-9]{32,}$/,
    groq: /^gsk_[a-zA-Z0-9]{32,}$/,
    anthropic: /^sk-ant-[a-zA-Z0-9_-]{95,}$/,
    together: /^[a-zA-Z0-9]{32,}$/,
    google: /^[a-zA-Z0-9_-]{39,}$/
};

window.Settings = {
    presets: [],
    configs: [],
    activeConfig: null,
    providers: {},
    initialized: false,
    validationStates: {}, // Track validation state for each field
    draftConfig: null, // Store draft configuration
    providersCache: null, // Cache providers data

    async init() {
        // Always reload data when opening settings view
        try {
            await Promise.all([
                this.loadPresets(),
                this.loadConfigs(),
                this.loadProviders(),
                this.loadActiveConfig()
            ]);
            
            // Load draft from localStorage
            this.loadDraft();
            
            this.setupEventListeners();
            this.renderProviderCards(); // Generate provider cards dynamically
            this.renderPresets();
            this.renderActiveConfig();
            this.renderSavedConfigs();
            this.initialized = true;
        } catch (error) {
            console.error('Settings initialization error:', error);
            this.clearLoadingPlaceholders();
            this.showError('Errore nell\'inizializzazione delle impostazioni', error);
        }
    },

    clearLoadingPlaceholders() {
        const presetContainer = document.getElementById('presetCards');
        const activeContainer = document.getElementById('activeConfigCard');
        const savedContainer = document.getElementById('savedConfigsList');
        
        if (presetContainer) {
            const loading = presetContainer.querySelector('.loading-placeholder');
            if (loading) loading.remove();
            if (presetContainer.children.length === 0 && this.presets.length === 0) {
                presetContainer.innerHTML = '<div class="empty-state"><i data-lucide="sparkles"></i><p>Nessun preset disponibile</p></div>';
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
        }
        
        if (activeContainer) {
            const loading = activeContainer.querySelector('.loading-placeholder');
            if (loading) loading.remove();
            if (activeContainer.children.length === 0 && !this.activeConfig) {
                activeContainer.innerHTML = `
                    <div class="active-config-empty">
                        <i data-lucide="settings"></i>
                        <p>Nessuna configurazione attiva</p>
                        <span class="hint">Seleziona un preset o crea una configurazione personalizzata</span>
                    </div>
                `;
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
        }
        
        if (savedContainer) {
            const loading = savedContainer.querySelector('.loading-placeholder');
            if (loading) loading.remove();
            if (savedContainer.children.length === 0 && this.configs.length === 0) {
                savedContainer.innerHTML = '<div class="empty-state"><i data-lucide="database"></i><p>Nessuna configurazione salvata</p></div>';
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
        }
    },

    async loadPresets() {
        try {
            const response = await fetch('/api/config/presets');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            this.presets = data.presets || [];
        } catch (error) {
            console.error('Failed to load presets:', error);
            this.presets = [];
            this.showError('Errore nel caricamento dei preset', error);
        }
    },

    async loadConfigs() {
        try {
            const response = await fetch('/api/config');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            this.configs = data.configs || [];
        } catch (error) {
            console.error('Failed to load configs:', error);
            this.configs = [];
            this.showError('Errore nel caricamento delle configurazioni', error);
        }
    },

    async loadProviders() {
        // Use cache if available
        if (this.providersCache) {
            this.providers = this.providersCache;
            return;
        }
        
        try {
            const response = await fetch('/api/config/providers');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            this.providers = data.providers || {};
            this.providersCache = this.providers; // Cache the result
        } catch (error) {
            console.error('Failed to load providers:', error);
            this.providers = {};
            // Don't show error toast for providers, it's not critical
        }
    },

    async loadActiveConfig() {
        try {
            const response = await fetch('/api/config/active');
            if (response.ok) {
                const data = await response.json();
                this.activeConfig = data;
            } else if (response.status === 404) {
                this.activeConfig = null;
            } else {
                console.warn(`Failed to load active config: HTTP ${response.status}`);
                this.activeConfig = null;
            }
        } catch (error) {
            console.error('Failed to load active config:', error);
            this.activeConfig = null;
        }
    },

    // Generate provider cards dynamically
    renderProviderCards() {
        const container = document.getElementById('providersGrid');
        if (!container) {
            console.warn('Providers grid container not found');
            return;
        }

        container.innerHTML = Object.entries(PROVIDER_CONFIG).map(([providerType, config]) => {
            const selectId = `${providerType}Provider`;
            const apiKeyId = `${providerType}ApiKey`;
            const apiKeyGroupId = `${providerType}ApiKeyGroup`;
            const baseUrlGroupId = `${providerType}BaseUrlGroup`;
            const baseUrlId = `${providerType}BaseUrl`;
            
            return `
                <div class="provider-card" data-provider-type="${providerType}" role="group" aria-labelledby="${providerType}-title">
                    <div class="provider-header">
                        <div class="provider-icon" aria-hidden="true">
                            <i data-lucide="${config.icon}"></i>
                        </div>
                        <div>
                            <h3 id="${providerType}-title">${config.label}</h3>
                            <p class="provider-desc">${config.desc}</p>
                        </div>
                        <button 
                            class="provider-guide-btn" 
                            data-provider-type="${providerType}" 
                            title="Mostra guida configurazione"
                            aria-label="Mostra guida per ${config.label}"
                            type="button">
                            <i data-lucide="help-circle"></i>
                        </button>
                    </div>
                    <div class="provider-fields">
                        <div class="field-group">
                            <label for="${selectId}">Provider & Modello</label>
                            <select 
                                id="${selectId}" 
                                class="provider-model-select" 
                                aria-required="true"
                                aria-describedby="${selectId}-status">
                                ${config.options.map(opt => 
                                    `<option value="${opt.provider}" data-model="${opt.model}">${opt.label}</option>`
                                ).join('')}
                            </select>
                            <span id="${selectId}-status" class="field-status" aria-live="polite"></span>
                        </div>
                        <div class="field-group" id="${apiKeyGroupId}">
                            <label for="${apiKeyId}">
                                API Key 
                                ${config.apiKeyOptional ? '<span class="optional">(opzionale per locale)</span>' : ''}
                            </label>
                            <div class="input-wrapper">
                                <input 
                                    type="text" 
                                    id="${apiKeyId}" 
                                    class="form-input api-key" 
                                    placeholder="sk-..." 
                                    autocomplete="off"
                                    aria-describedby="${apiKeyId}-status ${apiKeyId}-hint"
                                    aria-invalid="false">
                                <span id="${apiKeyId}-status" class="field-status" aria-live="polite"></span>
                            </div>
                            <span id="${apiKeyId}-hint" class="field-hint"></span>
                        </div>
                        <div class="field-group" id="${baseUrlGroupId}" style="display: none;">
                            <label for="${baseUrlId}">Base URL (Ollama)</label>
                            <input 
                                type="text" 
                                id="${baseUrlId}" 
                                class="form-input" 
                                placeholder="http://localhost:11434" 
                                value="http://localhost:11434"
                                aria-describedby="${baseUrlId}-status">
                            <span id="${baseUrlId}-status" class="field-status" aria-live="polite"></span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Re-initialize icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        // Setup validation for all fields
        this.setupValidation();
    },

    setupEventListeners() {
        // Use event delegation for all dynamic elements
        const configForm = document.querySelector('.config-form');
        if (configForm) {
            // Provider select changes - event delegation
            configForm.addEventListener('change', (e) => {
                if (e.target.classList.contains('provider-model-select')) {
                    this.onProviderModelChange(e.target);
                }
            });

            // API key input changes with debouncing - event delegation
            configForm.addEventListener('input', debounce((e) => {
                if (e.target.classList.contains('api-key') || e.target.id.includes('BaseUrl')) {
                    this.validateField(e.target);
                    this.saveDraft(); // Auto-save draft
                }
            }, 300));

            // Config name input
            const configNameInput = document.getElementById('configName');
            if (configNameInput) {
                configNameInput.addEventListener('input', debounce(() => {
                    this.saveDraft();
                }, 500));
            }
        }

        // Provider guide buttons - already using event delegation
        document.addEventListener('click', (e) => {
            const guideBtn = e.target.closest('.provider-guide-btn');
            if (guideBtn) {
                const providerType = guideBtn.dataset.providerType;
                const select = document.getElementById(`${providerType}Provider`);
                if (select) {
                    const provider = select.value;
                    this.openProviderGuide(providerType, provider);
                }
            }
        });

        // Preset apply buttons - event delegation to avoid duplicate listeners
        document.addEventListener('click', (e) => {
            const presetBtn = e.target.closest('.preset-apply-btn');
            if (presetBtn) {
                const presetId = presetBtn.dataset.presetId;
                if (presetId) {
                    this.applyPreset(presetId);
                }
            }
        });

        // Modal close handlers
        const modal = document.getElementById('providerGuideModal');
        const closeBtn = document.getElementById('closeProviderModal');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeProviderGuide());
        }
        
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeProviderGuide();
                }
            });
        }

        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal && modal.classList.contains('active')) {
                this.closeProviderGuide();
            }
            // Keyboard shortcut: Ctrl+S to save
            if (e.ctrlKey && e.key === 's' && document.getElementById('settingsView')?.classList.contains('active')) {
                e.preventDefault();
                const saveBtn = document.getElementById('saveConfigBtn');
                if (saveBtn && !saveBtn.disabled) {
                    saveBtn.click();
                }
            }
        });

        // Test button
        const testBtn = document.getElementById('testConfigBtn');
        if (testBtn) {
            testBtn.addEventListener('click', () => this.testConfiguration());
        }

        // Save button
        const saveBtn = document.getElementById('saveConfigBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveConfiguration());
        }

        // Initialize all provider selects on load
        document.querySelectorAll('.provider-model-select').forEach(select => {
            this.onProviderModelChange(select);
        });
    },

    setupValidation() {
        // Setup validation for all API key inputs
        document.querySelectorAll('.api-key').forEach(input => {
            // Initial validation
            this.validateField(input);
        });
    },

    validateField(field) {
        const fieldId = field.id;
        const providerType = fieldId.replace('ApiKey', '').replace('BaseUrl', '');
        const isApiKey = fieldId.includes('ApiKey');
        const statusEl = document.getElementById(`${fieldId}-status`);
        const hintEl = document.getElementById(`${fieldId}-hint`);
        
        if (!statusEl) return;

        let isValid = true;
        let message = '';
        let statusClass = '';

        if (isApiKey) {
            const select = document.getElementById(`${providerType}Provider`);
            if (!select) return;
            
            const provider = select.value;
            const value = field.value.trim();

            // Skip validation for local providers
            if (provider === 'local_whisper' || provider === 'ollama') {
                isValid = true;
                message = '';
                statusClass = 'valid';
            } else if (!value) {
                isValid = false;
                message = 'API Key richiesta';
                statusClass = 'invalid';
            } else {
                // Validate format if pattern exists
                const pattern = API_KEY_PATTERNS[provider];
                if (pattern && !pattern.test(value)) {
                    isValid = false;
                    message = 'Formato API Key non valido';
                    statusClass = 'invalid';
                } else {
                    isValid = true;
                    message = 'Valido';
                    statusClass = 'valid';
                }
            }
        } else if (fieldId.includes('BaseUrl')) {
            const value = field.value.trim();
            if (value && !/^https?:\/\/.+/.test(value)) {
                isValid = false;
                message = 'URL non valido';
                statusClass = 'invalid';
            } else {
                isValid = true;
                message = '';
                statusClass = 'valid';
            }
        }

        // Update UI
        field.setAttribute('aria-invalid', !isValid);
        statusEl.className = `field-status ${statusClass}`;
        statusEl.textContent = message;
        statusEl.setAttribute('aria-live', 'polite');

        if (hintEl && isApiKey) {
            const select = document.getElementById(`${providerType}Provider`);
            const provider = select?.value;
            if (provider && this.providers[provider]?.api_key_url) {
                hintEl.innerHTML = `<a href="${this.providers[provider].api_key_url}" target="_blank" rel="noopener">Ottieni API Key</a>`;
            } else {
                hintEl.innerHTML = '';
            }
        }

        // Store validation state
        this.validationStates[fieldId] = isValid;
        
        // Update save button state
        this.updateSaveButtonState();
    },

    updateSaveButtonState() {
        const saveBtn = document.getElementById('saveConfigBtn');
        if (!saveBtn) return;

        const allValid = Object.values(this.validationStates).every(v => v !== false);
        const configName = document.getElementById('configName')?.value.trim();
        
        saveBtn.disabled = !allValid || !configName;
        saveBtn.setAttribute('aria-disabled', !allValid || !configName);
    },

    onProviderModelChange(select) {
        const providerId = select.id.replace('Provider', '');
        const selectedOption = select.options[select.selectedIndex];
        const provider = select.value;
        const model = selectedOption.getAttribute('data-model') || '';
        
        // Show/hide base URL input for local providers
        const baseUrlGroup = document.getElementById(`${providerId}BaseUrlGroup`);
        if (baseUrlGroup) {
            baseUrlGroup.style.display = (provider === 'ollama') ? 'block' : 'none';
        }

        // Show/hide API key requirement
        const apiKeyGroup = document.getElementById(`${providerId}ApiKeyGroup`);
        if (apiKeyGroup) {
            const apiKeyInput = document.getElementById(`${providerId}ApiKey`);
            if (provider === 'local_whisper' || provider === 'ollama') {
                apiKeyGroup.style.display = 'none';
                if (apiKeyInput) {
                    apiKeyInput.value = '';
                    apiKeyInput.removeAttribute('required');
                }
            } else {
                apiKeyGroup.style.display = 'block';
                if (apiKeyInput) {
                    apiKeyInput.placeholder = 'Incolla la tua API key qui';
                    apiKeyInput.required = true;
                }
            }
        }

        // Re-validate the API key field
        const apiKeyInput = document.getElementById(`${providerId}ApiKey`);
        if (apiKeyInput) {
            this.validateField(apiKeyInput);
        }

        // Update provider help/info (now handled by modal)
        this.updateProviderHelp(providerId, provider, model);
    },

    updateProviderHelp(providerId, provider, model) {
        // Help is now shown in modal, so we can hide or remove this section
        const helpDiv = document.getElementById(`${providerId}Help`);
        if (helpDiv) {
            helpDiv.innerHTML = ''; // Clear inline help, modal handles it
        }
    },

    // Save draft to localStorage
    saveDraft() {
        try {
            const configData = this.getFormData();
            const configName = document.getElementById('configName')?.value.trim() || '';
            
            this.draftConfig = {
                name: configName,
                data: configData,
                timestamp: Date.now()
            };
            
            localStorage.setItem('settings_draft', JSON.stringify(this.draftConfig));
        } catch (error) {
            console.warn('Failed to save draft:', error);
        }
    },

    // Load draft from localStorage
    loadDraft() {
        try {
            const draft = localStorage.getItem('settings_draft');
            if (draft) {
                this.draftConfig = JSON.parse(draft);
                // Restore form values
                if (this.draftConfig.name) {
                    const nameInput = document.getElementById('configName');
                    if (nameInput) nameInput.value = this.draftConfig.name;
                }
                
                // Restore provider selections and API keys
                if (this.draftConfig.data) {
                    Object.entries(this.draftConfig.data).forEach(([providerType, config]) => {
                        const select = document.getElementById(`${providerType}Provider`);
                        if (select && config.provider) {
                            // Find matching option
                            const option = Array.from(select.options).find(opt => 
                                opt.value === config.provider && opt.getAttribute('data-model') === config.model
                            );
                            if (option) {
                                select.value = config.provider;
                                this.onProviderModelChange(select);
                                
                                // Restore API key
                                const apiKeyInput = document.getElementById(`${providerType}ApiKey`);
                                if (apiKeyInput && config.api_key) {
                                    apiKeyInput.value = config.api_key;
                                }
                                
                                // Restore base URL
                                const baseUrlInput = document.getElementById(`${providerType}BaseUrl`);
                                if (baseUrlInput && config.base_url) {
                                    baseUrlInput.value = config.base_url;
                                }
                            }
                        }
                    });
                }
            }
        } catch (error) {
            console.warn('Failed to load draft:', error);
        }
    },

    // Clear draft
    clearDraft() {
        localStorage.removeItem('settings_draft');
        this.draftConfig = null;
    },

    getProviderGuide(provider, providerType) {
        const guides = {
            'openai': {
                'transcription': `
                    <p><strong>OpenAI Whisper</strong> - Trascrizione audio di alta qualità</p>
                    <ol>
                        <li>Vai su <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener">platform.openai.com/api-keys</a></li>
                        <li>Crea un account o accedi</li>
                        <li>Clicca "Create new secret key"</li>
                        <li>Copia la chiave e incollala qui</li>
                        <li>Assicurati di avere credito disponibile sul tuo account</li>
                    </ol>
                    <p><strong>Costo:</strong> ~$0.006 per minuto di audio</p>
                `,
                'vision': `
                    <p><strong>GPT-4o Vision</strong> - Analisi visiva avanzata</p>
                    <ol>
                        <li>Richiede API key OpenAI (stessa chiave di Whisper)</li>
                        <li>Modello consigliato: <code>gpt-4o</code> (migliore qualità) o <code>gpt-4o-mini</code> (più economico)</li>
                        <li>Costo: ~$0.01-0.10 per immagine (dipende dalla risoluzione)</li>
                    </ol>
                `,
                'analysis': `
                    <p><strong>GPT-4o</strong> - Analisi testuale avanzata</p>
                    <ol>
                        <li>Usa la stessa API key OpenAI</li>
                        <li>Modello <code>gpt-4o</code> per massima qualità</li>
                        <li>Modello <code>gpt-4o-mini</code> per risparmiare (85% qualità, 15x più economico)</li>
                        <li>Costo: ~$0.005-0.015 per 1K token</li>
                    </ol>
                `
            },
            'groq': `
                <p><strong>Groq</strong> - API gratuita con rate limit</p>
                <ol>
                    <li>Vai su <a href="https://console.groq.com/keys" target="_blank" rel="noopener">console.groq.com/keys</a></li>
                    <li>Registrati gratuitamente</li>
                    <li>Crea una nuova API key</li>
                    <li>Copia e incolla la chiave qui</li>
                </ol>
                <p><strong>Vantaggi:</strong> Gratuito, veloce, buona qualità</p>
                <p><strong>Limitazioni:</strong> 30 richieste/minuto, modelli Llama 3.1</p>
            `,
            'ollama': `
                <p><strong>Ollama</strong> - Modelli locali (100% gratuito)</p>
                <ol>
                    <li>Installa Ollama da <a href="https://ollama.ai" target="_blank" rel="noopener">ollama.ai</a></li>
                    <li>Scarica i modelli necessari:
                        <ul>
                            <li><code>ollama pull llava:13b</code> (per vision)</li>
                            <li><code>ollama pull llama3.1:8b</code> (per analisi)</li>
                        </ul>
                    </li>
                    <li>Assicurati che Ollama sia in esecuzione (default: http://localhost:11434)</li>
                    <li>Inserisci l'URL base se diverso da quello predefinito</li>
                </ol>
                <p><strong>Vantaggi:</strong> Completamente gratuito, dati locali</p>
                <p><strong>Requisiti:</strong> GPU consigliata per performance migliori</p>
            `,
            'local_whisper': `
                <p><strong>Faster-Whisper</strong> - Trascrizione locale gratuita</p>
                <ol>
                    <li>Installa: <code>pip install faster-whisper</code></li>
                    <li>Nessuna API key richiesta</li>
                    <li>Il modello verrà scaricato automaticamente al primo utilizzo</li>
                    <li>Modelli disponibili: <code>tiny</code>, <code>base</code>, <code>small</code>, <code>medium</code>, <code>large-v3</code></li>
                </ol>
                <p><strong>Vantaggi:</strong> Gratuito, dati locali, alta qualità</p>
                <p><strong>Requisiti:</strong> CPU/GPU locale, spazio disco per i modelli</p>
            `,
            'together': `
                <p><strong>Together AI</strong> - Modelli open-source economici</p>
                <ol>
                    <li>Vai su <a href="https://api.together.xyz/settings/api-keys" target="_blank" rel="noopener">api.together.xyz</a></li>
                    <li>Registrati e ottieni API key</li>
                    <li>Modelli supportati: Llama Vision, Llama 3.1</li>
                </ol>
                <p><strong>Costo:</strong> ~$0.0002 per 1K token (molto economico)</p>
            `,
            'google': `
                <p><strong>Google AI Studio</strong> - Gemini gratuito con limiti</p>
                <ol>
                    <li>Vai su <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener">aistudio.google.com</a></li>
                    <li>Accedi con account Google</li>
                    <li>Crea una nuova API key</li>
                    <li>Copia e incolla qui</li>
                </ol>
                <p><strong>Vantaggi:</strong> Gratuito, buona qualità</p>
                <p><strong>Limitazioni:</strong> 15 richieste/minuto</p>
            `,
            'anthropic': `
                <p><strong>Anthropic Claude</strong> - Alta qualità, costo medio</p>
                <ol>
                    <li>Vai su <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noopener">console.anthropic.com</a></li>
                    <li>Crea account e ottieni API key</li>
                    <li>Modello consigliato: <code>claude-3-haiku-20240307</code> (economico)</li>
                </ol>
                <p><strong>Costo:</strong> ~$0.25 per 1M token</p>
            `
        };

        if (provider === 'openai' && guides['openai'] && guides['openai'][providerType]) {
            return guides['openai'][providerType];
        }
        return guides[provider] || null;
    },

    renderPresets() {
        const container = document.getElementById('presetCards');
        if (!container) {
            console.warn('Preset container not found');
            return;
        }

        const loadingPlaceholder = container.querySelector('.loading-placeholder');
        if (loadingPlaceholder) {
            loadingPlaceholder.remove();
        }

        if (this.presets.length === 0) {
            container.innerHTML = '<div class="empty-state"><i data-lucide="sparkles"></i><p>Nessun preset disponibile</p></div>';
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }

        container.innerHTML = this.presets.map(preset => {
            const config = preset.config || {};
            const isFree = preset.cost_per_video_5min.toLowerCase().includes('free');
            
            return `
            <div class="preset-card" data-preset-id="${preset.id}" role="article" aria-labelledby="preset-${preset.id}-title">
                <div class="preset-card-header">
                    <div class="preset-title">
                        <h3 id="preset-${preset.id}-title">${preset.name}</h3>
                        <div class="preset-badges">
                            <span class="badge badge-quality badge-${preset.quality}">
                                ${'⭐'.repeat(preset.quality_stars || 3)}
                            </span>
                            ${isFree ? '<span class="badge badge-free">Gratuito</span>' : ''}
                        </div>
                    </div>
                    <div class="preset-cost">
                        <span class="cost-label">Costo (5min):</span>
                        <span class="cost-value">${preset.cost_per_video_5min}</span>
                    </div>
                </div>
                
                <p class="preset-description">${preset.description}</p>
                
                <div class="preset-stack">
                    <div class="stack-item">
                        <i data-lucide="mic"></i>
                        <span class="stack-label">Trascrizione</span>
                        <span class="stack-value">${this.getProviderDisplayName(config.transcription?.provider)}</span>
                    </div>
                    <div class="stack-item">
                        <i data-lucide="eye"></i>
                        <span class="stack-label">Vision</span>
                        <span class="stack-value">${this.getProviderDisplayName(config.vision?.provider)}</span>
                    </div>
                    <div class="stack-item">
                        <i data-lucide="brain"></i>
                        <span class="stack-label">Analisi</span>
                        <span class="stack-value">${this.getProviderDisplayName(config.analysis?.provider)}</span>
                    </div>
                    <div class="stack-item">
                        <i data-lucide="zap"></i>
                        <span class="stack-label">Arricchimento</span>
                        <span class="stack-value">${this.getProviderDisplayName(config.enrichment?.provider)}</span>
                    </div>
                </div>

                ${preset.setup_requirements && preset.setup_requirements.length > 0 ? `
                <details class="preset-requirements">
                    <summary>
                        <i data-lucide="info"></i>
                        <span>Requisiti Setup</span>
                        <i data-lucide="chevron-down"></i>
                    </summary>
                    <ul>
                        ${preset.setup_requirements.map(req => `<li>${req}</li>`).join('')}
                    </ul>
                </details>
                ` : ''}

                <button class="btn btn-primary btn-block preset-apply-btn" data-preset-id="${preset.id}" aria-label="Applica preset ${preset.name}">
                    <i data-lucide="check"></i> Applica Preset
                </button>
            </div>
        `;
        }).join('');

        // Event delegation is handled in setupEventListeners to avoid duplicate listeners

        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    },

    getProviderDisplayName(provider) {
        const names = {
            'openai': 'OpenAI',
            'groq': 'Groq',
            'ollama': 'Ollama',
            'together': 'Together AI',
            'google': 'Google AI',
            'anthropic': 'Anthropic',
            'local_whisper': 'Faster-Whisper'
        };
        return names[provider] || provider || 'N/A';
    },

    openProviderGuide(providerType, provider) {
        const modal = document.getElementById('providerGuideModal');
        if (!modal) return;

        // Lazy load modal content only when opened
        const providerInfo = this.providers[provider] || {};
        const guide = this.getProviderGuide(provider, providerType);
        
        const typeNames = {
            'transcription': 'Trascrizione Audio',
            'vision': 'Analisi Visiva',
            'analysis': 'Analisi Contenuto',
            'enrichment': 'Arricchimento'
        };

        const icons = {
            'transcription': 'mic',
            'vision': 'eye',
            'analysis': 'brain',
            'enrichment': 'zap'
        };

        const modalName = document.getElementById('modalProviderName');
        const modalType = document.getElementById('modalProviderType');
        const modalIcon = document.getElementById('modalProviderIcon');
        const modalContent = document.getElementById('modalProviderContent');

        if (modalName) {
            modalName.textContent = providerInfo.name || this.getProviderDisplayName(provider);
        }

        if (modalType) {
            modalType.textContent = typeNames[providerType] || providerType;
        }

        if (modalIcon) {
            modalIcon.innerHTML = `<i data-lucide="${icons[providerType] || 'settings'}"></i>`;
        }

        let content = '';

        if (providerInfo.quality_rating || providerInfo.cost_rating) {
            content += `
                <div class="modal-badges">
                    ${providerInfo.quality_rating ? `
                        <span class="badge badge-quality badge-${providerInfo.quality_rating}">
                            <i data-lucide="star"></i> Qualità: ${providerInfo.quality_rating}
                        </span>
                    ` : ''}
                    ${providerInfo.cost_rating ? `
                        <span class="badge badge-cost">
                            <i data-lucide="dollar-sign"></i> Costo: ${providerInfo.cost_rating === 'free' ? 'Gratuito' : providerInfo.cost_rating}
                        </span>
                    ` : ''}
                    ${providerInfo.rate_limits ? `
                        <span class="badge badge-info">
                            <i data-lucide="gauge"></i> ${providerInfo.rate_limits}
                        </span>
                    ` : ''}
                </div>
            `;
        }

        if (guide) {
            content += `
                <div class="modal-section">
                    <h3><i data-lucide="book-open"></i> Guida Configurazione</h3>
                    <div class="modal-guide-content">
                        ${guide}
                    </div>
                </div>
            `;
        }

        if (providerInfo.api_key_url) {
            content += `
                <div class="modal-section">
                    <h3><i data-lucide="key"></i> Come Ottenere l'API Key</h3>
                    <div class="modal-steps">
                        <ol>
                            <li>Vai al sito del provider usando il link qui sotto</li>
                            <li>Accedi o crea un account</li>
                            <li>Naviga alla sezione API Keys</li>
                            <li>Crea una nuova API key</li>
                            <li>Copia la chiave e incollala nel campo corrispondente</li>
                        </ol>
                        <a href="${providerInfo.api_key_url}" target="_blank" rel="noopener" class="btn btn-primary modal-link-btn">
                            <i data-lucide="external-link"></i> Ottieni API Key
                        </a>
                    </div>
                </div>
            `;
        } else if (provider === 'local_whisper' || provider === 'ollama') {
            content += `
                <div class="modal-section">
                    <h3><i data-lucide="info"></i> Provider Locale</h3>
                    <div class="modal-info-box">
                        <p><strong>Nessuna API Key richiesta!</strong></p>
                        <p>Questo provider funziona localmente sul tuo computer. Assicurati di avere installato e configurato correttamente il software necessario.</p>
                    </div>
                </div>
            `;
        }

        if (providerInfo.website) {
            content += `
                <div class="modal-section">
                    <h3><i data-lucide="link"></i> Link Utili</h3>
                    <div class="modal-links">
                        <a href="${providerInfo.website}" target="_blank" rel="noopener" class="modal-link">
                            <i data-lucide="external-link"></i> Sito Web Ufficiale
                        </a>
                        ${providerInfo.documentation_url ? `
                            <a href="${providerInfo.documentation_url}" target="_blank" rel="noopener" class="modal-link">
                                <i data-lucide="book"></i> Documentazione
                            </a>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        const modelSuggestions = this.getModelSuggestions(provider, providerType);
        if (modelSuggestions.length > 0) {
            content += `
                <div class="modal-section">
                    <h3><i data-lucide="cpu"></i> Modelli Consigliati</h3>
                    <div class="modal-models">
                        ${modelSuggestions.map(model => `
                            <div class="model-suggestion">
                                <code>${model.name}</code>
                                ${model.description ? `<span class="model-desc">${model.description}</span>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        if (modalContent) {
            modalContent.innerHTML = content || '<p>Nessuna informazione disponibile per questo provider.</p>';
        }

        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Focus management for accessibility
        const firstFocusable = modal.querySelector('button, a, input, select, textarea');
        if (firstFocusable) {
            firstFocusable.focus();
        }

        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    },

    closeProviderGuide() {
        const modal = document.getElementById('providerGuideModal');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
            
            // Return focus to the button that opened the modal
            const activeElement = document.activeElement;
            if (activeElement && activeElement.classList.contains('provider-guide-btn')) {
                activeElement.focus();
            }
        }
    },

    getModelSuggestions(provider, providerType) {
        const suggestions = {
            'openai': {
                'transcription': [{ name: 'whisper-1', description: 'Modello standard per trascrizione' }],
                'vision': [
                    { name: 'gpt-4o', description: 'Massima qualità, costo più alto' },
                    { name: 'gpt-4o-mini', description: 'Buona qualità, più economico' }
                ],
                'analysis': [
                    { name: 'gpt-4o', description: 'Massima qualità' },
                    { name: 'gpt-4o-mini', description: '85% qualità, 15x più economico' }
                ],
                'enrichment': [{ name: 'gpt-4o-mini', description: 'Ottimo rapporto qualità/prezzo' }]
            },
            'groq': {
                'analysis': [
                    { name: 'llama-3.1-70b-versatile', description: 'Alta qualità' },
                    { name: 'llama-3.1-8b-instant', description: 'Veloce ed economico' }
                ],
                'enrichment': [{ name: 'llama-3.1-8b-instant', description: 'Veloce e gratuito' }]
            },
            'ollama': {
                'vision': [{ name: 'llava:13b', description: 'Modello vision locale' }],
                'analysis': [{ name: 'llama3.1:8b', description: 'Buon equilibrio qualità/velocità' }],
                'enrichment': [{ name: 'llama3.1:8b', description: 'Veloce per arricchimento' }]
            },
            'together': {
                'vision': [{ name: 'meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo', description: 'Vision economico' }],
                'analysis': [{ name: 'meta-llama/Llama-3.1-70B-Instruct-Turbo', description: 'Alta qualità' }]
            },
            'google': {
                'vision': [{ name: 'gemini-1.5-flash', description: 'Gratuito con rate limit' }],
                'analysis': [{ name: 'gemini-1.5-flash', description: 'Gratuito e veloce' }]
            },
            'anthropic': {
                'analysis': [{ name: 'claude-3-haiku-20240307', description: 'Economico e veloce' }]
            },
            'local_whisper': {
                'transcription': [
                    { name: 'large-v3', description: 'Massima qualità' },
                    { name: 'medium', description: 'Buon equilibrio' },
                    { name: 'small', description: 'Veloce' }
                ]
            }
        };

        return suggestions[provider]?.[providerType] || [];
    },

    async applyPreset(presetId) {
        try {
            Utils.showToast('Applicazione preset in corso...', 'info');
            const response = await fetch(`/api/config/presets/${presetId}/apply`, {
                method: 'POST'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to apply preset');
            }

            const data = await response.json();
            Utils.showToast(`Preset "${data.config.config_name}" applicato con successo!`, 'success');
            
            await this.reloadAnalyzer();
            await this.loadConfigs();
            await this.loadActiveConfig();
            this.renderActiveConfig();
            this.renderSavedConfigs();
        } catch (error) {
            console.error('Failed to apply preset:', error);
            this.showError('Errore nell\'applicazione del preset', error);
        }
    },

    renderActiveConfig() {
        const container = document.getElementById('activeConfigCard');
        if (!container) {
            console.warn('Active config container not found');
            return;
        }

        const loadingPlaceholder = container.querySelector('.loading-placeholder');
        if (loadingPlaceholder) {
            loadingPlaceholder.remove();
        }

        if (!this.activeConfig) {
            container.innerHTML = `
                <div class="active-config-empty">
                    <i data-lucide="settings"></i>
                    <p>Nessuna configurazione attiva</p>
                    <span class="hint">Seleziona un preset o crea una configurazione personalizzata</span>
                </div>
            `;
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }

        container.innerHTML = `
            <div class="active-config-content">
                <div class="active-config-header">
                    <div>
                        <h3>${this.activeConfig.config_name}</h3>
                        <div class="active-badges">
                            <span class="badge badge-active">Attiva</span>
                            ${this.activeConfig.quality_rating ? `<span class="badge badge-quality badge-${this.activeConfig.quality_rating}">${this.activeConfig.quality_rating}</span>` : ''}
                        </div>
                    </div>
                    <div class="active-cost">
                        <span class="cost-label">Costo stimato:</span>
                        <span class="cost-value">${this.activeConfig.estimated_cost_per_video}</span>
                    </div>
                </div>
                <div class="active-stack">
                    <div class="stack-item">
                        <i data-lucide="mic"></i>
                        <span>${this.getProviderDisplayName(this.activeConfig.transcription.provider)}</span>
                        <span class="model-name">${this.activeConfig.transcription.model}</span>
                    </div>
                    <div class="stack-item">
                        <i data-lucide="eye"></i>
                        <span>${this.getProviderDisplayName(this.activeConfig.vision.provider)}</span>
                        <span class="model-name">${this.activeConfig.vision.model}</span>
                    </div>
                    <div class="stack-item">
                        <i data-lucide="brain"></i>
                        <span>${this.getProviderDisplayName(this.activeConfig.analysis.provider)}</span>
                        <span class="model-name">${this.activeConfig.analysis.model}</span>
                    </div>
                    <div class="stack-item">
                        <i data-lucide="zap"></i>
                        <span>${this.getProviderDisplayName(this.activeConfig.enrichment.provider)}</span>
                        <span class="model-name">${this.activeConfig.enrichment.model}</span>
                    </div>
                </div>
            </div>
        `;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    },

    renderSavedConfigs() {
        const container = document.getElementById('savedConfigsList');
        if (!container) return;

        if (this.configs.length === 0) {
            container.innerHTML = '<div class="empty-state"><i data-lucide="database"></i><p>Nessuna configurazione salvata</p></div>';
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }

        container.innerHTML = this.configs.map(config => `
            <div class="saved-config-card ${config.is_active ? 'active' : ''}" role="article" aria-labelledby="config-${config.id}-title">
                <div class="saved-card-header">
                    <div>
                        <h4 id="config-${config.id}-title">${config.config_name}</h4>
                        <div class="saved-badges">
                            ${config.is_active ? '<span class="badge badge-active">Attiva</span>' : ''}
                            ${config.quality_rating ? `<span class="badge badge-quality badge-${config.quality_rating}">${config.quality_rating}</span>` : ''}
                        </div>
                    </div>
                    <div class="saved-actions">
                        ${!config.is_active ? `
                            <button class="btn btn-sm btn-primary activate-btn" data-config-id="${config.id}" aria-label="Attiva configurazione ${config.config_name}">
                                <i data-lucide="check-circle"></i> Attiva
                            </button>
                        ` : ''}
                        <button class="btn btn-sm btn-danger delete-btn" data-config-id="${config.id}" aria-label="Elimina configurazione ${config.config_name}">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </div>
                </div>
                <div class="saved-card-info">
                    <div class="info-item">
                        <i data-lucide="dollar-sign"></i>
                        <span>${config.estimated_cost_per_video}</span>
                    </div>
                    <div class="info-item">
                        <i data-lucide="star"></i>
                        <span>${config.quality_rating || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `).join('');

        // Use event delegation for saved config buttons
        container.addEventListener('click', (e) => {
            const activateBtn = e.target.closest('.activate-btn');
            const deleteBtn = e.target.closest('.delete-btn');
            
            if (activateBtn) {
                const configId = parseInt(activateBtn.dataset.configId);
                this.activateConfig(configId);
            } else if (deleteBtn) {
                const configId = parseInt(deleteBtn.dataset.configId);
                this.deleteConfig(configId);
            }
        });

        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    },

    async activateConfig(configId) {
        try {
            const response = await fetch(`/api/config/${configId}/activate`, {
                method: 'POST'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to activate config');
            }

            Utils.showToast('Configurazione attivata con successo!', 'success');
            
            await this.reloadAnalyzer();
            await this.loadConfigs();
            await this.loadActiveConfig();
            this.renderActiveConfig();
            this.renderSavedConfigs();
        } catch (error) {
            console.error('Failed to activate config:', error);
            this.showError('Errore nell\'attivazione della configurazione', error);
        }
    },

    async deleteConfig(configId) {
        if (!confirm('Sei sicuro di voler eliminare questa configurazione?')) {
            return;
        }

        try {
            const response = await fetch(`/api/config/${configId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete config');
            }

            Utils.showToast('Configurazione eliminata', 'success');
            
            await this.loadConfigs();
            this.renderSavedConfigs();
        } catch (error) {
            console.error('Failed to delete config:', error);
            this.showError('Errore nell\'eliminazione della configurazione', error);
        }
    },

    async testConfiguration() {
        const configData = this.getFormData();
        
        if (!this.validateForm(configData)) {
            return;
        }

        const testBtn = document.getElementById('testConfigBtn');
        const originalText = testBtn?.innerHTML;
        
        try {
            if (testBtn) {
                testBtn.disabled = true;
                testBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Test in corso...';
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
            
            Utils.showToast('Test configurazione in corso...', 'info');
            
            const response = await fetch('/api/config/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(configData)
            });

            const result = await response.json();
            
            if (result.success) {
                Utils.showToast('Test completato con successo! Tutti i provider sono disponibili.', 'success');
            } else {
                const failed = Object.entries(result.results || {})
                    .filter(([_, r]) => !r.success)
                    .map(([name, r]) => `${name}: ${r.error || 'Failed'}`)
                    .join(', ');
                Utils.showToast(`Test fallito per: ${failed}`, 'error');
            }
        } catch (error) {
            console.error('Test failed:', error);
            this.showError('Errore nel test della configurazione', error);
        } finally {
            if (testBtn) {
                testBtn.disabled = false;
                testBtn.innerHTML = originalText || '<i data-lucide="test-tube"></i> Testa Configurazione';
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
        }
    },

    async saveConfiguration() {
        const configData = this.getFormData();
        const configName = document.getElementById('configName').value.trim();
        
        if (!configName) {
            Utils.showToast('Inserisci un nome per la configurazione', 'error');
            return;
        }

        if (!this.validateForm(configData)) {
            return;
        }

        const saveBtn = document.getElementById('saveConfigBtn');
        const originalText = saveBtn?.innerHTML;
        
        try {
            if (saveBtn) {
                saveBtn.disabled = true;
                saveBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Salvataggio...';
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
            
            Utils.showToast('Salvataggio configurazione...', 'info');
            
            const payload = {
                config_name: configName,
                ...configData,
                quality_rating: 'medium',
                estimated_cost_per_video: 'Unknown'
            };

            const response = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save config');
            }

            Utils.showToast('Configurazione salvata con successo!', 'success');
            
            // Clear draft after successful save
            this.clearDraft();
            
            await this.loadConfigs();
            this.renderSavedConfigs();
            
            // Clear form
            document.getElementById('configName').value = '';
            document.querySelectorAll('.api-key').forEach(input => input.value = '');
            document.querySelectorAll('.provider-model-select').forEach(select => {
                select.selectedIndex = 0;
                this.onProviderModelChange(select);
            });
            this.validationStates = {};
            this.updateSaveButtonState();
        } catch (error) {
            console.error('Failed to save config:', error);
            this.showError('Errore nel salvataggio della configurazione', error);
        } finally {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = originalText || '<i data-lucide="save"></i> Salva Configurazione';
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
        }
    },

    getFormData() {
        const getProviderModel = (selectId) => {
            const select = document.getElementById(selectId);
            if (!select) return { provider: null, model: null };
            const selectedOption = select.options[select.selectedIndex];
            return {
                provider: select.value,
                model: selectedOption.getAttribute('data-model') || ''
            };
        };

        const transcription = getProviderModel('transcriptionProvider');
        const vision = getProviderModel('visionProvider');
        const analysis = getProviderModel('analysisProvider');
        const enrichment = getProviderModel('enrichmentProvider');

        return {
            transcription: {
                provider: transcription.provider,
                model: transcription.model,
                api_key: document.getElementById('transcriptionApiKey')?.value.trim() || null,
                base_url: document.getElementById('transcriptionBaseUrl')?.value.trim() || null
            },
            vision: {
                provider: vision.provider,
                model: vision.model,
                api_key: document.getElementById('visionApiKey')?.value.trim() || null,
                base_url: document.getElementById('visionBaseUrl')?.value.trim() || null
            },
            analysis: {
                provider: analysis.provider,
                model: analysis.model,
                api_key: document.getElementById('analysisApiKey')?.value.trim() || null,
                base_url: document.getElementById('analysisBaseUrl')?.value.trim() || null
            },
            enrichment: {
                provider: enrichment.provider,
                model: enrichment.model,
                api_key: document.getElementById('enrichmentApiKey')?.value.trim() || null,
                base_url: document.getElementById('enrichmentBaseUrl')?.value.trim() || null
            }
        };
    },

    validateForm(configData) {
        const providers = ['transcription', 'vision', 'analysis', 'enrichment'];
        
        for (const provider of providers) {
            const providerConfig = configData[provider];
            if (providerConfig.provider !== 'local_whisper' && 
                providerConfig.provider !== 'ollama' && 
                !providerConfig.api_key) {
                Utils.showToast(`API Key richiesta per ${provider} (${providerConfig.provider})`, 'error');
                // Focus on the problematic field
                const input = document.getElementById(`${provider}ApiKey`);
                if (input) {
                    input.focus();
                    input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                return false;
            }
        }
        
        return true;
    },

    async reloadAnalyzer() {
        try {
            const response = await fetch('/api/config/reload', {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error('Failed to reload analyzer');
            }

            Utils.showToast('Configurazione ricaricata. Le nuove analisi useranno questa configurazione.', 'success');
        } catch (error) {
            console.error('Failed to reload analyzer:', error);
            this.showError('Errore nel ricaricare la configurazione', error);
        }
    },

    // Improved error handling
    showError(message, error) {
        const errorMessage = error?.message || error?.toString() || 'Errore sconosciuto';
        const fullMessage = `${message}: ${errorMessage}`;
        
        if (typeof Utils !== 'undefined' && Utils.showToast) {
            Utils.showToast(fullMessage, 'error');
        } else {
            console.error(fullMessage);
        }
    },

    // Public method called from app.js - reset and reload
    async reload() {
        this.initialized = false;
        this.providersCache = null; // Clear cache on reload
        await this.init();
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Settings will be initialized when view is shown
    });
} else {
    // DOM already loaded
}
