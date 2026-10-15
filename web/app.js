const SAMPLES = {
    valid: `int idade = 20; int total = 0; total = idade + 5 * 2; return total;`,
    undeclared: `int resultado = 10; total = resultado + 5;`,
    type_error: `int resultado = "texto";`
};

const editor = document.getElementById("code-editor");
const lineNumbers = document.getElementById("line-numbers");
const fileInput = document.getElementById("source-file");
const filenameLabel = document.getElementById("current-filename");
const sourceStats = document.getElementById("source-stats");
const sampleSelect = document.getElementById("sample-select");
const analyzeButton = document.getElementById("btn-analyze");
const analysisIndicator = document.getElementById("analysis-indicator");
const analysisStatus = document.getElementById("analysis-status");
const analysisTime = document.getElementById("analysis-time");
const cursorPosition = document.getElementById("cursor-position");
const tokensCount = document.getElementById("tokens-count");
const symbolsCount = document.getElementById("symbols-count");
const problemsCount = document.getElementById("problems-count");
const statusErrors = document.getElementById("status-errors");
const semanticSummary = document.getElementById("semantic-summary");
const tokensBody = document.getElementById("tokens-body");
const symbolsBody = document.getElementById("symbols-body");
const problemsBody = document.getElementById("problems-body");
const astOutput = document.getElementById("ast-output");
const tabs = document.querySelectorAll(".output-tab");
const pages = document.querySelectorAll(".output-page");
const workspace = document.getElementById("workspace");
const resizer = document.getElementById("editor-resizer");
const toggleOutput = document.getElementById("toggle-output");
const menuTriggers = document.querySelectorAll(".menu-trigger");
const menuActions = document.querySelectorAll("[data-action]");
const helpDialog = document.getElementById("help-dialog");
const helpDialogTitle = document.getElementById("help-dialog-title");
const helpDialogBody = document.getElementById("help-dialog-body");
const closeHelpButton = document.getElementById("close-help");

let currentFilename = "main.c";

function closeMenus(exception = null) {
    menuTriggers.forEach((trigger) => {
        const menu = document.getElementById(trigger.getAttribute("aria-controls"));
        if (trigger === exception) return;
        trigger.setAttribute("aria-expanded", "false");
        menu.hidden = true;
    });
}

menuTriggers.forEach((trigger) => {
    trigger.addEventListener("click", (event) => {
        event.stopPropagation();
        const menu = document.getElementById(trigger.getAttribute("aria-controls"));
        const opening = menu.hidden;
        closeMenus(trigger);
        menu.hidden = !opening;
        trigger.setAttribute("aria-expanded", String(opening));
    });
});

document.addEventListener("click", () => closeMenus());
document.querySelectorAll(".menu-dropdown").forEach((menu) => {
    menu.addEventListener("click", (event) => event.stopPropagation());
});

function selectTab(button) {
    tabs.forEach((tab) => {
        const active = tab === button;
        tab.classList.toggle("active", active);
        tab.setAttribute("aria-selected", String(active));
    });
    pages.forEach((page) => {
        const active = page.id === button.dataset.tab;
        page.classList.toggle("active", active);
        page.hidden = !active;
    });
}

function openTabById(id) {
    const tab = Array.from(tabs).find((item) => item.dataset.tab === id);
    if (tab) selectTab(tab);
}

tabs.forEach((tab) => tab.addEventListener("click", () => selectTab(tab)));
function updateEditorMetadata() {
    const lines = editor.value.split("\n");
    const fragment = document.createDocumentFragment();
    lines.forEach((_, index) => {
        const number = document.createElement("span");
        number.textContent = index + 1;
        fragment.appendChild(number);
    });
    lineNumbers.replaceChildren(fragment);
    sourceStats.textContent = `${lines.length} ${lines.length === 1 ? "linha" : "linhas"}`;
}

