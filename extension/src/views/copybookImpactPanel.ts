import * as vscode from 'vscode';
import { BackendClient } from '../api/backendClient';

interface ImpactEntry {
    name: string;
    depth: number;
    via: string | null;
    confidence: number;
}

interface ImpactedJob {
    name: string;
}

interface CopybookImpact {
    copybook_name: string;
    direct_impacts: ImpactEntry[];
    indirect_impacts: ImpactEntry[];
    uncertain_impacts: ImpactEntry[];
    impacted_jobs: ImpactedJob[];
    total_programs: number;
    total_jobs: number;
}

function esc(s: string): string {
    return s
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function listOrEmpty(items: string[], empty: string): string {
    if (items.length === 0) return `<p class="empty">${empty}</p>`;
    return `<ul>${items.join('')}</ul>`;
}

function depthBadge(depth: number): string {
    return `<span class="badge depth-${Math.min(depth, 5)}">d=${depth}</span>`;
}

function renderImpact(impact: CopybookImpact): string {
    const directItems = impact.direct_impacts.map(
        e => `<li>${esc(e.name)} ${depthBadge(e.depth)}</li>`
    );
    const indirectItems = impact.indirect_impacts.map(
        e =>
            `<li>${esc(e.name)} ${depthBadge(e.depth)}` +
            (e.via ? ` <span class="via">via ${esc(e.via)}</span>` : '') +
            `</li>`
    );
    const jobItems = impact.impacted_jobs.map(j => `<li>${esc(j.name)}</li>`);

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
.badge{display:inline-block;font-size:.7em;padding:1px 5px;border-radius:3px;margin-left:5px;vertical-align:middle;font-weight:600}
.depth-1{background:#1a5c14;color:#fff}
.depth-2{background:#0044a0;color:#fff}
.depth-3{background:#7d4000;color:#fff}
.depth-4,.depth-5{background:#555;color:#fff}
.via{color:var(--vscode-descriptionForeground);font-size:.82em;font-style:italic;margin-left:4px}
.empty{color:var(--vscode-descriptionForeground);font-style:italic;margin:4px 0;font-size:.9em}
</style>
</head>
<body>
<h1>Impact — ${esc(impact.copybook_name)}.cpy</h1>
<div class="sub">Analyse d'impact copybook — programmes et jobs affectés par une modification</div>
<div class="metrics">
  <div class="mc"><div class="mv">${impact.total_programs}</div><div class="ml">Programmes</div></div>
  <div class="mc"><div class="mv">${impact.direct_impacts.length}</div><div class="ml">Directs</div></div>
  <div class="mc"><div class="mv">${impact.indirect_impacts.length}</div><div class="ml">Indirects</div></div>
  <div class="mc"><div class="mv">${impact.total_jobs}</div><div class="ml">Jobs JCL</div></div>
</div>
<section>
  <h2>Impacts directs (depth=1)</h2>
  ${listOrEmpty(directItems, 'Aucun programme n\'inclut ce copybook')}
</section>
<section>
  <h2>Impacts indirects (appelants transitifs)</h2>
  ${listOrEmpty(indirectItems, 'Aucun')}
</section>
<section>
  <h2>Jobs JCL impactés</h2>
  ${listOrEmpty(jobItems, 'Aucun')}
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

export class CopybookImpactPanel {
    private static readonly viewType = 'cobol-cartography.copybookImpact';
    private static readonly panels = new Map<string, CopybookImpactPanel>();

    private readonly disposables: vscode.Disposable[] = [];

    static async show(copybookName: string, client: BackendClient): Promise<void> {
        const key = copybookName.toUpperCase();
        const existing = CopybookImpactPanel.panels.get(key);
        if (existing) {
            existing.webviewPanel.reveal();
            return;
        }
        const panel = vscode.window.createWebviewPanel(
            CopybookImpactPanel.viewType,
            `Impact : ${key}`,
            vscode.ViewColumn.One,
            { enableScripts: false }
        );
        new CopybookImpactPanel(panel, key, client);
    }

    private constructor(
        private readonly webviewPanel: vscode.WebviewPanel,
        private readonly copybookName: string,
        private readonly client: BackendClient
    ) {
        CopybookImpactPanel.panels.set(copybookName, this);
        this.webviewPanel.onDidDispose(
            () => {
                CopybookImpactPanel.panels.delete(this.copybookName);
                this.dispose();
            },
            null,
            this.disposables
        );
        void this.loadAndRender();
    }

    private async loadAndRender(): Promise<void> {
        this.webviewPanel.webview.html = shellHtml(
            `<p>Analyse d'impact pour <strong>${esc(this.copybookName)}</strong>…</p>`
        );
        try {
            const impact = await this.client.get<CopybookImpact>(
                `/api/impact/copybook/${encodeURIComponent(this.copybookName)}`
            );
            this.webviewPanel.webview.html = renderImpact(impact);
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            this.webviewPanel.webview.html = shellHtml(
                `<h2 class="err">Erreur — ${esc(this.copybookName)}</h2><p>${esc(msg)}</p>`
            );
        }
    }

    private dispose(): void {
        this.disposables.forEach(d => d.dispose());
        this.disposables.length = 0;
    }
}
