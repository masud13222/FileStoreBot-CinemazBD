const cors_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, HEAD, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
};

const SERVICE_ACCOUNTS = [
    // Add your service account details here
];

let currentAccountIndex = 0;
const LINK_VALIDITY_DURATION = 6 * 60 * 60 * 1000; // 6 hours in milliseconds

function base64UrlEncode(str) {
    return btoa(str)
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');
}

function base64UrlDecode(str) {
    str = str.replace(/-/g, '+').replace(/_/g, '/');
    while (str.length % 4) {
        str += '=';
    }
    return atob(str);
}

async function handleRequest(request) {
    if (request.method === "OPTIONS") {
        return new Response(null, { headers: cors_headers });
    }

    const url = new URL(request.url);
    const path = url.pathname.slice(1); // Remove leading slash

    if (path.startsWith('gdirect/')) {
        const encodedParts = path.split('gdirect/')[1];
        if (!encodedParts) {
            return new Response('File ID or timestamp not found', { status: 404 });
        }

        const [encodedDriveId, encodedTimestamp] = encodedParts.split('/');
        if (!encodedDriveId || !encodedTimestamp) {
            return new Response('File ID or timestamp not found', { status: 404 });
        }

        // Decode driveId and timestamp
        const driveId = base64UrlDecode(encodedDriveId);
        const timestamp = parseInt(base64UrlDecode(encodedTimestamp));

        // Validate timestamp
        const currentTime = Date.now();
        if (currentTime - timestamp > LINK_VALIDITY_DURATION) {
            return new Response('Link has expired', { status: 403 });
        }

        return await handleDriveDownload(driveId, request);
    }

    // Existing bot redirect logic
    const BOT_USERNAME = "autoforwardbd_bot";
    if (path.startsWith('batch_')) {
        return Response.redirect(`https://t.me/${BOT_USERNAME}?start=${path}`, 301);
    }

    // Ensure no leading slash in the start parameter
    const cleanPath = path.replace(/^\//, '');
    return Response.redirect(`https://t.me/${BOT_USERNAME}?start=${cleanPath}`, 301);
}

async function handleDriveDownload(driveId, request) {
    try {
        const credentials = SERVICE_ACCOUNTS[currentAccountIndex];
        const accessToken = await getAccessToken(credentials);

        const metadataUrl = `https://www.googleapis.com/drive/v3/files/${driveId}?supportsAllDrives=true&fields=name,mimeType,size`;
        const metadataResponse = await fetch(metadataUrl, {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
            }
        });

        if (!metadataResponse.ok) {
            if (metadataResponse.status === 429) {
                console.log("Quota reached for current account, switching to next account...");
                currentAccountIndex = (currentAccountIndex + 1) % SERVICE_ACCOUNTS.length;
                return await handleDriveDownload(driveId, request);
            }
            return new Response(`Failed to get file metadata: ${metadataResponse.status}`, { status: metadataResponse.status });
        }

        const metadata = await metadataResponse.json();

        const downloadUrl = `https://www.googleapis.com/drive/v3/files/${driveId}?alt=media&supportsAllDrives=true`;

        const headers = {
            'Authorization': `Bearer ${accessToken}`,
        };

        const rangeHeader = request.headers.get('Range');
        if (rangeHeader) {
            headers['Range'] = rangeHeader;
        }

        const response = await fetch(downloadUrl, { headers });

        if (!response.ok && response.status !== 206) {
            if (response.status === 429) {
                console.log("Quota reached for current account, switching to next account...");
                currentAccountIndex = (currentAccountIndex + 1) % SERVICE_ACCOUNTS.length;
                return await handleDriveDownload(driveId, request);
            }
            return new Response(`Drive API error: ${response.status}`, { status: response.status });
        }

        const responseHeaders = {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': metadata.mimeType || 'application/octet-stream',
            'Content-Disposition': `attachment; filename="${encodeURIComponent(metadata.name)}"`,
            'Accept-Ranges': 'bytes',
            'Content-Length': metadata.size
        };

        if (response.status === 206) {
            responseHeaders['Content-Range'] = response.headers.get('Content-Range');
        }

        return new Response(response.body, {
            status: response.status,
            headers: responseHeaders
        });
    } catch (err) {
        return new Response(err.message, { status: 500 });
    }
}

addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request));
});

async function getAccessToken(credentials) {
    const header = {
        alg: 'RS256',
        typ: 'JWT'
    };

    const now = Math.floor(Date.now() / 1000);
    const claim = {
        iss: credentials.client_email,
        scope: 'https://www.googleapis.com/auth/drive.readonly',
        aud: 'https://oauth2.googleapis.com/token',
        exp: now + 3600,
        iat: now
    };

    function base64UrlEncode(str) {
        return btoa(str)
            .replace(/\+/g, '-')
            .replace(/\//g, '_')
            .replace(/=+$/, '');
    }

    const encodedHeader = base64UrlEncode(JSON.stringify(header));
    const encodedClaim = base64UrlEncode(JSON.stringify(claim));
    const signatureInput = `${encodedHeader}.${encodedClaim}`;

    const pemContents = credentials.private_key
        .replace('-----BEGIN PRIVATE KEY-----\n', '')
        .replace('\n-----END PRIVATE KEY-----\n', '')
        .replace(/\s/g, '');

    const binaryDer = str2ab(atob(pemContents));

    const cryptoKey = await crypto.subtle.importKey(
        'pkcs8',
        binaryDer,
        {
            name: 'RSASSA-PKCS1-v1_5',
            hash: 'SHA-256',
        },
        false,
        ['sign']
    );

    const signature = await crypto.subtle.sign(
        'RSASSA-PKCS1-v1_5',
        cryptoKey,
        new TextEncoder().encode(signatureInput)
    );

    const signatureBytes = new Uint8Array(signature);
    let binary = '';
    for (let i = 0; i < signatureBytes.length; i++) {
        binary += String.fromCharCode(signatureBytes[i]);
    }
    const encodedSignature = base64UrlEncode(binary);

    const jwt = `${encodedHeader}.${encodedClaim}.${encodedSignature}`;

    const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}`
    });

    const data = await tokenResponse.json();

    if (!data.access_token) {
        throw new Error('Failed to get access token: ' + JSON.stringify(data));
    }

    return data.access_token;
}

function str2ab(str) {
    const buf = new ArrayBuffer(str.length);
    const bufView = new Uint8Array(buf);
    for (let i = 0, strLen = str.length; i < strLen; i++) {
        bufView[i] = str.charCodeAt(i);
    }
    return buf;
} 




