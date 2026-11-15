const SAMPLES = {
    valido: `// Média ponderada de um aluno
int nota1 = 7;
int nota2 = 9;
int nota3 = 6;
int peso1 = 2;
int peso2 = 3;
int peso3 = 5;

int somaPesos = peso1 + peso2 + peso3;
float media = (nota1 * peso1 + nota2 * peso2 + nota3 * peso3) / (somaPesos * 1.0);

/* Operações com char: 'B' é promovido para int */
char conceito = 'B';
int codigo = conceito + 1;
int resto = codigo % 3;

float bonus = 0.5;
media = media + bonus * resto;

int resultado;
resultado = -(codigo - resto) * 2 + somaPesos;
return resultado;`,
    erros: `int total = 10;
float taxa = 2.5;
int parcial = total % taxa;
int nome = "Maria";
int total = 5;
desconto = total - 1;
int valor = taxa * 2;
int x = total / 0;
return parcial;
int sobra = 1;`,
    c_completo: `#include <stdio.h>
#define MAX 5

int soma(int v[], int n);

int main(void) {
    int numeros[MAX] = {4, 8, 15, 16, 23};
    int i, pares = 0;

    for (i = 0; i < MAX; i++) {
        if (numeros[i] % 2 == 0) {
            pares++;
        }
    }

    printf("Soma: %d\\n", soma(numeros, MAX));
    printf("Pares: %d\\n", pares);
    return 0;
}

int soma(int v[], int n) {
    int total = 0;
    for (int k = 0; k < n; k++)
        total += v[k];
    return total;
}`,
    c_erros: `#include <stdio.h>

int dobro(int x) {
    return x * 2;
}

int main() {
    int idade;
    int v[3] = {1, 2, 3};

    scanf("%d", idade);
    if (idade = 18) {
        printf("maior de idade\\n");
    }

    v[3] = dobro(idade, 2);
    total = v[0];
    return 0;
}`
};

const $ = (id) => document.getElementById(id);

const editor = $("code-editor");
const lineNumbers = $("line-numbers");
const analyzeButton = $("btn-analyze");
const summary = $("summary");
const tabs = document.querySelectorAll(".tab");

/* ---------- Editor ---------- */

function updateLineNumbers() {
    const total = editor.value.split("\n").length;
    lineNumbers.innerHTML = Array.from({ length: total }, (_, i) => `<span>${i + 1}</span>`).join("");
}

editor.addEventListener("input", updateLineNumbers);
editor.addEventListener("scroll", () => { lineNumbers.scrollTop = editor.scrollTop; });
editor.addEventListener("keydown", (event) => {
    if (event.key !== "Tab") return;
    event.preventDefault();
    editor.setRangeText("    ", editor.selectionStart, editor.selectionEnd, "end");
});

function loadCode(code) {
    editor.value = code;
    updateLineNumbers();
    clearResults();
    editor.focus();
}

$("sample-select").addEventListener("change", (event) => {
    loadCode(SAMPLES[event.target.value]);
});

// Arquivos .c do Windows costumam estar em ANSI (Windows-1252), não em UTF-8.
async function readSourceFile(file) {
    const bytes = await file.arrayBuffer();
    try {
        return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    } catch {
        return new TextDecoder("windows-1252").decode(bytes);
    }
}

$("source-file").addEventListener("change", async (event) => {
    const [file] = event.target.files;
    if (file) loadCode(await readSourceFile(file));
    event.target.value = "";
});

/* ---------- Abas ---------- */

function openTab(id) {
    tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === id));
    document.querySelectorAll(".page").forEach((page) => page.classList.toggle("active", page.id === id));
}

tabs.forEach((tab) => tab.addEventListener("click", () => openTab(tab.dataset.tab)));

/* ---------- Renderização ---------- */

