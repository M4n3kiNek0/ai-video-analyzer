import { NextRequest, NextResponse } from 'next/server';

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string; format: string }> }
) {
    const { id, format } = await params;

    if (!['pdf', 'zip'].includes(format)) {
        return NextResponse.json({ error: 'Invalid format' }, { status: 400 });
    }

    // Use localhost for local development, internal hostname for Docker
    const backendUrl = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    console.log(`[Export Proxy] Fetching from: ${backendUrl}/videos/${id}/export/${format}`);

    try {
        const response = await fetch(`${backendUrl}/videos/${id}/export/${format}`, {
            method: 'GET',
        });

        console.log(`[Export Proxy] Response status: ${response.status}`);
        console.log(`[Export Proxy] Response headers:`, Object.fromEntries(response.headers.entries()));

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[Export Proxy] Backend error:', errorText);
            return NextResponse.json(
                { error: 'Export failed', details: errorText },
                { status: response.status }
            );
        }

        const data = await response.arrayBuffer();
        console.log(`[Export Proxy] Received ${data.byteLength} bytes`);

        // Determine content type and filename based on format
        const contentType = format === 'pdf' ? 'application/pdf' : 'application/zip';
        const filename = `video_${id}_report.${format}`;

        return new NextResponse(data, {
            status: 200,
            headers: {
                'Content-Type': contentType,
                'Content-Disposition': `attachment; filename="${filename}"`,
                'Content-Length': data.byteLength.toString(),
            },
        });
    } catch (error) {
        console.error('[Export Proxy] Error:', error);
        return NextResponse.json({ error: 'Export failed', message: String(error) }, { status: 500 });
    }
}
