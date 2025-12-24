// ========================================
// State Management Module
// ========================================

window.AppState = {
    API_BASE: '',
    MIN_CONTEXT_CHARS: 50,
    VIDEO_FORMATS: ['.mp4', '.mov', '.avi', '.mkv', '.webm'],
    AUDIO_FORMATS: ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.wma', '.opus'],
    
    currentVideoId: null,
    currentMediaType: 'video',  // 'video' or 'audio'
    currentMediaFilter: 'all',  // 'all', 'video', 'audio'
    selectedAnalysisType: 'auto',  // 'auto', 'reverse_engineering', 'meeting', 'debrief', 'brainstorming', 'notes'
    pollingInterval: null,
    selectedFile: null,
    originalContext: '',
    optimizedContext: ''
};

