import * as path from 'path';
import * as vscode from 'vscode';
import { BackendClient } from '../api/backendClient';
import { getCopybookPaths } from '../config/settings';

interface IndexResponse {
    jobId: string;
    status: string;
    programs: number;
    copybooks: number;
    jclJobs: number;
    errors: number;
    unresolvedCopybooks: number;
    graphNodes: number;
    graphEdges: number;
}

export function registerIndexWorkspace(
    _context: vscode.ExtensionContext,
    client: BackendClient,
    onIndexed: () => void
): vscode.Disposable {
    return vscode.commands.registerCommand(
        'cobol-cartography.indexWorkspace',
        async () => {
            const folders = vscode.workspace.workspaceFolders;
            if (!folders || folders.length === 0) {
                void vscode.window.showErrorMessage(
                    'COBOL Cartography: No workspace folder open.'
                );
                return;
            }

            const workspacePath = folders[0].uri.fsPath;
            const copybookPaths = getCopybookPaths().map(p =>
                path.isAbsolute(p) ? p : path.join(workspacePath, p)
            );

            await vscode.window.withProgress(
                {
                    location: vscode.ProgressLocation.Notification,
                    title: 'COBOL Cartography: Indexing…',
                    cancellable: false,
                },
                async (progress) => {
                    progress.report({ message: 'Scanning workspace…' });

                    try {
                        const result = await client.post<IndexResponse>(
                            '/api/index/workspace',
                            {
                                workspacePath,
                                copybookPaths,
                                sourceFormat: 'fixed',
                                incremental: false,
                            }
                        );

                        onIndexed();

                        void vscode.window.showInformationMessage(
                            `COBOL Cartography: Indexed ${result.programs} programs, ` +
                            `${result.copybooks} copybooks, ${result.jclJobs} JCL jobs — ` +
                            `${result.graphNodes} nodes, ${result.graphEdges} edges.`
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
