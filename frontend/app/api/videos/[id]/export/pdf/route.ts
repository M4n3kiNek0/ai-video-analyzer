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
        const backendUrl = `${API_URL}/videos/${id}/export/pdf`;
        console.log(`[API Proxy] Fetching PDF from: ${backendUrl}`);
        
        const response = await fetch(backendUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/pdf',
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

        // Get the PDF blob
        const pdfBlob = await response.blob();
        
        // Return the PDF with appropriate headers
        return new NextResponse(pdfBlob, {
            status: 200,
            headers: {
                'Content-Type': 'application/pdf',
                'Content-Disposition': `attachment; filename="video_${id}_report.pdf"`,
            },
        });
    } catch (error) {
        console.error('[API Proxy] PDF export error:', error);
        return NextResponse.json(
            { error: 'Failed to export PDF' },
            { status: 500 }
        );
    }
}

