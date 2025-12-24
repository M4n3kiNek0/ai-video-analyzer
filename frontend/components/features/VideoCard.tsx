import { Card, CardFooter, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Play, Clock, FileText, Trash2, RotateCcw } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface VideoCardProps {
    id: number;
    title: string;
    duration: number;
    status: string;
    createdAt: string;
    thumbnailUrl?: string;
    onDelete?: (id: number) => void;
    onRetry?: (id: number) => void;
}

export function VideoCard({
    id,
    title,
    duration,
    status,
    createdAt,
    thumbnailUrl,
    onDelete,
    onRetry
}: VideoCardProps) {
    const [imageError, setImageError] = useState(false);
    const [prevThumbnailUrl, setPrevThumbnailUrl] = useState(thumbnailUrl);

    if (thumbnailUrl !== prevThumbnailUrl) {
        setPrevThumbnailUrl(thumbnailUrl);
        setImageError(false);
    }
    
    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const statusColor = {
        pending: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
        processing: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
        completed: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
        failed: "bg-red-500/10 text-red-500 hover:bg-red-500/20",
    }[status] || "bg-gray-500/10 text-gray-500";

    const showPlaceholder = !thumbnailUrl || imageError;

    return (
        <Card className="group relative overflow-hidden transition-all hover:scale-[1.02] hover:shadow-lg border-white/5 bg-white/2">
            <Link href={`/videos/${id}`} className="absolute inset-0 z-10" />

            <div className="relative aspect-video w-full bg-zinc-900 overflow-hidden">
                {thumbnailUrl && !imageError && (
                    <img 
                        src={thumbnailUrl} 
                        alt={title} 
                        className="w-full h-full object-cover transition-transform group-hover:scale-105"
                        onError={() => setImageError(true)}
                    />
                )}
                {showPlaceholder && (
                    <div className="w-full h-full flex items-center justify-center bg-linear-to-br from-zinc-800 to-zinc-900">
                        <Play className="w-12 h-12 text-white/20" />
                    </div>
                )}
                <div className="absolute bottom-2 right-2 px-2 py-1 rounded bg-black/60 backdrop-blur-sm text-xs text-white font-medium flex items-center">
                    <Clock className="w-3 h-3 mr-1" />
                    {formatDuration(duration)}
                </div>
            </div>

            <CardHeader className="p-4 pb-2">
                <div className="flex justify-between items-start">
                    <h3 className="font-semibold text-lg text-white line-clamp-1 group-hover:text-blue-400 transition-colors">
                        {title}
                    </h3>
                    <span className={cn("text-xs px-2 py-1 rounded-full font-medium uppercase tracking-wider", statusColor)}>
                        {status}
                    </span>
                </div>
                <p className="text-xs text-zinc-500 mt-1">
                    {new Date(createdAt).toLocaleDateString()}
                </p>
            </CardHeader>

            <CardFooter className="p-4 pt-2 flex justify-between items-center relative z-20">
                <div className="flex space-x-2">
                    <Link href={`/videos/${id}`} passHref>
                        <Button size="sm" variant="ghost" className="h-8 text-zinc-400 hover:text-white">
                            <FileText className="w-4 h-4 mr-1" />
                            View
                        </Button>
                    </Link>
                </div>
                <div className="flex space-x-1">
                    {/* Show Retry button for failed videos */}
                    {status === 'failed' && onRetry && (
                        <Button
                            size="icon"
                            variant="ghost"
                            className="h-8 w-8 text-zinc-500 hover:text-blue-500 hover:bg-blue-500/10"
                            onClick={(e) => {
                                e.stopPropagation();
                                e.preventDefault();
                                onRetry(id);
                            }}
                        >
                            <RotateCcw className="w-4 h-4" />
                        </Button>
                    )}
                    {onDelete && (
                        <Button
                            size="icon"
                            variant="ghost"
                            className="h-8 w-8 text-zinc-500 hover:text-red-500 hover:bg-red-500/10"
                            onClick={(e) => {
                                e.stopPropagation();
                                e.preventDefault();
                                onDelete(id);
                            }}
                        >
                            <Trash2 className="w-4 h-4" />
                        </Button>
                    )}
                </div>
            </CardFooter>
        </Card>
    );
}
