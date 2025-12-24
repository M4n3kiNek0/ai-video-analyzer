import { NextRequest, NextResponse } from 'next/server';

// Use internal Docker URL for server-side API routes (priority over public URL)
const API_URL = process.env.INTERNAL_API_URL || 'http://web:8000';

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        
        // Proxy to backend API
        const backendUrl = `${API_URL}/videos/${id}/export/zip`;
        console.log(`[API Proxy] Fetching ZIP from: ${backendUrl}`);
        
        const response = await fetch(backendUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/zip',
            },
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`[API Proxy] Backend error: ${response.status} - ${errorText}`);
            return NextResponse.json(
                { error: `Backend error: ${response.status}` },
                { status: response.status }
            );
        }

        // Get the ZIP blob
        const zipBlob = await response.blob();
        
        // Return the ZIP with appropriate headers
        return new NextResponse(zipBlob, {
            status: 200,
            headers: {
                'Content-Type': 'application/zip',
                'Content-Disposition': `attachment; filename="video_${id}_export.zip"`,
            },
        });
    } catch (error) {
        console.error('[API Proxy] ZIP export error:', error);
        return NextResponse.json(
            { error: 'Failed to export ZIP' },
            { status: 500 }
        );
    }
}

