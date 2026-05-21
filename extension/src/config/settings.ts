import * as vscode from 'vscode';

/**
 * Reads the backend URL from VS Code workspace configuration.
 * Falls back to http://localhost:8000 if not configured.
 *
 * Naming convention note: VS Code configuration keys use camelCase prefixes
 * (cobolCartography.backendUrl as declared in package.json contributes.configuration),
 * while the extension ID and SecretStorage keys use kebab-case (cobol-cartography).
 * Both follow VS Code conventions for their respective domains.
 */
export function getBackendUrl(): string {
    const config = vscode.workspace.getConfiguration('cobolCartography');
    return config.get<string>('backendUrl', 'http://localhost:8000');
}

/**
 * Reads the API key from VS Code SecretStorage.
 * Returns undefined if no key has been stored.
 *
 * IMPORTANT: The API key is intentionally never stored in workspace
 * configuration — only in SecretStorage — to prevent accidental exposure
 * in settings.json files committed to source control.
 */
export async function getApiKey(
    context: vscode.ExtensionContext
): Promise<string | undefined> {
    return context.secrets.get('cobol-cartography.apiKey');
}
