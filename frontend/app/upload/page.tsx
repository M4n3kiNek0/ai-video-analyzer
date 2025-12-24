"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { UploadCloud, FileVideo, FileAudio, X, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function UploadPage() {
    const router = useRouter();
    const [dragActive, setDragActive] = useState(false);
    const [file, setFile] = useState<File | null>(null);
    const [context, setContext] = useState("");
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    };

    const dirname = (path: string) => path.replace(/\\/g, '/').replace(/\/[^/]*$/, '');

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    };

    const handleFile = (file: File) => {
        const isVideo = file.type.startsWith("video/");
        const isAudio = file.type.startsWith("audio/");

        if (isVideo || isAudio) {
            setFile(file);
            setError(null);
        } else {
            setError("Please upload a supported video or audio file.");
        }
    };

    const handleSubmit = async () => {
        if (!file) return;

        try {
            setUploading(true);
            setError(null);

            const formData = new FormData();
            formData.append("file", file);
            if (context) formData.append("context", context);

            // Determine endpoint based on file type
            const endpoint = file.type.startsWith("audio/") ? "/upload-audio" : "/upload";

            await api.post(endpoint, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            // Redirect to dashboard
            router.push("/");
            router.refresh();

        } catch (err: any) {
            console.error("Upload failed:", err);
            setError(err.response?.data?.detail || "Upload failed. Please try again.");
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="p-8 max-w-4xl mx-auto h-[calc(100vh-2rem)] flex items-center justify-center">
            <Card className="w-full bg-white/5 border-white/10 backdrop-blur-xl">
                <CardHeader>
                    <CardTitle className="text-3xl bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-violet-500">
                        Upload Media
                    </CardTitle>
                    <CardDescription className="text-zinc-400">
                        Upload video or audio files for AI analysis.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div
                        className={cn(
                            "relative flex flex-col items-center justify-center w-full h-64 rounded-xl border-2 border-dashed transition-all duration-300",
                            dragActive
                                ? "border-blue-500 bg-blue-500/10"
                                : "border-white/20 bg-black/20 hover:bg-black/40 hover:border-white/30",
                            file && "border-green-500/50 bg-green-500/5"
                        )}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                    >
                        {!file ? (
                            <>
                                <UploadCloud className="w-16 h-16 text-zinc-500 mb-4 group-hover:text-blue-400 transition-colors" />
                                <p className="text-zinc-300 font-medium">
                                    Drag & drop or <span className="text-blue-400">browse</span>
                                </p>
                                <p className="text-zinc-500 text-sm mt-2">
                                    MP4, MOV, MP3, WAV supported
                                </p>
                                <input
                                    type="file"
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                    onChange={handleChange}
                                    accept="video/*,audio/*"
                                    disabled={uploading}
                                />
                            </>
                        ) : (
                            <div className="flex flex-col items-center animate-in fade-in zoom-in duration-300">
                                {file.type.startsWith('video') ? (
                                    <FileVideo className="w-16 h-16 text-blue-500 mb-4" />
                                ) : (
                                    <FileAudio className="w-16 h-16 text-violet-500 mb-4" />
                                )}
                                <p className="text-white font-medium text-lg">{file.name}</p>
                                <p className="text-zinc-400 text-sm mt-1">
                                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                                </p>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="mt-4 text-zinc-400 hover:text-red-400"
                                    onClick={() => setFile(null)}
                                    disabled={uploading}
                                >
                                    <X className="w-4 h-4 mr-2" />
                                    Remove
                                </Button>
                            </div>
                        )}
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-zinc-300">
                            Context (Optional)
                        </label>
                        <textarea
                            className="w-full h-24 bg-black/40 border border-white/10 rounded-lg p-3 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all resize-none"
                            placeholder="Describe the content to help the AI (e.g. 'A university lecture about quantum mechanics')"
                            value={context}
                            onChange={(e) => setContext(e.target.value)}
                            disabled={uploading}
                        />
                    </div>

                    {error && (
                        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    <div className="flex justify-end pt-4">
                        <Button
                            variant="gradient"
                            size="lg"
                            className="w-full md:w-auto min-w-[150px]"
                            onClick={handleSubmit}
                            disabled={!file || uploading}
                        >
                            {uploading ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Uploading...
                                </>
                            ) : (
                                "Start Analysis"
                            )}
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
