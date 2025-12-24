"use client";

import { useEffect, useState, useRef, use } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { VideoAnalysis } from "@/types";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Play, Pause, Download, Trash2, Clock, FileText, Sparkles, Terminal } from "lucide-react";
import { cn } from "@/lib/utils";
import { ProgressTerminal } from "@/components/ProgressTerminal";

// Helper for timestamp formatting
const formatTime = (seconds: number) => {
    const date = new Date(seconds * 1000);
    const hh = date.getUTCHours();
    const mm = date.getUTCMinutes();
    const ss = date.getUTCSeconds().toString().padStart(2, "0");
    if (hh) {
        return `${hh}:${mm.toString().padStart(2, "0")}:${ss}`;
    }
    return `${mm}:${ss}`;
};

export default function VideoDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const router = useRouter();
    const unwrappedParams = use(params);
    const { id } = unwrappedParams;

    const [data, setData] = useState<VideoAnalysis | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);

    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const response = await api.get(`/videos/${id}`);
                setData(response.data);
            } catch (err) {
                console.error("Failed to load video details:", err);
                setError("Failed to load video details.");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [id]);

    const handleTimeUpdate = () => {
        if (videoRef.current) {
            setCurrentTime(videoRef.current.currentTime);
        }
    };

    const jumpToTime = (seconds: number) => {
        if (videoRef.current) {
            videoRef.current.currentTime = seconds;
            videoRef.current.play();
            setIsPlaying(true);
        }
    };

    const handleDelete = async () => {
        if (!confirm("Delete this video permanently?")) return;
        try {
            await api.delete(`/videos/${id}`);
            router.push("/");
        } catch (err) {
            alert("Delete failed");
        }
    };

    if (loading) {
        return <div className="flex h-[calc(100vh-2rem)] items-center justify-center text-zinc-400">Loading analysis...</div>;
    }

    if (error || !data) {
        return (
            <div className="flex flex-col items-center justify-center h-[calc(100vh-2rem)] gap-4">
                <p className="text-red-400">{error || "Video not found"}</p>
                <Button onClick={() => router.push('/')}>Back to Dashboard</Button>
            </div>
        );
    }

    const { video, transcript, keyframes, analysis } = data;

    return (
        <div className="flex flex-col h-[calc(100vh-2rem)] overflow-hidden bg-black text-white -mx-4 md:-mx-8 -mt-4 px-4 md:px-8 pt-4">
            {/* Header */}
            <div className="h-16 border-b border-white/10 flex items-center px-6 justify-between bg-zinc-900/50 backdrop-blur-md">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => router.push('/')} className="text-zinc-400 hover:text-white">
                        <ArrowLeft className="w-5 h-5" />
                    </Button>
                    <div>
                        <h1 className="font-semibold text-lg line-clamp-1">{video.filename}</h1>
                        <div className="flex items-center gap-2 text-xs text-zinc-500">
                            <span className="capitalize">{video.status}</span>
                            <span>•</span>
                            <span>{new Date(video.created_at).toLocaleDateString()}</span>
                            {video.analysis_type && (
                                <>
                                    <span>•</span>
                                    <Badge variant="secondary" className="text-[10px] h-4 px-1">{video.analysis_type}</Badge>
                                </>
                            )}
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {video.status === 'completed' && (
                        <>
                            <Button
                                variant="outline"
                                size="sm"
                                className="hidden md:flex items-center gap-2 bg-blue-600 text-white border-blue-500 hover:bg-blue-700"
                                onClick={async () => {
                                    try {
                                        const response = await fetch(`/api/videos/${video.id}/export/pdf`);
                                        if (!response.ok) throw new Error('Export failed');
                                        const blob = await response.blob();
                                        const url = window.URL.createObjectURL(blob);
                                        const a = document.createElement('a');
                                        a.href = url;
                                        a.download = `${video.filename.replace(/\.[^/.]+$/, '')}_report.pdf`;
                                        document.body.appendChild(a);
                                        a.click();
                                        window.URL.revokeObjectURL(url);
                                        a.remove();
                                    } catch (err) {
                                        alert('Failed to export PDF');
                                    }
                                }}
                            >
                                <Download className="w-4 h-4" /> PDF
                                </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                className="hidden md:flex items-center gap-2 bg-emerald-600 text-white border-emerald-500 hover:bg-emerald-700"
                                onClick={async () => {
                                    try {
                                        const response = await fetch(`/api/videos/${video.id}/export/zip`);
                                        if (!response.ok) throw new Error('Export failed');
                                        const blob = await response.blob();
                                        const url = window.URL.createObjectURL(blob);
                                        const a = document.createElement('a');
                                        a.href = url;
                                        a.download = `${video.filename.replace(/\.[^/.]+$/, '')}_export.zip`;
                                        document.body.appendChild(a);
                                        a.click();
                                        window.URL.revokeObjectURL(url);
                                        a.remove();
                                    } catch (err) {
                                        alert('Failed to export ZIP');
                                    }
                                }}
                            >
                                <Download className="w-4 h-4" /> ZIP
                            </Button>
                        </>
                    )}
                    <Button variant="ghost" size="icon" className="text-zinc-400 hover:text-red-400" onClick={handleDelete}>
                        <Trash2 className="w-4 h-4" />
                    </Button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col md:flex-row overflow-hidden min-h-0">
                {/* Left Column: Player */}
                <div className="w-full md:w-2/3 lg:w-3/4 flex flex-col bg-zinc-950 relative min-h-0">
                    <div className="flex-1 flex items-center justify-center p-4 min-h-0 overflow-hidden">
                        {/* Actual Video Player */}
                        {/* Note: In production, we assume a static file server or S3 URL. Using a placeholder or assuming generic path */}
                        <video
                            ref={videoRef}
                            className="max-h-full max-w-full rounded-lg shadow-2xl bg-black"
                            controls
                            onTimeUpdate={handleTimeUpdate}
                            onPlay={() => setIsPlaying(true)}
                            onPause={() => setIsPlaying(false)}
                        >
                            {/* We need a real URL here. Assuming backend returns an S3 URL or similar in future */}
                            {/* For now, use a placeholder if url is missing, or construct it if local */}
                            <source src={`http://localhost:8000/static/videos/${video.id}.mp4`} type="video/mp4" />
                            <p>Video playback not supported</p>
                        </video>
                    </div>

                    {/* Keyframes Strip (Optional) */}
                    {keyframes && keyframes.length > 0 && (
                        <div className="h-24 flex-shrink-0 border-t border-white/10 bg-zinc-900 overflow-x-auto whitespace-nowrap p-2 flex gap-2 scrollbar-thin scrollbar-thumb-zinc-700">
                            {keyframes.map((kf: any) => (
                                <div
                                    key={kf.id}
                                    className="relative group cursor-pointer min-w-[120px] h-full rounded overflow-hidden border border-white/5 hover:border-blue-500"
                                    onClick={() => jumpToTime(kf.timestamp)}
                                >
                                    <img src={kf.s3_url || "/placeholder.jpg"} className="w-full h-full object-cover opacity-70 group-hover:opacity-100 transition-opacity" />
                                    <div className="absolute bottom-1 right-1 px-1 bg-black/70 rounded text-[10px] font-mono">
                                        {formatTime(kf.timestamp)}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Right Column: Sidebar (Transcript/Analysis) */}
                <div className="w-full md:w-1/3 lg:w-1/4 border-l border-white/10 bg-zinc-900 flex flex-col min-h-0">
                    <Tabs defaultValue="transcript" className="flex-1 flex flex-col min-h-0 overflow-hidden">
                        <div className="p-3 border-b border-white/5 flex-shrink-0">
                            <TabsList className="w-full grid grid-cols-3">
                                <TabsTrigger value="transcript" className="text-xs text-zinc-300 data-[state=active]:text-white">
                                    <FileText className="w-4 h-4 mr-2 text-current" /> Transcript
                                </TabsTrigger>
                                <TabsTrigger value="analysis" className="text-xs text-zinc-300 data-[state=active]:text-white">
                                    <Sparkles className="w-4 h-4 mr-2 text-current" /> Analysis
                                </TabsTrigger>
                                <TabsTrigger value="logs" className="text-xs text-zinc-300 data-[state=active]:text-white">
                                    <Terminal className="w-4 h-4 mr-2 text-current" /> Log
                                </TabsTrigger>
                            </TabsList>
                        </div>

                        <TabsContent value="transcript" className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0 mt-0 max-h-full">
                            {transcript?.segments ? (
                                transcript.segments.map((seg: any, idx: number) => {
                                    const isActive = currentTime >= seg.start && currentTime < seg.end;
                                    return (
                                        <div
                                            key={idx}
                                            className={cn(
                                                "cursor-pointer p-3 rounded-lg transition-all text-sm group",
                                                isActive ? "bg-blue-500/10 border border-blue-500/20" : "hover:bg-white/5 border border-transparent"
                                            )}
                                            onClick={() => jumpToTime(seg.start)}
                                        >
                                            <div className="flex justify-between text-xs text-zinc-500 mb-1 font-mono">
                                                <span className={cn(isActive && "text-blue-400 font-bold")}>{formatTime(seg.start)}</span>
                                            </div>
                                            <p className={cn("leading-relaxed", isActive ? "text-blue-100" : "text-zinc-300 group-hover:text-zinc-200")}>
                                                {seg.text}
                                            </p>
                                        </div>
                                    );
                                })
                            ) : (
                                <div className="text-center text-zinc-500 py-10">No transcript available</div>
                            )}
                        </TabsContent>

                        <TabsContent value="analysis" className="flex-1 overflow-y-auto p-4 min-h-0 mt-0 max-h-full">
                            {/* Render Analysis Markdown or Content */}
                            <div className="prose prose-invert prose-sm max-w-none">
                                {typeof analysis === 'object' ? (
                                    <pre className="whitespace-pre-wrap font-mono text-xs text-zinc-400 break-words">
                                        {JSON.stringify(analysis, null, 2)}
                                    </pre>
                                ) : (
                                    <div className="whitespace-pre-wrap break-words">{analysis || "No analysis available yet."}</div>
                                )}
                            </div>
                        </TabsContent>

                        <TabsContent value="logs" className="flex-1 overflow-hidden p-0 min-h-0 mt-0 max-h-full">
                            <ProgressTerminal videoId={video.id} status={video.status} />
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </div>
    );
}
