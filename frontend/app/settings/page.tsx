import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Settings, Shield, User } from "lucide-react";

export default function SettingsPage() {
    return (
        <div className="p-8 max-w-4xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-white">Settings</h1>
                <p className="text-zinc-400 mt-1">Manage your application preferences.</p>
            </div>

            <Card className="bg-white/5 border-white/10">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <User className="w-5 h-5 text-blue-400" />
                        Account
                    </CardTitle>
                    <CardDescription>Manage your profile and authentication.</CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-zinc-400 text-sm">Authentication is coming in Phase 4.</p>
                </CardContent>
            </Card>

            <Card className="bg-white/5 border-white/10">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Shield className="w-5 h-5 text-green-400" />
                        API Configuration
                    </CardTitle>
                    <CardDescription>Configure AI providers and API keys.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-zinc-300">OpenAI API Key</label>
                        <input type="password" value="sk-........................" disabled className="w-full bg-black/40 border border-white/10 rounded px-3 py-2 text-zinc-500" />
                    </div>
                    <Button disabled variant="secondary">Save Changes</Button>
                </CardContent>
            </Card>
        </div>
    );
}
