import * as vscode from 'vscode';
import { getBackendUrl, getApiKey } from './config/settings';
import { BackendClient } from './api/backendClient';
import { registerIndexWorkspace } from './commands/indexWorkspace';

export async function activate(context: vscode.ExtensionContext): Promise<void> {
    const backendUrl = getBackendUrl();
    const apiKey = await getApiKey(context);
    const client = new BackendClient(backendUrl, apiKey);

    context.subscriptions.push(registerIndexWorkspace(context, client));

    // Check backend health on activation (non-blocking, log only)
    client.get<{ status: string }>('/api/health').then(
        () => console.log('[cobol-cartography] Backend connected'),
        (err) => console.warn('[cobol-cartography] Backend not reachable:', err)
    );
}

export function deactivate(): void {}