function updateCursorPosition() {
    const beforeCursor = editor.value.slice(0, editor.selectionStart);
    const lines = beforeCursor.split("\n");
    cursorPosition.textContent = `Ln ${lines.length}, Col ${lines.at(-1).length + 1}`;
}

editor.addEventListener("input", () => {
    updateEditorMetadata();
    updateCursorPosition();
});
editor.addEventListener("click", updateCursorPosition);
editor.addEventListener("keyup", updateCursorPosition);
editor.addEventListener("scroll", () => { lineNumbers.scrollTop = editor.scrollTop; });
editor.addEventListener("keydown", (event) => {
    if (event.key !== "Tab") return;
    event.preventDefault();
    editor.setRangeText("    ", editor.selectionStart, editor.selectionEnd, "end");
    updateEditorMetadata();
    updateCursorPosition();
});

sampleSelect.addEventListener("change", () => {
    editor.value = SAMPLES[sampleSelect.value];
    currentFilename = `${sampleSelect.value}.c`;
    filenameLabel.textContent = currentFilename;
    updateEditorMetadata();
    resetOutput();
    editor.focus();
});

fileInput.addEventListener("change", async () => {
    const [file] = fileInput.files;
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".c")) {
        setStatus("Selecione um arquivo .c", "error");
        fileInput.value = "";
        return;
    }

    editor.value = await file.text();
    currentFilename = file.name;
    filenameLabel.textContent = currentFilename;
    updateEditorMetadata();
    resetOutput();
    setStatus("Arquivo carregado", "ready");
});

window.addEventListener("keydown", (event) => {
    const commandKey = event.ctrlKey || event.metaKey;
    const key = event.key.toLowerCase();

    if (commandKey && key === "enter") {
        event.preventDefault();
        analyzeSource();
        return;
    }

    if (commandKey && key === "n") {
        event.preventDefault();
        newFile();
    } else if (commandKey && key === "o") {
        event.preventDefault();
        fileInput.click();
    } else if (commandKey && key === "s") {
        event.preventDefault();
        saveSourceFile();
    } else if (key === "escape") {
        closeMenus();
        if (helpDialog.open) helpDialog.close();
    }
});

function newFile() {
    editor.value = "";
    currentFilename = "main.c";
    filenameLabel.textContent = currentFilename;
    updateEditorMetadata();
    updateCursorPosition();
    resetOutput();
    editor.focus();
}

function clearEditor() {
    editor.value = "";
    updateEditorMetadata();
    updateCursorPosition();
    resetOutput();
    editor.focus();
}

