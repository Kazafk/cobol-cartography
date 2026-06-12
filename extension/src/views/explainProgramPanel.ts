import * as vscode from 'vscode';
import { BackendClient } from '../api/backendClient';

interface ComplexityIndicators {
    copybooks_included: number;
    programs_called: number;
    tables_accessed: number;
    called_by_count: number;
    executed_by_jobs: number;
}

interface CallInteraction { target: string; mechanism: string; }
interface TableInteraction { table: string; operations: string[]; }
interface Interactions {
    copybooks: string[];
    outgoing_calls: CallInteraction[];
    table_accesses: TableInteraction[];
    executed_by_jobs: string[];
}

interface BusinessRuleCandidate {
    description: string;
    confidence: number;
    evidence: string;
}

interface ProgramExplanation {
    program_id: string;
    detail_level: string;
    mode: string;
    summary: { role: string; complexity_indicators: ComplexityIndicators };
    interactions: Interactions;
    business_rule_candidates: BusinessRuleCandidate[];
    uncertainties: string[];
    ai_mode: string;
}

type RuleStatus = 'accepted' | 'rejected';
type Validations = Record<string, RuleStatus>;

function esc(s: string): string {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function confidenceLabel(c: number): string {
    if (c >= 0.8) { return '<span class="conf high">ÉLEVÉE</span>'; }
    if (c >= 0.6) { return '<span class="conf med">MOYENNE</span>'; }
    return '<span class="conf low">FAIBLE</span>';
}

function listOrEmpty(items: string[], empty: string): string {
    if (!items.length) { return `<p class="empty">${empty}</p>`; }
    return `<ul>${items.join('')}</ul>`;
}

function ruleCard(r: BusinessRuleCandidate, idx: number, validations: Validations, nonce: string): string {
    const saved = validations[r.description];
    const acceptActive = saved === 'accepted' ? ' active-accept' : '';
    const rejectActive = saved === 'rejected' ? ' active-reject' : '';
    const statusText = saved === 'accepted' ? '&#10003; Validée' : saved === 'rejected' ? '&#10007; Rejetée' : '';
    const statusClass = saved === 'accepted' ? 'status-accepted' : saved === 'rejected' ? 'status-rejected' : '';
    return `<div class="rule" data-desc="${esc(r.description)}" data-status="${saved ?? ''}">
  <div class="rule-header">${esc(r.description)} ${confidenceLabel(r.confidence)}</div>
  <div class="rule-evidence">&#8250; ${esc(r.evidence)}</div>
  <div class="conf-bar"><div class="conf-fill" style="width:${Math.round(r.confidence * 100)}%"></div></div>
  <div class="rule-actions">
    <button class="btn-validate btn-accept${acceptActive}" data-action="accepted">&#10003; Accepter</button>
    <button class="btn-validate btn-reject${rejectActive}" data-action="rejected">&#10007; Rejeter</button>
    <span class="rule-status ${statusClass}">${statusText}</span>
  </div>
</div>`;
}

function renderExplanation(
    ex: ProgramExplanation,
    validations: Validations,
    nonce: string
): string {
    const ci = ex.summary.complexity_indicators;

    const metricCards = (
        [
            [ci.copybooks_included, 'Copybooks'],
            [ci.programs_called, 'Appels'],
            [ci.tables_accessed, 'Tables'],
            [ci.called_by_count, 'Appelé par'],
            [ci.executed_by_jobs, 'Jobs JCL'],
        ] as [number, string][]
    )
        .map(([v, l]) => `<div class="mc"><div class="mv">${v}</div><div class="ml">${l}</div></div>`)
        .join('');

    const copybooksHtml = listOrEmpty(
        ex.interactions.copybooks.map(c => `<li>${esc(c)}</li>`),
        'Aucun'
    );
    const callsHtml = listOrEmpty(
        ex.interactions.outgoing_calls.map(
            c => `<li>${esc(c.target)} <span class="tag">${esc(c.mechanism)}</span></li>`
        ),
        'Aucun'
    );
    const tablesHtml = listOrEmpty(
        ex.interactions.table_accesses.map(
            t =>
                `<li>${esc(t.table)} ${t.operations
                    .map(op => `<span class="tag acc-${esc(op.toLowerCase())}">${esc(op)}</span>`)
                    .join(' ')}</li>`
        ),
        'Aucune'
    );
    const jobsHtml = listOrEmpty(
        ex.interactions.executed_by_jobs.map(j => `<li>${esc(j)}</li>`),
        'Aucun'
    );

    const rulesHtml = ex.business_rule_candidates.length === 0
        ? '<p class="empty">Aucun candidat détecté</p>'
        : ex.business_rule_candidates
            .map((r, i) => ruleCard(r, i, validations, nonce))
            .join('');

    const uncHtml = ex.uncertainties.length === 0
        ? '<p class="empty">Aucune</p>'
        : `<ul>${ex.uncertainties.map(u => `<li>${esc(u)}</li>`).join('')}</ul>`;

    const stateJson = JSON.stringify(validations).replace(/<\//g, '<\\/');

    return `<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'nonce-${nonce}'; style-src 'unsafe-inline';">
<style>
body{font-family:var(--vscode-font-family);color:var(--vscode-foreground);background:var(--vscode-editor-background);padding:20px;margin:0}
h1{font-size:1.3em;margin:0 0 4px}
.badge-mode{font-size:.65em;padding:2px 7px;border-radius:3px;background:var(--vscode-badge-background,#4d4d4d);color:var(--vscode-badge-foreground,#fff);vertical-align:middle;margin-left:8px;letter-spacing:.05em}
.role{background:var(--vscode-textBlockQuote-background,#2a2a2a);border-left:3px solid var(--vscode-focusBorder,#007acc);padding:10px 14px;margin:14px 0;font-size:.93em;line-height:1.5}
.metrics{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}
.mc{background:var(--vscode-sideBar-background,#1e1e1e);border:1px solid var(--vscode-panel-border,#444);border-radius:4px;padding:10px 16px;text-align:center;min-width:72px}
.mv{font-size:1.6em;font-weight:700;line-height:1}
.ml{font-size:.72em;color:var(--vscode-descriptionForeground);margin-top:4px}
section{margin:16px 0}
h2{font-size:.9em;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--vscode-descriptionForeground);border-bottom:1px solid var(--vscode-panel-border,#444);padding-bottom:4px;margin:0 0 8px}
ul{margin:0;padding-left:18px}
li{margin:3px 0;font-size:.92em}
.tag{display:inline-block;font-size:.72em;padding:1px 6px;border-radius:3px;margin-left:5px;background:var(--vscode-badge-background,#4d4d4d);color:var(--vscode-badge-foreground,#fff);vertical-align:middle}
.acc-read{background:#1a5c14;color:#fff}
.acc-write{background:#7d4000;color:#fff}
.acc-update{background:#0044a0;color:#fff}
.acc-delete{background:#8b0000;color:#fff}
.empty{color:var(--vscode-descriptionForeground);font-style:italic;margin:4px 0;font-size:.9em}
.rule{background:var(--vscode-sideBar-background,#1e1e1e);border:1px solid var(--vscode-panel-border,#444);border-radius:4px;padding:10px 12px;margin-bottom:8px;transition:border-color .15s}
.rule[data-status="accepted"]{border-color:#1a5c14}
.rule[data-status="rejected"]{border-color:#7a1a1a;opacity:.7}
.rule-header{font-size:.93em;font-weight:500;margin-bottom:4px}
.rule-evidence{font-size:.78em;color:var(--vscode-descriptionForeground);font-family:var(--vscode-editor-font-family,monospace);margin-bottom:6px}
.conf{font-size:.68em;padding:1px 5px;border-radius:3px;margin-left:6px;vertical-align:middle;font-weight:600}
.conf.high{background:#1a5c14;color:#fff}
.conf.med{background:#7d4000;color:#fff}
.conf.low{background:#555;color:#fff}
.conf-bar{height:3px;background:var(--vscode-panel-border,#444);border-radius:2px;overflow:hidden;margin-bottom:8px}
.conf-fill{height:100%;background:var(--vscode-progressBar-background,#007acc);border-radius:2px}
.rule-actions{display:flex;align-items:center;gap:8px}
.btn-validate{padding:3px 10px;border:1px solid var(--vscode-button-border,#555);border-radius:3px;background:transparent;cursor:pointer;font-size:.78em;color:var(--vscode-foreground);transition:background .12s,color .12s}
.btn-validate:hover{background:var(--vscode-button-secondaryBackground,rgba(255,255,255,.07))}
.btn-accept.active-accept{background:#1a5c14;color:#fff;border-color:#1a5c14}
.btn-reject.active-reject{background:#7a1a1a;color:#fff;border-color:#7a1a1a}
.rule-status{font-size:.78em;font-weight:600}
.status-accepted{color:#4ec983}
.status-rejected{color:#e85858}
</style>
</head>
<body>
<h1>${esc(ex.program_id)}<span class="badge-mode">LOCAL STRICT</span></h1>
<div class="role">${esc(ex.summary.role)}</div>
<div class="metrics">${metricCards}</div>
<section>
  <h2>Interactions</h2>
  <strong style="font-size:.85em">Copybooks</strong>${copybooksHtml}
  <strong style="font-size:.85em;display:block;margin-top:8px">Appels sortants</strong>${callsHtml}
  <strong style="font-size:.85em;display:block;margin-top:8px">Tables DB2</strong>${tablesHtml}
  <strong style="font-size:.85em;display:block;margin-top:8px">Exécuté par (JCL)</strong>${jobsHtml}
</section>
<section>
  <h2>Règles métier candidates</h2>
  ${rulesHtml}
</section>
<section>
  <h2>Incertitudes explicites</h2>
  ${uncHtml}
</section>
<script nonce="${nonce}">
(function () {
  var vscode = acquireVsCodeApi();
  var saved = ${stateJson};

  document.querySelectorAll('.btn-validate').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var ruleEl = btn.closest('.rule');
      var desc = ruleEl.dataset.desc;
      var action = btn.dataset.action;
      var current = ruleEl.dataset.status;
      var next = (current === action) ? '' : action;

      ruleEl.dataset.status = next;
      applyStatus(ruleEl, next);
      vscode.postMessage({ command: 'validate', description: desc, status: next || 'reset' });
    });
  });

  function applyStatus(ruleEl, status) {
    var acceptBtn = ruleEl.querySelector('.btn-accept');
    var rejectBtn = ruleEl.querySelector('.btn-reject');
    var statusEl = ruleEl.querySelector('.rule-status');

    if (status === 'accepted') {
      acceptBtn.classList.add('active-accept');
      rejectBtn.classList.remove('active-reject');
      statusEl.textContent = '✓ Validée';
      statusEl.className = 'rule-status status-accepted';
    } else if (status === 'rejected') {
      acceptBtn.classList.remove('active-accept');
      rejectBtn.classList.add('active-reject');
      statusEl.textContent = '✗ Rejetée';
      statusEl.className = 'rule-status status-rejected';
    } else {
      acceptBtn.classList.remove('active-accept');
      rejectBtn.classList.remove('active-reject');
      statusEl.textContent = '';
      statusEl.className = 'rule-status';
    }
  }
})();
</script>
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

const STORAGE_PREFIX = 'cobol-cartography.rules.';

export class ExplainProgramPanel {
    private static readonly viewType = 'cobol-cartography.explainProgram';
    private static readonly panels = new Map<string, ExplainProgramPanel>();

    private readonly disposables: vscode.Disposable[] = [];

    static async show(
        programName: string,
        client: BackendClient,
        context: vscode.ExtensionContext
    ): Promise<void> {
        const key = programName.toUpperCase();
        const existing = ExplainProgramPanel.panels.get(key);
        if (existing) {
            existing.webviewPanel.reveal();
            return;
        }
        const panel = vscode.window.createWebviewPanel(
            ExplainProgramPanel.viewType,
            `Explication : ${key}`,
            vscode.ViewColumn.One,
            { enableScripts: true }
        );
        new ExplainProgramPanel(panel, key, client, context);
    }

    private constructor(
        private readonly webviewPanel: vscode.WebviewPanel,
        private readonly programName: string,
        private readonly client: BackendClient,
        private readonly context: vscode.ExtensionContext
    ) {
        ExplainProgramPanel.panels.set(programName, this);
        this.webviewPanel.onDidDispose(
            () => { ExplainProgramPanel.panels.delete(this.programName); this.dispose(); },
            null,
            this.disposables
        );
        this.webviewPanel.webview.onDidReceiveMessage(
            async (msg: { command: string; description: string; status: string }) => {
                if (msg.command !== 'validate') { return; }
                const storageKey = STORAGE_PREFIX + this.programName;
                const current = this.context.workspaceState.get<Validations>(storageKey) ?? {};
                if (msg.status === 'reset') {
                    delete current[msg.description];
                } else {
                    current[msg.description] = msg.status as RuleStatus;
                }
                await this.context.workspaceState.update(storageKey, current);
            },
            null,
            this.disposables
        );
        void this.loadAndRender();
    }

    private async loadAndRender(): Promise<void> {
        this.webviewPanel.webview.html = shellHtml(
            `<p>Génération de l'explication pour <strong>${esc(this.programName)}</strong>…</p>`
        );
        try {
            const ex = await this.client.post<ProgramExplanation>(
                '/api/ai/explain/program',
                { programId: this.programName, detailLevel: 'standard', includeBusinessRules: true }
            );
            const storageKey = STORAGE_PREFIX + this.programName;
            const validations = this.context.workspaceState.get<Validations>(storageKey) ?? {};
            const nonce = Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2);
            this.webviewPanel.webview.html = renderExplanation(ex, validations, nonce);
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
