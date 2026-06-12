import * as vscode from 'vscode';
import { BackendClient } from '../api/backendClient';

interface TableImpactEntry {
    name: string;
    confidence: number;
}

interface TableImpact {
    table_name: string;
    readers: TableImpactEntry[];
    writers: TableImpactEntry[];
    updaters: TableImpactEntry[];
    deleters: TableImpactEntry[];
    associated_jobs: { name: string }[];
}

function esc(s: string): string {
    return s
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function accessBadge(type: 'READ' | 'WRITE' | 'UPDATE' | 'DELETE'): string {
    const colors: Record<string, string> = {
        READ: '#1a5c14', WRITE: '#0044a0', UPDATE: '#7d4000', DELETE: '#7a1a1a'
    };
    return `<span class="badge" style="background:${colors[type]}">${type}</span>`;
}

function entryList(entries: TableImpactEntry[], type: 'READ' | 'WRITE' | 'UPDATE' | 'DELETE'): string {
    if (entries.length === 0) {
        return '<p class="empty">Aucun</p>';
    }
    const items = entries.map(
        e => `<li>${esc(e.name)} ${accessBadge(type)}</li>`
    ).join('');
    return `<ul>${items}</ul>`;
}

function renderImpact(impact: TableImpact): string {
    const total =
        impact.readers.length +
        impact.writers.length +
        impact.updaters.length +
        impact.deleters.length;

    return `<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline';">
<style>
body{font-family:var(--vscode-font-family);color:var(--vscode-foreground);background:var(--vscode-editor-background);padding:20px;margin:0}
h1{font-size:1.3em;margin:0 0 4px}
.sub{color:var(--vscode-descriptionForeground);font-size:.85em;margin-bottom:16px}
.metrics{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}
.mc{background:var(--vscode-sideBar-background,#1e1e1e);border:1px solid var(--vscode-panel-border,#444);border-radius:4px;padding:10px 16px;text-align:center;min-width:72px}
.mv{font-size:1.6em;font-weight:700;line-height:1}
.ml{font-size:.72em;color:var(--vscode-descriptionForeground);margin-top:4px}
section{margin:16px 0}
h2{font-size:.9em;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--vscode-descriptionForeground);border-bottom:1px solid var(--vscode-panel-border,#444);padding-bottom:4px;margin:0 0 8px}
ul{margin:0;padding-left:18px}
li{margin:3px 0;font-size:.92em}
.badge{display:inline-block;font-size:.7em;padding:1px 5px;border-radius:3px;margin-left:5px;vertical-align:middle;font-weight:600;color:#fff}
.empty{color:var(--vscode-descriptionForeground);font-style:italic;margin:4px 0;font-size:.9em}
</style>
</head>
<body>
<h1>Impact — ${esc(impact.table_name)}</h1>
<div class="sub">Programmes et jobs accédant à cette table DB2</div>
<div class="metrics">
  <div class="mc"><div class="mv">${total}</div><div class="ml">Programmes</div></div>
  <div class="mc"><div class="mv">${impact.readers.length}</div><div class="ml">Lecteurs</div></div>
  <div class="mc"><div class="mv">${impact.writers.length}</div><div class="ml">Écrivains</div></div>
  <div class="mc"><div class="mv">${impact.updaters.length}</div><div class="ml">Mises à jour</div></div>
  <div class="mc"><div class="mv">${impact.deleters.length}</div><div class="ml">Suppressions</div></div>
  <div class="mc"><div class="mv">${impact.associated_jobs.length}</div><div class="ml">Jobs JCL</div></div>
</div>
<section>
  <h2>Programmes lecteurs (SELECT / READ)</h2>
  ${entryList(impact.readers, 'READ')}
</section>
<section>
  <h2>Programmes écrivains (INSERT / WRITE)</h2>
  ${entryList(impact.writers, 'WRITE')}
</section>
<section>
  <h2>Programmes modificateurs (UPDATE)</h2>
  ${entryList(impact.updaters, 'UPDATE')}
</section>
<section>
  <h2>Programmes suppresseurs (DELETE)</h2>
  ${entryList(impact.deleters, 'DELETE')}
</section>
<section>
  <h2>Jobs JCL associés</h2>
  ${impact.associated_jobs.length === 0
        ? '<p class="empty">Aucun job JCL n\'exécute un programme accédant à cette table</p>'
        : `<ul>${impact.associated_jobs.map(j => `<li>${esc(j.name)}</li>`).join('')}</ul>`}
</section>
</body>
</html>`;
}

function shellHtml(body: string): string {
    return `<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline';">
<style>body{font-family:var(--vscode-font-family);color:var(--vscode-foreground);background:var(--vscode-editor-background);padding:20px}
.err{color:var(--vscode-errorForeground)}</style>
</head><body>${body}</body></html>`;
}

export class TableImpactPanel {
    private static readonly viewType = 'cobol-cartography.tableImpact';
    private static readonly panels = new Map<string, TableImpactPanel>();

    private readonly disposables: vscode.Disposable[] = [];

    static async show(tableName: string, client: BackendClient): Promise<void> {
        const key = tableName.toUpperCase();
        const existing = TableImpactPanel.panels.get(key);
        if (existing) {
            existing.webviewPanel.reveal();
            return;
        }
        const panel = vscode.window.createWebviewPanel(
            TableImpactPanel.viewType,
            `Impact table : ${key}`,
            vscode.ViewColumn.One,
            { enableScripts: false }
        );
        new TableImpactPanel(panel, key, client);
    }

    private constructor(
        private readonly webviewPanel: vscode.WebviewPanel,
        private readonly tableName: string,
        private readonly client: BackendClient
    ) {
        TableImpactPanel.panels.set(tableName, this);
        this.webviewPanel.onDidDispose(
            () => {
                TableImpactPanel.panels.delete(this.tableName);
                this.dispose();
            },
            null,
            this.disposables
        );
        void this.loadAndRender();
    }

    private async loadAndRender(): Promise<void> {
        this.webviewPanel.webview.html = shellHtml(
            `<p>Analyse d'impact pour la table <strong>${esc(this.tableName)}</strong>…</p>`
        );
        try {
            const impact = await this.client.get<TableImpact>(
                `/api/impact/table/${encodeURIComponent(this.tableName)}`
            );
            this.webviewPanel.webview.html = renderImpact(impact);
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            this.webviewPanel.webview.html = shellHtml(
                `<h2 class="err">Erreur — ${esc(this.tableName)}</h2><p>${esc(msg)}</p>`
            );
        }
    }

    private dispose(): void {
        this.disposables.forEach(d => d.dispose());
        this.disposables.length = 0;
    }
}
