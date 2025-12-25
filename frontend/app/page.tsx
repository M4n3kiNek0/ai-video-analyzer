"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { VideoCard } from "@/components/features/VideoCard";
import { Plus, Search, Filter } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Video } from "@/types";
import { useDebounce } from "@/lib/hooks";

export default function DashboardPage() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const debouncedSearch = useDebounce(search, 400);

  const fetchVideos = async (query?: string, status?: string) => {
    try {
      setLoading(true);
      console.log('[Dashboard] Fetching videos from API...');
      console.log('[Dashboard] API base URL:', api.defaults.baseURL);
      
      const response = await api.get('/videos', {
        params: {
          ...(query ? { q: query } : {}),
          ...(status ? { status } : {}),
        },
      });
      console.log('[Dashboard] API Response:', response.data);
      
      const data = response.data;
      // Backend returns { videos: [...] } or { items: [...] } or just [...]
      const videosList = data.videos || data.items || (Array.isArray(data) ? data : []);
      console.log('[Dashboard] Videos list:', videosList);
      
      setVideos(Array.isArray(videosList) ? videosList : []);
      setError(null);
    } catch (err: any) {
      console.error("[Dashboard] Failed to fetch videos:", err);
      console.error("[Dashboard] Error details:", err.response?.status, err.response?.data, err.message);
      setError(`Failed to load videos: ${err.message || 'Unknown error'}. Is the backend running on port 8000?`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVideos(debouncedSearch, statusFilter);

    // Poll for updates every 10 seconds if there are processing videos
    const interval = setInterval(() => {
      fetchVideos(debouncedSearch, statusFilter);
    }, 10000);

    return () => clearInterval(interval);
  }, [debouncedSearch, statusFilter]);

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this video?")) return;
    try {
      await api.delete(`/videos/${id}`);
      setVideos(prev => prev.filter(v => v.id !== id));
    } catch (err) {
      alert("Failed to delete video");
    }
  };

  const handleRetry = async (id: number) => {
    try {
      await api.post(`/videos/${id}/retry`);
      // Update status locally
      setVideos(prev => prev.map(v =>
        v.id === id ? { ...v, status: 'processing' as const } : v
      ));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to retry analysis");
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-zinc-400">
            My Library
          </h1>
          <p className="text-zinc-400 mt-1">
            Manage your uploaded videos and analysis.
          </p>
        </div>
        <Link href="/upload">
          <Button variant="gradient" size="lg" className="shadow-lg shadow-blue-900/20">
            <Plus className="w-5 h-5 mr-2" />
            Upload New
          </Button>
        </Link>
      </div>

      {/* Filters & Search - Visual only for now */}
      <div className="flex gap-4 items-center bg-white/5 p-2 rounded-xl border border-white/10 backdrop-blur-sm">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            type="text"
            placeholder="Search videos..."
            className="w-full bg-transparent border-none text-sm text-white placeholder:text-zinc-500 focus:outline-none pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="h-6 w-px bg-white/10" />
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-zinc-500" />
          <select
            className="bg-transparent border border-white/10 rounded-md text-sm text-white px-2 py-1 focus:outline-none"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="uploading">Uploading</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Content */}
      {loading && videos.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="aspect-video rounded-xl bg-white/5 animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-20 text-red-400 bg-red-500/5 rounded-2xl border border-red-500/10">
          <p>{error}</p>
          <Button variant="outline" className="mt-4" onClick={fetchVideos}>Retry</Button>
        </div>
      ) : videos.length === 0 ? (
        <div className="text-center py-32 bg-white/5 rounded-3xl border border-dashed border-white/10">
          <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4">
            <VideoCardIcon className="w-8 h-8 text-zinc-500" />
          </div>
          <h3 className="text-xl font-medium text-white">No videos yet</h3>
          <p className="text-zinc-400 mt-2 max-w-sm mx-auto">
            Upload a video to get started with AI-powered analysis and transcription.
          </p>
          <Link href="/upload">
            <Button variant="secondary" className="mt-6">
              Upload your first video
            </Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {videos.map((video) => (
            <VideoCard
              key={video.id}
              id={video.id}
              title={video.filename}
              duration={video.duration}
              status={video.status}
              createdAt={video.created_at}
              thumbnailUrl={video.thumbnail_url}
              onDelete={handleDelete}
              onRetry={handleRetry}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function VideoCardIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M15 10l5 5-5 5" />
      <path d="M4 4v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4" />
    </svg>
  )
}
