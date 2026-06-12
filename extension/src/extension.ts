import * as vscode from 'vscode';
import { getBackendUrl, getApiKey } from './config/settings';
import { BackendClient } from './api/backendClient';
import { registerIndexWorkspace } from './commands/indexWorkspace';
import { InventoryTreeProvider } from './views/inventoryTreeProvider';
import { ProgramSheetPanel } from './views/programSheetPanel';
import { CopybookImpactPanel } from './views/copybookImpactPanel';
import { ExplainProgramPanel } from './views/explainProgramPanel';
import { GraphViewPanel } from './views/graphViewPanel';
import { TableImpactPanel } from './views/tableImpactPanel';
import { JobProgramsPanel } from './views/jobProgramsPanel';

export async function activate(context: vscode.ExtensionContext): Promise<void> {
    const backendUrl = getBackendUrl();
    const apiKey = await getApiKey(context);
    const client = new BackendClient(backendUrl, apiKey);

    const inventoryProvider = new InventoryTreeProvider(client);
    const treeView = vscode.window.createTreeView(
        'cobol-cartography.inventory',
        { treeDataProvider: inventoryProvider, showCollapseAll: true }
    );

    const refreshCmd = vscode.commands.registerCommand(
        'cobol-cartography.refreshInventory',
        () => inventoryProvider.refresh()
    );

    const showSheetCmd = vscode.commands.registerCommand(
        'cobol-cartography.showProgramSheet',
        async (item?: unknown) => {
            let programName: string | undefined;
            if (
                item &&
                typeof item === 'object' &&
                'programName' in item &&
                typeof (item as { programName: unknown }).programName === 'string'
            ) {
                programName = (item as { programName: string }).programName;
            } else {
                programName = await vscode.window.showInputBox({
                    prompt: 'Nom du programme COBOL',
                    placeHolder: 'BNKMENU',
                });
            }
            if (programName) {
                await ProgramSheetPanel.show(programName.toUpperCase(), client);
            }
        }
    );

    const explainCmd = vscode.commands.registerCommand(
        'cobol-cartography.explainProgram',
        async (item?: unknown) => {
            let programName: string | undefined;
            if (
                item &&
                typeof item === 'object' &&
                'programName' in item &&
                typeof (item as { programName: unknown }).programName === 'string'
            ) {
                programName = (item as { programName: string }).programName;
            } else {
                programName = await vscode.window.showInputBox({
                    prompt: 'Nom du programme à expliquer',
                    placeHolder: 'BNKMENU',
                });
            }
            if (programName) {
                await ExplainProgramPanel.show(programName.toUpperCase(), client, context);
            }
        }
    );

    const analyzeImpactCmd = vscode.commands.registerCommand(
        'cobol-cartography.analyzeCopybookImpact',
        async (item?: unknown) => {
            let copybookName: string | undefined;
            if (
                item &&
                typeof item === 'object' &&
                'copybookName' in item &&
                typeof (item as { copybookName: unknown }).copybookName === 'string'
            ) {
                copybookName = (item as { copybookName: string }).copybookName;
            } else {
                copybookName = await vscode.window.showInputBox({
                    prompt: 'Nom du copybook COBOL',
                    placeHolder: 'ACCOUNT',
                });
            }
            if (copybookName) {
                await CopybookImpactPanel.show(copybookName.toUpperCase(), client);
            }
        }
    );

    const showGraphCmd = vscode.commands.registerCommand(
        'cobol-cartography.showGraphView',
        () => GraphViewPanel.show(client)
    );

    const showJobProgramsCmd = vscode.commands.registerCommand(
        'cobol-cartography.showJobPrograms',
        async (item?: unknown) => {
            let jobName: string | undefined;
            if (
                item &&
                typeof item === 'object' &&
                'jclJobName' in item &&
                typeof (item as { jclJobName: unknown }).jclJobName === 'string'
            ) {
                jobName = (item as { jclJobName: string }).jclJobName;
            } else {
                jobName = await vscode.window.showInputBox({
                    prompt: 'Nom du job JCL',
                    placeHolder: 'BATCHJOB',
                });
            }
            if (jobName) {
                await JobProgramsPanel.show(jobName.toUpperCase(), client);
            }
        }
    );

    const analyzeTableImpactCmd = vscode.commands.registerCommand(
        'cobol-cartography.analyzeTableImpact',
        async () => {
            const tableName = await vscode.window.showInputBox({
                prompt: 'Nom de la table DB2',
                placeHolder: 'CUSTOMER',
            });
            if (tableName) {
                await TableImpactPanel.show(tableName.toUpperCase(), client);
            }
        }
    );

    context.subscriptions.push(
        treeView,
        refreshCmd,
        showSheetCmd,
        explainCmd,
        analyzeImpactCmd,
        showGraphCmd,
        showJobProgramsCmd,
        analyzeTableImpactCmd,
        registerIndexWorkspace(context, client, () => inventoryProvider.refresh())
    );

    client.get<{ status: string }>('/api/health').then(
        () => console.log('[cobol-cartography] Backend connected'),
        (err) => console.warn('[cobol-cartography] Backend not reachable:', err)
    );
}

export function deactivate(): void {}
