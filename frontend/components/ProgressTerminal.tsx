"use client";

import { useEffect, useRef, useState } from "react";
import { Terminal } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";

interface LogEntry {
    id: number;
    timestamp: string;
    level: string;
    message: string;
}

interface ProgressTerminalProps {
    videoId: number;
    status: string;
}

export function ProgressTerminal({ videoId, status }: ProgressTerminalProps) {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [polling, setPolling] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    // Poll for logs
    useEffect(() => {
        let interval: NodeJS.Timeout;

        const fetchLogs = async () => {
            try {
                const response = await api.get(`/videos/${videoId}/logs`);
                setLogs(response.data);
            } catch (err) {
                console.error("Failed to fetch logs", err);
            }
        };

        // Fetch immediately
        fetchLogs();

        // Start polling if processing
        if (status === 'processing' || status === 'uploading') {
            setPolling(true);
            interval = setInterval(fetchLogs, 2000); // 2s polling
        } else {
            setPolling(false);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [videoId, status]);

    // Auto-scroll to bottom
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    return (
        <div className="flex flex-col h-full max-h-full bg-black border border-white/10 rounded-lg overflow-hidden font-mono text-xs">
            {/* Header */}
            <div className="flex items-center justify-between px-3 py-2 bg-zinc-900 border-b border-white/10 flex-shrink-0">
                <div className="flex items-center gap-2 text-zinc-400">
                    <Terminal className="w-3 h-3" />
                    <span className="font-semibold">Processing Logs</span>
                </div>
                <div className="flex items-center gap-2">
                    {polling && (
                        <span className="flex h-2 w-2 relative">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                        </span>
                    )}
                    <span className={cn(
                        "text-[10px] px-1.5 py-0.5 rounded",
                        status === 'completed' ? "bg-green-500/10 text-green-400" :
                            status === 'failed' ? "bg-red-500/10 text-red-400" :
                                "bg-blue-500/10 text-blue-400"
                    )}>
                        {status.toUpperCase()}
                    </span>
                </div>
            </div>

            {/* Terminal Window */}
            <ScrollArea className="flex-1 p-3 bg-black/95 min-h-0 overflow-auto">
                <div className="space-y-1">
                    {logs.length === 0 ? (
                        <div className="text-zinc-600 italic">Waiting for logs...</div>
                    ) : (
                        logs.map((log) => (
                            <div key={log.id} className="flex gap-2">
                                <span className="text-zinc-600 shrink-0">
                                    [{new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}]
                                </span>
                                <span className={cn(
                                    "break-all",
                                    log.level === 'ERROR' ? "text-red-400 font-bold" :
                                        log.level === 'WARNING' ? "text-yellow-400" :
                                            log.level === 'SUCCESS' ? "text-green-400 font-bold" :
                                                "text-zinc-300"
                                )}>
                                    {log.level !== 'INFO' && <span className="mr-1">[{log.level}]</span>}
                                    {log.message}
                                </span>
                            </div>
                        ))
                    )}
                    <div ref={bottomRef} />
                </div>
            </ScrollArea>
        </div>
    );
}