function saveSourceFile() {
    const blob = new Blob([editor.value], { type: "text/x-c;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = currentFilename || "main.c";
    link.click();
    URL.revokeObjectURL(url);
    setStatus("Arquivo salvo", "ready");
}

function showOutputTab(id) {
    document.body.classList.remove("output-collapsed");
    toggleOutput.setAttribute("aria-pressed", "false");
    openTabById(id);
}

function showHelp(kind) {
    if (kind === "language") {
        helpDialogTitle.textContent = "Linguagem suportada";
        helpDialogBody.innerHTML = `
            <p>Este projeto analisa um subconjunto didático de C com declarações, atribuições, expressões aritméticas e retorno.</p>
            <pre>int idade = 20;
float preco = 19.90;
char letra = 'A';
idade = idade + 2 * 3;
return idade;</pre>
            <p>Tipos reconhecidos: <code>int</code>, <code>float</code> e <code>char</code>. Operadores: <code>+</code>, <code>-</code>, <code>*</code>, <code>/</code> e <code>%</code>.</p>`;
    } else {
        helpDialogTitle.textContent = "Sobre o projeto";
        helpDialogBody.innerHTML = `
            <p><strong>Mini Compilador C</strong></p>
            <p>Projeto acadêmico dedicado às etapas léxica, sintática e semântica. A interface apresenta tokens, tabela de símbolos, árvore sintática e diagnósticos do código.</p>
            <p>Use <code>Ctrl + Enter</code> para analisar o conteúdo do editor.</p>`;
    }

    helpDialog.showModal();
}

menuActions.forEach((item) => {
    item.addEventListener("click", () => {
        closeMenus();

        switch (item.dataset.action) {
            case "new-file": newFile(); break;
            case "open-file": fileInput.click(); break;
            case "save-file": saveSourceFile(); break;
            case "undo": editor.focus(); document.execCommand("undo"); updateEditorMetadata(); break;
            case "redo": editor.focus(); document.execCommand("redo"); updateEditorMetadata(); break;
            case "select-all": editor.focus(); editor.select(); break;
            case "clear-editor": clearEditor(); break;
            case "run-analysis": analyzeSource(); break;
            case "clear-results": resetOutput(); break;
            case "show-tokens": showOutputTab("tab-tokens"); break;
            case "show-symbols": showOutputTab("tab-symbols"); break;
            case "show-ast": showOutputTab("tab-ast"); break;
            case "show-problems": showOutputTab("tab-semantic"); break;
            case "show-language-help": showHelp("language"); break;
            case "show-about": showHelp("about"); break;
        }
    });
});

closeHelpButton.addEventListener("click", () => helpDialog.close());
helpDialog.addEventListener("click", (event) => {
    if (event.target === helpDialog) helpDialog.close();
});

analyzeButton.addEventListener("click", analyzeSource);
document.getElementById("problems-shortcut").addEventListener("click", () => {
    document.body.classList.remove("output-collapsed");
    toggleOutput.setAttribute("aria-pressed", "false");
    openTabById("tab-semantic");
});

toggleOutput.addEventListener("click", () => {
    const collapsed = document.body.classList.toggle("output-collapsed");
    toggleOutput.setAttribute("aria-pressed", String(collapsed));
    toggleOutput.title = collapsed ? "Mostrar resultados" : "Recolher resultados";
});

resizer.addEventListener("pointerdown", (event) => {
    if (window.innerWidth <= 900) return;
    resizer.setPointerCapture(event.pointerId);
    resizer.classList.add("dragging");
    document.body.style.cursor = "row-resize";
});

resizer.addEventListener("pointermove", (event) => {
    if (!resizer.hasPointerCapture(event.pointerId)) return;
    const rect = workspace.getBoundingClientRect();
    const requested = event.clientY - rect.top;
    const maximum = rect.height - 155;
    const height = Math.max(220, Math.min(requested, maximum));
    document.documentElement.style.setProperty("--editor-height", `${height}px`);
});

function stopResize(event) {
    if (resizer.hasPointerCapture(event.pointerId)) resizer.releasePointerCapture(event.pointerId);
    resizer.classList.remove("dragging");
    document.body.style.cursor = "";
}
resizer.addEventListener("pointerup", stopResize);
resizer.addEventListener("pointercancel", stopResize);

function setStatus(message, state) {
    analysisStatus.textContent = message;
    analysisIndicator.className = "status-item";
    analysisIndicator.classList.add(state === "running" ? "status-running" : state === "error" ? "status-error" : "status-ready");
}

function resetOutput() {
    tokensCount.textContent = "0";
    symbolsCount.textContent = "0";
    problemsCount.textContent = "0";
    statusErrors.textContent = "0";
    tokensBody.innerHTML = '<tr class="empty-row"><td colspan="5">Nenhum token disponível.</td></tr>';
    symbolsBody.innerHTML = '<tr class="empty-row"><td colspan="5">Nenhum símbolo disponível.</td></tr>';
    problemsBody.innerHTML = '<tr class="empty-row"><td colspan="4">Execute a análise para verificar o código.</td></tr>';
    astOutput.textContent = "// A árvore sintática aparecerá aqui.";
    semanticSummary.textContent = "Nenhuma análise executada";
    setStatus("Pronto", "ready");
}

async function analyzeSource() {
    const code = editor.value;
    if (!code.trim()) {
        renderProblem("Entrada", 1, 1, "O arquivo está vazio.");
        return;
    }

    const startedAt = performance.now();
    analyzeButton.disabled = true;
    analyzeButton.classList.add("loading");
    analyzeButton.querySelector(".button-label").textContent = "Analisando";
    setStatus("Analisando", "running");
    analysisTime.textContent = "…";

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code, filename: currentFilename })
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();

        if (!result.success) {
            renderFailure(result);
            return;
        }

        renderTokens(result.tokens || []);
        renderSymbols(result.symbols || []);
        astOutput.textContent = result.ast_pretty || "// Árvore sintática indisponível.";
        renderSuccess(result.semantic);
        setStatus("Análise concluída", "ready");
    } catch (error) {
        renderProblem("Conexão", 1, 1, `API indisponível: ${error.message}`);
        setStatus("Backend não conectado", "error");
    } finally {
        analysisTime.textContent = `${Math.round(performance.now() - startedAt)} ms`;
        analyzeButton.disabled = false;
        analyzeButton.classList.remove("loading");
        analyzeButton.querySelector(".button-label").textContent = "Analisar";
    }
}

