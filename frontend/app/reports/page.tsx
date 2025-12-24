import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { PieChart, BarChart } from "lucide-react";

export default function ReportsPage() {
    return (
        <div className="p-8 max-w-7xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-white">Reports & Analytics</h1>
                <p className="text-zinc-400 mt-1">Insights across your video library (Coming Soon).</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <Card className="bg-white/5 border-white/10">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <PieChart className="w-5 h-5 text-blue-400" />
                            Content Breakdown
                        </CardTitle>
                        <CardDescription>Distribution of video topics</CardDescription>
                    </CardHeader>
                    <CardContent className="h-64 flex items-center justify-center text-zinc-500 bg-black/20 rounded-lg m-6">
                        Placeholder Chart
                    </CardContent>
                </Card>
                <Card className="bg-white/5 border-white/10">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <BarChart className="w-5 h-5 text-purple-400" />
                            Processing Metrics
                        </CardTitle>
                        <CardDescription>Average processing time per minute of video</CardDescription>
                    </CardHeader>
                    <CardContent className="h-64 flex items-center justify-center text-zinc-500 bg-black/20 rounded-lg m-6">
                        Placeholder Chart
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
