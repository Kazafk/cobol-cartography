import * as vscode from 'vscode';
import { BackendClient } from '../api/backendClient';

/**
 * Registers the `cobol-cartography.indexWorkspace` command.
 *
 * The command shows a progress notification while it contacts the backend
 * health endpoint. Full indexing logic will be added in a later task.
 *
 * @param context - Extension context, kept for future disposable management.
 * @param client  - Pre-configured backend HTTP client.
 * @returns A Disposable that can be added to context.subscriptions.
 */
export function registerIndexWorkspace(
    context: vscode.ExtensionContext,
    client: BackendClient
): vscode.Disposable {
    // context is accepted for API consistency and future use (e.g. storing
    // state, registering additional disposables inside the command).
    void context;

    return vscode.commands.registerCommand(
        'cobol-cartography.indexWorkspace',
        async () => {
            await vscode.window.withProgress(
                {
                    location: vscode.ProgressLocation.Notification,
                    title: 'COBOL Cartography: Indexing…',
                    cancellable: false,
                },
                async (progress) => {
                    progress.report({ message: 'Connecting to backend…' });

                    try {
                        await client.get('/api/health');
                        void vscode.window.showInformationMessage(
                            'Index Workspace: connected to backend (not yet implemented)'
                        );
                    } catch (err) {
                        const message =
                            err instanceof Error ? err.message : String(err);
                        void vscode.window.showErrorMessage(
                            `COBOL Cartography: ${message}`
                        );
                    }
                }
            );
        }
    );
}
