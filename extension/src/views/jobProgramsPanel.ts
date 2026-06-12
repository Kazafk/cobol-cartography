import * as vscode from 'vscode';
import { BackendClient } from '../api/backendClient';

interface StepExecution {
    step_name: string;
    program_name: string;
    program_path: string | null;
}

interface JobPrograms {
    job_name: string;
    steps: StepExecution[];
    total_programs: number;
}

function esc(s: string): string {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function renderJobPrograms(data: JobPrograms): string {
    const rowsHtml = data.steps.length === 0
        ? `<tr><td colspan="3" class="empty">Aucune étape EXEC PGM trouvée dans ce job</td></tr>`
        : data.steps.map(s => {
            const pathCell = s.program_path
                ? `<span class="path">${esc(s.program_path)}</span>`
                : `<span class="badge-stub">stub</span>`;
            return `<tr>
  <td class="step">${esc(s.step_name)}</td>
  <td class="prog">${esc(s.program_name)}</td>
  <td>${pathCell}</td>
</tr>`;
        }).join('');

    return `<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline';">
<style>
body{font-family:var(--vscode-font-family);color:var(--vscode-foreground);background:var(--vscode-editor-background);padding:20px;margin:0}
h1{font-size:1.3em;margin:0 0 4px}
.sub{color:var(--vscode-descriptionForeground);font-size:.85em;margin-bottom:20px}
.metrics{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}
.mc{background:var(--vscode-sideBar-background,#1e1e1e);border:1px solid var(--vscode-panel-border,#444);border-radius:4px;padding:10px 16px;text-align:center;min-width:72px}
.mv{font-size:1.6em;font-weight:700;line-height:1}
.ml{font-size:.72em;color:var(--vscode-descriptionForeground);margin-top:4px}
table{width:100%;border-collapse:collapse;font-size:.9em}
thead th{text-align:left;font-size:.78em;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--vscode-descriptionForeground);border-bottom:1px solid var(--vscode-panel-border,#444);padding:4px 8px 6px}
tbody tr:hover{background:var(--vscode-list-hoverBackground,rgba(255,255,255,.04))}
td{padding:5px 8px;border-bottom:1px solid var(--vscode-panel-border,#222);vertical-align:top}
.step{font-family:var(--vscode-editor-font-family,monospace);font-weight:600;color:var(--vscode-symbolIcon-keywordForeground,#c586c0);white-space:nowrap}
.prog{font-family:var(--vscode-editor-font-family,monospace);font-weight:600;white-space:nowrap}
.path{font-size:.78em;color:var(--vscode-descriptionForeground);word-break:break-all}
.badge-stub{display:inline-block;font-size:.72em;padding:1px 6px;border-radius:3px;background:#555;color:#fff;vertical-align:middle}
.empty{color:var(--vscode-descriptionForeground);font-style:italic;padding:12px 8px;text-align:center}
</style>
</head>
<body>
<h1>Job — ${esc(data.job_name)}</h1>
<div class="sub">Programmes exécutés par ce job JCL</div>
<div class="metrics">
  <div class="mc"><div class="mv">${data.steps.length}</div><div class="ml">Étapes</div></div>
  <div class="mc"><div class="mv">${data.total_programs}</div><div class="ml">Programmes</div></div>
  <div class="mc"><div class="mv">${data.steps.filter(s => s.program_path === null).length}</div><div class="ml">Stubs</div></div>
</div>
<table>
  <thead><tr><th>Étape</th><th>Programme</th><th>Chemin</th></tr></thead>
  <tbody>${rowsHtml}</tbody>
</table>
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

export class JobProgramsPanel {
    private static readonly viewType = 'cobol-cartography.jobPrograms';
    private static readonly panels = new Map<string, JobProgramsPanel>();

    private readonly disposables: vscode.Disposable[] = [];

    static async show(jobName: string, client: BackendClient): Promise<void> {
        const key = jobName.toUpperCase();
        const existing = JobProgramsPanel.panels.get(key);
        if (existing) {
            existing.webviewPanel.reveal();
            return;
        }
        const panel = vscode.window.createWebviewPanel(
            JobProgramsPanel.viewType,
            `Job : ${key}`,
            vscode.ViewColumn.One,
            { enableScripts: false }
        );
        new JobProgramsPanel(panel, key, client);
    }

    private constructor(
        private readonly webviewPanel: vscode.WebviewPanel,
        private readonly jobName: string,
        private readonly client: BackendClient
    ) {
        JobProgramsPanel.panels.set(jobName, this);
        this.webviewPanel.onDidDispose(
            () => { JobProgramsPanel.panels.delete(this.jobName); this.dispose(); },
            null,
            this.disposables
        );
        void this.loadAndRender();
    }

    private async loadAndRender(): Promise<void> {
        this.webviewPanel.webview.html = shellHtml(
            `<p>Chargement des programmes pour le job <strong>${esc(this.jobName)}</strong>…</p>`
        );
        try {
            const data = await this.client.get<JobPrograms>(
                `/api/jobs/${encodeURIComponent(this.jobName)}/programs`
            );
            this.webviewPanel.webview.html = renderJobPrograms(data);
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            this.webviewPanel.webview.html = shellHtml(
                `<h2 class="err">Erreur — ${esc(this.jobName)}</h2><p>${esc(msg)}</p>`
            );
        }
    }

    private dispose(): void {
        this.disposables.forEach(d => d.dispose());
        this.disposables.length = 0;
    }
}
