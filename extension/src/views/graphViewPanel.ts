import * as vscode from 'vscode';
import { BackendClient } from '../api/backendClient';

interface D3Node {
    id: string;
    kind: string;
    name: string;
    path: string | null;
}

interface D3Link {
    source: string;
    target: string;
    relation: string;
    confidence: number;
}

interface GraphExport {
    nodes: D3Node[];
    links: D3Link[];
}

export class GraphViewPanel {
    private static _instance: GraphViewPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private readonly _disposables: vscode.Disposable[] = [];

    private constructor(panel: vscode.WebviewPanel) {
        this._panel = panel;
        panel.onDidDispose(() => this.dispose(), null, this._disposables);
    }

    static async show(client: BackendClient): Promise<void> {
        if (GraphViewPanel._instance) {
            GraphViewPanel._instance._panel.reveal(vscode.ViewColumn.One);
            return;
        }
        const panel = vscode.window.createWebviewPanel(
            'cobol-cartography.graphView',
            'COBOL Graph',
            vscode.ViewColumn.One,
            { enableScripts: true, retainContextWhenHidden: true }
        );
        const instance = new GraphViewPanel(panel);
        GraphViewPanel._instance = instance;

        panel.webview.html = '<body style="padding:2rem;font-family:sans-serif;color:var(--vscode-foreground)">Chargement du graphe...</body>';

        let graph: GraphExport;
        try {
            graph = await client.get<GraphExport>('/api/graph/export');
        } catch {
            panel.webview.html = '<body style="padding:2rem;font-family:sans-serif;color:var(--vscode-foreground)">Erreur de chargement du graphe. Le backend est-il démarré ?</body>';
            return;
        }

        panel.webview.html = GraphViewPanel._buildHtml(graph);

        panel.webview.onDidReceiveMessage(
            (msg: { command: string; path?: string }) => {
                if (msg.command === 'openFile' && msg.path) {
                    vscode.commands.executeCommand('vscode.open', vscode.Uri.file(msg.path));
                }
            },
            null,
            instance._disposables
        );
    }

