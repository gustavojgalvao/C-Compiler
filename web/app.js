// ==========================================================================
// Exemplos C pré-carregados
// ==========================================================================
const SAMPLES = {
    variables: `int main() {\n    int a = 10;\n    int b = 25;\n    int c = a + b;\n    return c;\n}`,
    arithmetic: `int main() {\n    return (10 + 5 * 2) - 8 / 2;\n}`,
    return_val: `int main() {\n    return 42;\n}`,
    control_flow: `int main() {\n    int i = 0;\n    int sum = 0;\n    while (i < 10) {\n        sum = sum + i;\n        i = i + 1;\n    }\n    if (sum == 45) {\n        return 1;\n    } else {\n        return 0;\n    }\n}`,
    functions: `int add(int a, int b) {\n    return a + b;\n}\n\nint main() {\n    int x = 20;\n    int y = 22;\n    return add(x, y);\n}`,
    pointers: `int main() {\n    int x = 100;\n    int *p = &x;\n    *p = 200;\n    return x;\n}`
};

// Elementos do DOM
const codeEditor = document.getElementById("code-editor");
const sampleSelect = document.getElementById("sample-select");
const btnCompile = document.getElementById("btn-compile");
const btnClear = document.getElementById("btn-clear");

const resultHero = document.getElementById("result-hero");
const resultVal = document.getElementById("result-val");
const resultStatus = document.getElementById("result-status");
const compileLogs = document.getElementById("compile-logs");

const metricTokens = document.getElementById("metric-tokens");
const metricFunctions = document.getElementById("metric-functions");
const metricAssembly = document.getElementById("metric-assembly");
const tokensCountBadge = document.getElementById("tokens-count");

const tokensList = document.getElementById("tokens-list");
const astView = document.getElementById("ast-view");
const irRaw = document.getElementById("ir-raw");
const irOptimized = document.getElementById("ir-optimized");
const assemblyView = document.getElementById("assembly-view");

const tabButtons = document.querySelectorAll(".tab-btn");
const tabPanes = document.querySelectorAll(".tab-pane");

// ==========================================================================
// Troca de Abas
// ==========================================================================
tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
        const targetTab = btn.getAttribute("data-tab");
        tabButtons.forEach(b => b.classList.remove("active"));
        tabPanes.forEach(p => p.classList.remove("active"));

        btn.classList.add("active");
        document.getElementById(targetTab).classList.add("active");
    });
});

// ==========================================================================
// Troca de Exemplos Prontos
// ==========================================================================
sampleSelect.addEventListener("change", (e) => {
    const val = e.target.value;
    if (SAMPLES[val]) {
        codeEditor.value = SAMPLES[val];
        compileCode();
    }
});

// Limpar editor
btnClear.addEventListener("click", () => {
    codeEditor.value = "";
    codeEditor.focus();
});

// Atalho de Teclado: Ctrl + Enter para compilar
window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        compileCode();
    }
});

btnCompile.addEventListener("click", compileCode);

// ==========================================================================
// Classificação Visual dos Tokens
// ==========================================================================
function getTokenCategory(type) {
    const kw = ["INT", "CHAR", "VOID", "RETURN", "IF", "ELSE", "WHILE", "FOR", "STRUCT", "SIZEOF"];
    const op = ["PLUS", "MINUS", "STAR", "SLASH", "PERCENT", "ASSIGN", "EQ_EQ", "BANG_EQ", "LESS", "LESS_EQ", "GREATER", "GREATER_EQ", "AND_AND", "OR_OR", "BANG", "TILDE", "INCREMENT", "DECREMENT", "AMPERSAND"];
    const delim = ["SEMICOLON", "COMMA", "DOT", "ARROW", "LPAREN", "RPAREN", "LBRACE", "RBRACE", "LBRACKET", "RBRACKET", "EOF"];

    if (kw.includes(type)) return "keyword";
    if (type === "IDENTIFIER") return "identifier";
    if (type === "INT_LITERAL") return "number";
    if (op.includes(type)) return "operator";
    if (delim.includes(type)) return "delimiter";
    return "default";
}

// ==========================================================================
// Função Principal de Compilação (API POST /api/compile)
// ==========================================================================
async function compileCode() {
    const code = codeEditor.value.trim();
    if (!code) {
        alert("Por favor, digite um código em C para compilar.");
        return;
    }

    // Animação de loading no botão
    btnCompile.style.opacity = "0.7";
    btnCompile.innerHTML = "<span>⏳ Compilando...</span>";

    try {
        const response = await fetch("/api/compile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: code })
        });

        const data = await response.json();

        if (data.success) {
            // 1. Atualizar Resultado
            resultHero.classList.remove("error");
            resultVal.textContent = data.result;
            resultStatus.textContent = "✔ Compilado com sucesso e executado na VM Python";

            metricTokens.textContent = data.metrics.tokens_count;
            metricFunctions.textContent = data.metrics.functions_count;
            metricAssembly.textContent = data.metrics.assembly_lines;
            tokensCountBadge.textContent = data.metrics.tokens_count;

            compileLogs.textContent = `[OK] Pipeline de compilação executado com sucesso!\n- Lexer: ${data.metrics.tokens_count} tokens identificados.\n- Parser: ${data.metrics.functions_count} função(ões) processadas na AST.\n- IR & Otimizador: Constant folding aplicado com sucesso.\n- CodeGen: ${data.metrics.assembly_lines} linhas de Assembly x86-64 geradas.\n- Execução: Retorno da função main() = ${data.result}`;

            // 2. Renderizar Tokens
            renderTokens(data.tokens);

            // 3. Renderizar AST
            astView.textContent = data.ast_pretty;

            // 4. Renderizar IR
            irRaw.textContent = data.ir_unoptimized;
            irOptimized.textContent = data.ir_optimized;

            // 5. Renderizar Assembly
            assemblyView.textContent = data.assembly;

            // Atualizar status das etapas
            document.querySelectorAll(".step-card").forEach(s => s.classList.add("success"));

        } else {
            // Exibir Erro
            resultHero.classList.add("error");
            resultVal.textContent = "Erro";
            resultStatus.textContent = `Falha na etapa: ${data.error_stage}`;
            compileLogs.textContent = `[FALHA] ${data.error}\nLinha: ${data.line}, Coluna: ${data.column}`;

            document.querySelectorAll(".step-card").forEach(s => s.classList.remove("success"));
        }

    } catch (err) {
        resultHero.classList.add("error");
        resultVal.textContent = "Erro de Conexão";
        resultStatus.textContent = "Não foi possível comunicar com o servidor Python.";
        compileLogs.textContent = String(err);
    } finally {
        btnCompile.style.opacity = "1";
        btnCompile.innerHTML = "<span>▶ Compilar & Executar</span><kbd>Ctrl + Enter</kbd>";
    }
}

// Renderiza a lista de chips de tokens
function renderTokens(tokens) {
    tokensList.innerHTML = "";
    tokens.forEach(t => {
        const cat = getTokenCategory(t.type);
        const chip = document.createElement("div");
        chip.className = "token-chip";
        chip.innerHTML = `
            <span class="token-type ${cat}">${t.type}</span>
            <span class="token-val">${escapeHtml(t.value || " ")}</span>
            <span class="token-pos">L${t.line}:C${t.column}</span>
        `;
        tokensList.appendChild(chip);
    });
}

function escapeHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Executar compilação inicial ao carregar
window.addEventListener("DOMContentLoaded", () => {
    compileCode();
});
