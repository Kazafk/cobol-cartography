import * as vscode from 'vscode';
import { BackendClient } from '../api/backendClient';

interface SheetMetrics {
    copybooks_included: number;
    programs_called: number;
    tables_accessed: number;
    called_by_count: number;
    executed_by_jobs: number;
}

interface ProgramCall {
    name: string;
    relation: string;
    line: number | null;
}

interface TableAccess {
    name: string;
    access: string;
}

interface JobExecution {
    job: string;
    step: string;
}

interface ProgramSheet {
    name: string;
    path: string | null;
    size_bytes: number | null;
    metrics: SheetMetrics;
    copybooks: string[];
    calls: ProgramCall[];
    called_by: ProgramCall[];
    tables: TableAccess[];
    executed_by: JobExecution[];
}

function esc(s: string): string {
    return s
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function formatBytes(bytes: number | null): string {
    if (bytes === null) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
}

function renderRelation(rel: string): string {
    const map: Record<string, string> = {
        CALLS_PROGRAM: 'CALL',
        CICS_LINKS_PROGRAM: 'CICS LINK',
        CICS_XCTLS_PROGRAM: 'CICS XCTL',
    };
    return map[rel] ?? rel;
}

function listOrEmpty(html: string, empty: string): string {
    return html || `<p class="empty">${empty}</p>`;
}

function renderSheet(sheet: ProgramSheet): string {
    const sizeStr = sheet.size_bytes ? ` — ${formatBytes(sheet.size_bytes)}` : '';
    const pathStr = sheet.path ? esc(sheet.path) : '<em>path inconnu</em>';

    const m = sheet.metrics;
    const metricCards = (
        [
            [m.copybooks_included, 'Copybooks'],
            [m.programs_called, 'Appels'],
            [m.tables_accessed, 'Tables'],
            [m.called_by_count, 'Appelé par'],
            [m.executed_by_jobs, 'Jobs JCL'],
        ] as [number, string][]
    )
        .map(
            ([v, l]) =>
                `<div class="mc"><div class="mv">${v}</div><div class="ml">${l}</div></div>`
        )
        .join('');

    const copybooksHtml = listOrEmpty(
        sheet.copybooks.map(c => `<li>${esc(c)}</li>`).join(''),
        'Aucun'
    );

    const callsHtml = listOrEmpty(
        sheet.calls
            .map(
                c =>
                    `<li>${esc(c.name)}<span class="tag">${esc(renderRelation(c.relation))}</span>` +
                    (c.line ? `<span class="ln">:${c.line}</span>` : '') +
                    `</li>`
            )
            .join(''),
        'Aucun'
    );

    const calledByHtml = listOrEmpty(
        sheet.called_by
            .map(
                c =>
                    `<li>${esc(c.name)}<span class="tag">${esc(renderRelation(c.relation))}</span></li>`
            )
            .join(''),
        'Aucun'
    );

    const tablesHtml = listOrEmpty(
        sheet.tables
            .map(
                t =>
                    `<li>${esc(t.name)}<span class="tag acc-${esc(t.access.toLowerCase())}">${esc(t.access)}</span></li>`
            )
            .join(''),
        'Aucune'
    );

    const execByHtml = listOrEmpty(
        sheet.executed_by
            .map(e => `<li><strong>${esc(e.job)}</strong> › ${esc(e.step)}</li>`)
            .join(''),
        'Aucun'
    );

    return `<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline';">
<style>
body{font-family:var(--vscode-font-family);color:var(--vscode-foreground);background:var(--vscode-editor-background);padding:20px;margin:0}
h1{font-size:1.4em;margin:0 0 4px}
.sub{color:var(--vscode-descriptionForeground);font-size:.85em;margin-bottom:16px;word-break:break-all}
.metrics{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}
.mc{background:var(--vscode-sideBar-background,#1e1e1e);border:1px solid var(--vscode-panel-border,#444);border-radius:4px;padding:10px 16px;text-align:center;min-width:72px}
.mv{font-size:1.6em;font-weight:700;line-height:1}
.ml{font-size:.72em;color:var(--vscode-descriptionForeground);margin-top:4px}
section{margin:16px 0}
h2{font-size:.9em;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--vscode-descriptionForeground);border-bottom:1px solid var(--vscode-panel-border,#444);padding-bottom:4px;margin:0 0 8px}
ul{margin:0;padding-left:18px}
li{margin:3px 0;font-size:.92em}
.tag{display:inline-block;font-size:.72em;padding:1px 6px;border-radius:3px;margin-left:6px;background:var(--vscode-badge-background,#4d4d4d);color:var(--vscode-badge-foreground,#fff);vertical-align:middle}
.acc-read{background:#1a5c14;color:#fff}
.acc-write{background:#7d4000;color:#fff}
.acc-update{background:#0044a0;color:#fff}
.acc-delete{background:#8b0000;color:#fff}
.ln{color:var(--vscode-descriptionForeground);font-size:.85em;margin-left:4px}
.empty{color:var(--vscode-descriptionForeground);font-style:italic;margin:4px 0;font-size:.9em}
.actions{margin-top:24px}
button{padding:6px 16px;background:var(--vscode-button-background);color:var(--vscode-button-foreground);border:none;border-radius:3px;font-size:.9em;opacity:.5;cursor:not-allowed}
</style>
</head>
<body>
<h1>${esc(sheet.name)}</h1>
<div class="sub">${pathStr}${sizeStr}</div>
<div class="metrics">${metricCards}</div>
<section><h2>Copybooks inclus</h2>${copybooksHtml.startsWith('<li>') ? `<ul>${copybooksHtml}</ul>` : copybooksHtml}</section>
<section><h2>Programmes appelés</h2>${callsHtml.startsWith('<li>') ? `<ul>${callsHtml}</ul>` : callsHtml}</section>
<section><h2>Appelé par</h2>${calledByHtml.startsWith('<li>') ? `<ul>${calledByHtml}</ul>` : calledByHtml}</section>
<section><h2>Tables DB2</h2>${tablesHtml.startsWith('<li>') ? `<ul>${tablesHtml}</ul>` : tablesHtml}</section>
<section><h2>Exécuté par (JCL)</h2>${execByHtml.startsWith('<li>') ? `<ul>${execByHtml}</ul>` : execByHtml}</section>
<div class="actions">
  <button disabled title="Disponible avec US-040">Analyser l’impact</button>
</div>
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

export class ProgramSheetPanel {
    private static readonly viewType = 'cobol-cartography.programSheet';
    private static readonly panels = new Map<string, ProgramSheetPanel>();

    private readonly disposables: vscode.Disposable[] = [];

    static async show(programName: string, client: BackendClient): Promise<void> {
        const key = programName.toUpperCase();
        const existing = ProgramSheetPanel.panels.get(key);
        if (existing) {
            existing.webviewPanel.reveal();
            return;
        }
        const panel = vscode.window.createWebviewPanel(
            ProgramSheetPanel.viewType,
            `COBOL : ${key}`,
            vscode.ViewColumn.One,
            { enableScripts: false }
        );
        new ProgramSheetPanel(panel, key, client);
    }

    private constructor(
        private readonly webviewPanel: vscode.WebviewPanel,
        private readonly programName: string,
        private readonly client: BackendClient
    ) {
        ProgramSheetPanel.panels.set(programName, this);
        this.webviewPanel.onDidDispose(
            () => {
                ProgramSheetPanel.panels.delete(this.programName);
                this.dispose();
            },
            null,
            this.disposables
        );
        void this.loadAndRender();
    }

    private async loadAndRender(): Promise<void> {
        this.webviewPanel.webview.html = shellHtml(
            `<p>Chargement de la fiche <strong>${esc(this.programName)}</strong>…</p>`
        );
        try {
            const sheet = await this.client.get<ProgramSheet>(
                `/api/programs/${encodeURIComponent(this.programName)}/sheet`
            );
            this.webviewPanel.webview.html = renderSheet(sheet);
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            this.webviewPanel.webview.html = shellHtml(
                `<h2 class="err">Erreur — ${esc(this.programName)}</h2><p>${esc(msg)}</p>`
            );
        }
    }

    private dispose(): void {
        this.disposables.forEach(d => d.dispose());
        this.disposables.length = 0;
    }
}