    private static _buildHtml(graph: GraphExport): string {
        const nonce = Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2);
        const graphJson = JSON.stringify(graph).replace(/<\//g, '<\\/');

        return `<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'nonce-${nonce}'; style-src 'unsafe-inline';">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--vscode-editor-background); color: var(--vscode-foreground); font-family: var(--vscode-font-family, sans-serif); display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
#controls { display: flex; align-items: center; gap: 8px; padding: 6px 12px; background: var(--vscode-editor-background); border-bottom: 1px solid var(--vscode-panel-border, #444); flex-shrink: 0; flex-wrap: wrap; }
.lbl { font-size: 11px; color: var(--vscode-descriptionForeground); }
.kind-btn { padding: 2px 10px; border: 1px solid var(--vscode-button-border, #555); border-radius: 10px; background: transparent; cursor: pointer; font-size: 11px; color: inherit; opacity: 0.45; transition: opacity 0.15s; }
.kind-btn.active { opacity: 1; background: var(--vscode-button-secondaryBackground, rgba(255,255,255,0.06)); }
#counter { margin-left: auto; font-size: 11px; color: var(--vscode-descriptionForeground); }
#canvas-wrap { flex: 1; position: relative; overflow: hidden; }
canvas { display: block; width: 100%; height: 100%; }
#tip { position: absolute; padding: 4px 8px; background: var(--vscode-editorHoverWidget-background, #252526); border: 1px solid var(--vscode-editorHoverWidget-border, #454545); color: var(--vscode-editorHoverWidget-foreground, #ccc); font-size: 11px; border-radius: 3px; pointer-events: none; display: none; max-width: 320px; white-space: nowrap; z-index: 10; }
</style>
</head>
<body>
<div id="controls">
  <span class="lbl">Afficher :</span>
  <button class="kind-btn active" id="btn-program" style="color:#4e9af1">&#9679; Programmes</button>
  <button class="kind-btn active" id="btn-copybook" style="color:#e8a94c">&#9679; Copybooks</button>
  <button class="kind-btn active" id="btn-db2table" style="color:#4ec983">&#9679; Tables DB2</button>
  <button class="kind-btn active" id="btn-jcl_job" style="color:#a078e8">&#9679; Jobs JCL</button>
  <button class="kind-btn active" id="btn-jcl_step" style="color:#8899aa">&#9679; Étapes JCL</button>
  <span id="counter"></span>
</div>
<div id="canvas-wrap">
  <canvas id="graph"></canvas>
  <div id="tip"></div>
</div>
<script nonce="${nonce}">
(function () {
  var graphData = ${graphJson};
  var canvas = document.getElementById('graph');
  var ctx = canvas.getContext('2d');
  var tip = document.getElementById('tip');
  var vscode = acquireVsCodeApi();

  var COLORS = {
    'program':  '#4e9af1',
    'copybook': '#e8a94c',
    'db2table': '#4ec983',
    'jcl_job':  '#a078e8',
    'jcl_step': '#8899aa'
  };
  var RADIUS = { 'program': 9, 'jcl_job': 9 };
  function nodeR(n) { return RADIUS[n.kind] || 6; }

  var enabledKinds = new Set(Object.keys(COLORS));

  var nodes = graphData.nodes.map(function (n) {
    return { id: n.id, kind: n.kind, name: n.name, path: n.path,
             x: 0, y: 0, vx: (Math.random() - 0.5), vy: (Math.random() - 0.5),
             pinned: false };
  });
  var nodeById = {};
  nodes.forEach(function (n) { nodeById[n.id] = n; });
  var links = graphData.links;

  var hovered = null, selected = null, dragNode = null, dragOX = 0, dragOY = 0;
  var frame = 0;

  /* ---- resize ---- */
  function resize() {
    var wrap = canvas.parentElement;
    canvas.width  = wrap.clientWidth;
    canvas.height = wrap.clientHeight;
    if (frame === 0 && nodes.length > 0) {
      var spread = Math.min(canvas.width, canvas.height) * 0.4;
      nodes.forEach(function (n) {
        n.x = canvas.width  / 2 + (Math.random() - 0.5) * spread * 2;
        n.y = canvas.height / 2 + (Math.random() - 0.5) * spread * 2;
      });
    }
  }
  resize();
  new ResizeObserver(resize).observe(canvas.parentElement);

  /* ---- helpers ---- */
  function filtered() {
    return nodes.filter(function (n) { return enabledKinds.has(n.kind); });
  }
  function filteredLinks(ids) {
    return links.filter(function (l) { return ids.has(l.source) && ids.has(l.target); });
  }
  function updateCounter() {
    var fn = filtered();
    var ids = new Set(fn.map(function (n) { return n.id; }));
    document.getElementById('counter').textContent =
      fn.length + ' nœuds · ' + filteredLinks(ids).length + ' arêtes';
  }
  function nodeAt(mx, my) {
    var fn = filtered();
    for (var i = fn.length - 1; i >= 0; i--) {
      var n = fn[i];
      var dx = n.x - mx, dy = n.y - my;
      var r = nodeR(n) + 4;
      if (dx * dx + dy * dy <= r * r) { return n; }
    }
    return null;
  }

  /* ---- simulation ---- */
  function tick() {
    frame++;
    var alpha = Math.max(0, 1 - frame / 500);
    var fn = filtered();
    var ids = new Set(fn.map(function (n) { return n.id; }));
    var fl = filteredLinks(ids);

    if (alpha > 0) {
      /* repulsion */
      for (var i = 0; i < fn.length; i++) {
        for (var j = i + 1; j < fn.length; j++) {
          var a = fn[i], b = fn[j];
          var dx = b.x - a.x || 0.01, dy = b.y - a.y || 0.01;
          var d2 = dx * dx + dy * dy;
          var d  = Math.sqrt(d2);
          var f  = alpha * 2800 / d2;
          var fx = f * dx / d, fy = f * dy / d;
          if (!a.pinned) { a.vx -= fx; a.vy -= fy; }
          if (!b.pinned) { b.vx += fx; b.vy += fy; }
        }
      }
      /* spring */
      for (var k = 0; k < fl.length; k++) {
        var l  = fl[k];
        var na = nodeById[l.source], nb = nodeById[l.target];
        if (!na || !nb) { continue; }
        var dx = nb.x - na.x, dy = nb.y - na.y;
        var d  = Math.sqrt(dx * dx + dy * dy) || 1;
        var f  = alpha * 0.07 * (d - 110);
        var fx = f * dx / d, fy = f * dy / d;
        if (!na.pinned) { na.vx += fx; na.vy += fy; }
        if (!nb.pinned) { nb.vx -= fx; nb.vy -= fy; }
      }
      /* gravity */
      var cx = canvas.width / 2, cy = canvas.height / 2;
      for (var i = 0; i < fn.length; i++) {
        var n = fn[i];
        if (n.pinned) { continue; }
        n.vx += (cx - n.x) * 0.0025 * alpha;
        n.vy += (cy - n.y) * 0.0025 * alpha;
      }
      /* integrate */
      for (var i = 0; i < fn.length; i++) {
        var n = fn[i];
        if (n.pinned) { continue; }
        n.vx *= 0.8; n.vy *= 0.8;
        n.x  += n.vx; n.y += n.vy;
        n.x   = Math.max(15, Math.min(canvas.width  - 15, n.x));
        n.y   = Math.max(15, Math.min(canvas.height - 15, n.y));
      }
    }

    draw(fn, fl);
    requestAnimationFrame(tick);
  }

  /* ---- draw ---- */
  function draw(fn, fl) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    var localById = {};
    fn.forEach(function (n) { localById[n.id] = n; });

    /* links */
    for (var k = 0; k < fl.length; k++) {
      var l = fl[k];
      var a = localById[l.source], b = localById[l.target];
      if (!a || !b) { continue; }
      var dx = b.x - a.x, dy = b.y - a.y;
      var d  = Math.sqrt(dx * dx + dy * dy) || 1;
      var rb = nodeR(b);
      var ex = b.x - rb * dx / d, ey = b.y - rb * dy / d;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(ex, ey);
      ctx.strokeStyle = 'rgba(150,150,170,0.28)';
      ctx.lineWidth = 1;
      ctx.stroke();
      var ang = Math.atan2(dy, dx);
      ctx.beginPath();
      ctx.moveTo(ex, ey);
      ctx.lineTo(ex - 7 * Math.cos(ang - 0.45), ey - 7 * Math.sin(ang - 0.45));
      ctx.lineTo(ex - 7 * Math.cos(ang + 0.45), ey - 7 * Math.sin(ang + 0.45));
      ctx.closePath();
      ctx.fillStyle = 'rgba(150,150,170,0.35)';
      ctx.fill();
    }

    /* nodes */
    for (var i = 0; i < fn.length; i++) {
      var n = fn[i];
      var col = COLORS[n.kind] || '#888';
      var r   = nodeR(n);
      var isSel = (n === selected), isHov = (n === hovered);
      if (isSel) { r += 3; }
      ctx.beginPath();
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fillStyle = col;
      ctx.fill();
      if (isSel || isHov) {
        ctx.strokeStyle = 'rgba(255,255,255,0.75)';
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.fillStyle = 'rgba(225,225,225,0.95)';
        ctx.font = (isSel ? 'bold ' : '') + '11px sans-serif';
        ctx.fillText(n.name, n.x + r + 4, n.y + 4);
      }
    }

    /* empty state */
    if (fn.length === 0) {
      ctx.fillStyle = 'rgba(150,150,150,0.45)';
      ctx.font = '13px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Graphe vide — indexez un workspace pour commencer', canvas.width / 2, canvas.height / 2);
      ctx.textAlign = 'left';
    }
  }

  /* ---- mouse ---- */
  canvas.addEventListener('mousedown', function (e) {
    var rect = canvas.getBoundingClientRect();
    var n = nodeAt(e.clientX - rect.left, e.clientY - rect.top);
    if (n) {
      dragNode = n;
      n.pinned = true;
      dragOX = n.x - (e.clientX - rect.left);
      dragOY = n.y - (e.clientY - rect.top);
    }
  });

  canvas.addEventListener('mousemove', function (e) {
    var rect = canvas.getBoundingClientRect();
    var mx = e.clientX - rect.left, my = e.clientY - rect.top;
    if (dragNode) {
      dragNode.x = mx + dragOX;
      dragNode.y = my + dragOY;
      return;
    }
    var n = nodeAt(mx, my);
    hovered = n;
    if (n) {
      canvas.style.cursor = 'pointer';
      tip.textContent = n.name + (n.path ? ' (' + n.kind + ')' : ' [stub]');
      tip.style.display = 'block';
      tip.style.left = (mx + 16) + 'px';
      tip.style.top  = (my -  4) + 'px';
    } else {
      canvas.style.cursor = 'default';
      tip.style.display = 'none';
    }
  });

  canvas.addEventListener('mouseup', function () { dragNode = null; });

  canvas.addEventListener('mouseleave', function () {
    dragNode = null; hovered = null;
    tip.style.display = 'none';
    canvas.style.cursor = 'default';
  });

  canvas.addEventListener('click', function (e) {
    var rect = canvas.getBoundingClientRect();
    var n = nodeAt(e.clientX - rect.left, e.clientY - rect.top);
    if (n) {
      selected = (selected === n) ? null : n;
      if (n.path) { vscode.postMessage({ command: 'openFile', path: n.path }); }
    } else {
      selected = null;
    }
  });

  /* ---- filters ---- */
  ['program', 'copybook', 'db2table', 'jcl_job', 'jcl_step'].forEach(function (kind) {
    var btn = document.getElementById('btn-' + kind);
    if (!btn) { return; }
    btn.addEventListener('click', function () {
      if (enabledKinds.has(kind)) {
        enabledKinds.delete(kind);
        btn.classList.remove('active');
      } else {
        enabledKinds.add(kind);
        btn.classList.add('active');
      }
      frame = 0;
      updateCounter();
    });
  });

  updateCounter();
  if (nodes.length > 0) {
    tick();
  } else {
    draw([], []);
  }
})();
</script>
</body>
</html>`;
    }

    private dispose(): void {
        GraphViewPanel._instance = undefined;
        this._panel.dispose();
        for (const d of this._disposables) { d.dispose(); }
        this._disposables.length = 0;
    }
}