function fillTable(bodyId, rows, emptyText, columns) {
    const body = $(bodyId);
    body.replaceChildren();

    if (rows.length === 0) {
        body.innerHTML = `<tr class="empty"><td colspan="${columns}">${emptyText}</td></tr>`;
        return;
    }

    rows.forEach((values) => {
        const row = document.createElement("tr");
        values.forEach((value) => {
            const cell = document.createElement("td");
            if (value && typeof value === "object") {
                cell.textContent = value.text;
                cell.className = value.className;
            } else {
                cell.textContent = String(value ?? "—");
            }
            row.appendChild(cell);
        });
        body.appendChild(row);
    });
}

function setSummary(text, state = "") {
    summary.textContent = text;
    summary.className = `summary ${state}`;
}

function plural(n, singular, pluralForm) {
    return `${n} ${n === 1 ? singular : pluralForm}`;
}

function clearResults() {
    setSummary("Clique em Analisar (ou Ctrl + Enter).");
    fillTable("problems-body", [], "Nenhuma análise executada.", 4);
    fillTable("tokens-body", [], "Nenhum token.", 5);
    fillTable("symbols-body", [], "Nenhum símbolo.", 5);
    $("ast-output").textContent = "";
    ["problems-count", "tokens-count", "symbols-count"].forEach((id) => { $(id).textContent = "0"; });
}

function showProblems(problems) {
    fillTable(
        "problems-body",
        problems.map((p) => [
            p.severity === "erro"
                ? { text: "Erro", className: "sev-error" }
                : { text: "Aviso", className: "sev-warning" },
            p.line,
            p.column,
            p.message
        ]),
        "Nenhum problema encontrado.",
        4
    );
    $("problems-count").textContent = problems.length;
}

function showResult(result) {
    const tokens = result.tokens || [];
    const symbols = result.symbols || [];
    const semantic = result.semantic || {};
    const diagnostics = semantic.diagnostics || [];

    fillTable("tokens-body", tokens.map((t, i) => [i + 1, t.tipo, t.lexema, t.linha, t.coluna]), "Nenhum token.", 5);
    fillTable("symbols-body", symbols.map((s) => [s.ordem, s.lexema, s.categoria, s.tipo, s.linha]), "Nenhum símbolo.", 5);
    $("tokens-count").textContent = tokens.length;
    $("symbols-count").textContent = symbols.length;
    $("ast-output").textContent = result.ast_pretty || "";

    showProblems(diagnostics);

    const errors = semantic.errors || 0;
    const warnings = semantic.warnings || 0;

    if (errors > 0) {
        setSummary(`✗ ${plural(errors, "erro", "erros")}, ${plural(warnings, "aviso", "avisos")}.`, "error");
    } else if (warnings > 0) {
        setSummary(`✓ Compilou, com ${plural(warnings, "aviso", "avisos")}.`, "warning");
    } else {
        setSummary("✓ Compilou sem erros nem avisos.", "ok");
    }

    openTab("tab-problems");
}

function showFailure(stage, message, line, column) {
    clearResults();
    showProblems([{ severity: "erro", message, line, column }]);
    setSummary(`✗ Erro na etapa ${stage}.`, "error");
    openTab("tab-problems");
}

/* ---------- Análise ---------- */

async function analyze() {
    if (!editor.value.trim()) {
        showFailure("Entrada", "O código está vazio.", 1, 1);
        return;
    }

    analyzeButton.disabled = true;
    analyzeButton.textContent = "Analisando…";

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: editor.value })
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const result = await response.json();

        if (result.success) {
            showResult(result);
        } else {
            showFailure(result.error_stage || "Análise", result.error, result.line, result.column);
        }
    } catch (error) {
        showFailure("Conexão", `Servidor indisponível (${error.message}). Rode: python server.py`, "—", "—");
    } finally {
        analyzeButton.disabled = false;
        analyzeButton.textContent = "Analisar";
    }
}

analyzeButton.addEventListener("click", analyze);

window.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        analyze();
    }
});

updateLineNumbers();
clearResults();
