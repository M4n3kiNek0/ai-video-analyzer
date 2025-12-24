export interface Video {
    id: number;
    filename: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    media_type: 'video' | 'audio';
    analysis_type: string;
    duration: number; // in seconds
    file_size_bytes: number;
    created_at: string;
    updated_at: string;
    thumbnail_url?: string; // Derived or fetched
}

export interface VideoAnalysis {
    video: Video;
    transcript?: {
        full_text: string;
        segments: any[];
        language: string;
    };
    keyframes: any[];
    analysis: any;
}
