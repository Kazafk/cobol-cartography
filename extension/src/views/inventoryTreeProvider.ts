import * as vscode from 'vscode';
import { BackendClient } from '../api/backendClient';

interface InventoryFile {
    path: string;
    relative_path: string;
    kind: string;
    size_bytes: number;
    sha256: string;
}

class CategoryItem extends vscode.TreeItem {
    constructor(
        label: string,
        public readonly endpoint: string
    ) {
        super(label, vscode.TreeItemCollapsibleState.Collapsed);
        this.iconPath = new vscode.ThemeIcon('folder');
        this.contextValue = 'cobol-category';
    }
}

export class FileItem extends vscode.TreeItem {
    readonly programName: string | undefined;
    readonly copybookName: string | undefined;
    readonly jclJobName: string | undefined;

    constructor(file: InventoryFile) {
        super(file.relative_path, vscode.TreeItemCollapsibleState.None);
        this.resourceUri = vscode.Uri.file(file.path);
        this.tooltip = file.path;
        this.command = {
            command: 'vscode.open',
            title: 'Open File',
            arguments: [vscode.Uri.file(file.path)],
        };

        const basename = file.relative_path.replace(/\\/g, '/').split('/').pop() ?? file.relative_path;
        const stem = basename.replace(/\.[^.]+$/, '').toUpperCase();

        if (file.kind === 'program') {
            this.contextValue = 'cobol-file-program';
            this.programName = stem;
        } else if (file.kind === 'copybook') {
            this.contextValue = 'cobol-file-copybook';
            this.copybookName = stem;
        } else {
            this.contextValue = 'cobol-file-jcl';
            this.jclJobName = stem;
        }
    }
}

type InventoryEntry = CategoryItem | FileItem;

export class InventoryTreeProvider
    implements vscode.TreeDataProvider<InventoryEntry>
{
    private readonly _onDidChangeTreeData =
        new vscode.EventEmitter<InventoryEntry | undefined | null | void>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private readonly categories: CategoryItem[] = [
        new CategoryItem('Programs', '/api/inventory/programs'),
        new CategoryItem('Copybooks', '/api/inventory/copybooks'),
        new CategoryItem('JCL Jobs', '/api/inventory/jobs'),
    ];

    constructor(private readonly client: BackendClient) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: InventoryEntry): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: InventoryEntry): Promise<InventoryEntry[]> {
        if (!element) {
            return this.categories;
        }
        if (element instanceof CategoryItem) {
            try {
                const files = await this.client.get<InventoryFile[]>(
                    element.endpoint
                );
                return files.map(f => new FileItem(f));
            } catch {
                return [];
            }
        }
        return [];
    }
}