function renderTokens(tokens) {
    tokensBody.replaceChildren();
    tokensCount.textContent = tokens.length;
    tokens.forEach((token, index) => {
        const row = document.createElement("tr");
        appendCells(row, [index + 1, token.type || token.tipo, token.lexeme ?? token.lexema ?? token.value ?? token.valor ?? "", token.line ?? token.linha ?? "—", token.column ?? token.coluna ?? "—"]);
        tokensBody.appendChild(row);
    });
}

function renderSymbols(symbols) {
    symbolsBody.replaceChildren();
    symbolsCount.textContent = symbols.length;
    symbols.forEach((symbol, index) => {
        const row = document.createElement("tr");
        appendCells(row, [symbol.order ?? symbol.ordem ?? index + 1, symbol.lexeme ?? symbol.lexema, symbol.category ?? symbol.categoria, symbol.data_type ?? symbol.tipo ?? "—", symbol.line ?? symbol.linha ?? "—"]);
        symbolsBody.appendChild(row);
    });
}

function appendCells(row, values) {
    values.forEach((value) => {
        const cell = document.createElement("td");
        cell.textContent = String(value);
        row.appendChild(cell);
    });
}

function renderSuccess(semantic = {}) {
    problemsBody.replaceChildren();
    const row = document.createElement("tr");
    const severity = document.createElement("td");
    severity.className = "severity-ok";
    severity.textContent = "OK";
    row.appendChild(severity);
    appendCells(row, ["—", "—", semantic.message || "Nenhuma inconsistência semântica encontrada."]);
    problemsBody.appendChild(row);
    problemsCount.textContent = "0";
    statusErrors.textContent = "0";
    semanticSummary.textContent = "0 erros";
}

function renderProblem(stage, line, column, description) {
    problemsBody.replaceChildren();
    const row = document.createElement("tr");
    const severity = document.createElement("td");
    severity.className = "severity-error";
    severity.textContent = "ERRO";
    row.appendChild(severity);
    appendCells(row, [line ?? "—", column ?? "—", `[${stage}] ${description}`]);
    problemsBody.appendChild(row);
    problemsCount.textContent = "1";
    statusErrors.textContent = "1";
    semanticSummary.textContent = "1 erro";
    document.body.classList.remove("output-collapsed");
    toggleOutput.setAttribute("aria-pressed", "false");
    openTabById("tab-semantic");
}

function renderFailure(result) {
    const stage = result.error_stage || "Análise";
    renderProblem(stage, result.line, result.column, result.error);
    setStatus(`Erro ${stage.toLowerCase()}`, "error");
}

updateEditorMetadata();
updateCursorPosition();
