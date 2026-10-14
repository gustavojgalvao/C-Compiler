const SAMPLES = {
    variables: `int main() {\n    int a = 10;\n    int b = 25;\n    int c = a + b;\n    return c;\n}`,
    arithmetic: `int main() {\n    return (10 + 5 * 2) - 8 / 2;\n}`,
    return_val: `int main() {\n    return 42;\n}`,
    control_flow: `int main() {\n    int i = 0;\n    int sum = 0;\n    while (i < 10) {\n        sum = sum + i;\n        i = i + 1;\n    }\n    if (sum == 45) {\n        return 1;\n    } else {\n        return 0;\n    }\n}`,
    functions: `int add(int a, int b) {\n    return a + b;\n}\n\nint main() {\n    int x = 20;\n    int y = 22;\n    return add(x, y);\n}`,
    pointers: `int main() {\n    int x = 100;\n    int *p = &x;\n    *p = 200;\n    return x;\n}`
};

const codeEditor = document.getElementById("code-editor");
const lineNumbers = document.getElementById("line-numbers");
const sampleSelect = document.getElementById("sample-select");
const btnCompile = document.getElementById("btn-compile");
const btnClear = document.getElementById("btn-clear");
const engineStatus = document.getElementById("engine-status");
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
const pipelineSteps = document.querySelectorAll(".step-card");

function selectTab(button) {
    const targetId = button.dataset.tab;

    tabButtons.forEach((tab) => {
        const isActive = tab === button;
        tab.classList.toggle("active", isActive);
        tab.setAttribute("aria-selected", String(isActive));
    });

    tabPanes.forEach((pane) => {
        const isActive = pane.id === targetId;
        pane.classList.toggle("active", isActive);
        pane.hidden = !isActive;
    });
}

tabButtons.forEach((button) => button.addEventListener("click", () => selectTab(button)));

function updateLineNumbers() {
    const count = codeEditor.value.split("\n").length;
    lineNumbers.innerHTML = Array.from({ length: count }, (_, index) => index + 1).join("<br>");
}

codeEditor.addEventListener("input", updateLineNumbers);
codeEditor.addEventListener("scroll", () => {
    lineNumbers.scrollTop = codeEditor.scrollTop;
});

codeEditor.addEventListener("keydown", (event) => {
    if (event.key !== "Tab") return;
    event.preventDefault();

    const start = codeEditor.selectionStart;
    const end = codeEditor.selectionEnd;
    codeEditor.setRangeText("    ", start, end, "end");
    updateLineNumbers();
});

sampleSelect.addEventListener("change", (event) => {
    const sample = SAMPLES[event.target.value];
    if (!sample) return;

    codeEditor.value = sample;
    updateLineNumbers();
    compileCode();
});

btnClear.addEventListener("click", () => {
    codeEditor.value = "";
    updateLineNumbers();
    codeEditor.focus();
});

window.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        compileCode();
    }
});

btnCompile.addEventListener("click", compileCode);

function getTokenCategory(type) {
    const keywords = ["INT", "CHAR", "VOID", "RETURN", "IF", "ELSE", "WHILE", "FOR", "STRUCT", "SIZEOF"];
    const operators = ["PLUS", "MINUS", "STAR", "SLASH", "PERCENT", "ASSIGN", "EQ_EQ", "BANG_EQ", "LESS", "LESS_EQ", "GREATER", "GREATER_EQ", "AND_AND", "OR_OR", "BANG", "TILDE", "INCREMENT", "DECREMENT", "AMPERSAND"];
    const delimiters = ["SEMICOLON", "COMMA", "DOT", "ARROW", "LPAREN", "RPAREN", "LBRACE", "RBRACE", "LBRACKET", "RBRACKET", "EOF"];

    if (keywords.includes(type)) return "keyword";
    if (type === "IDENTIFIER") return "identifier";
    if (type === "INT_LITERAL") return "number";
    if (operators.includes(type)) return "operator";
    if (delimiters.includes(type)) return "delimiter";
    return "default";
}

function setCompiling(isCompiling) {
    btnCompile.disabled = isCompiling;
    btnCompile.classList.toggle("loading", isCompiling);
    btnCompile.querySelector(".btn-label").textContent = isCompiling ? "Compilando" : "Compilar";
}

function setPipelineComplete(isComplete) {
    pipelineSteps.forEach((step) => step.classList.toggle("success", isComplete));
}

function setEngineAvailability(isAvailable) {
    engineStatus.classList.toggle("offline", !isAvailable);
    engineStatus.title = isAvailable ? "Servidor de compilação disponível" : "Servidor de compilação indisponível";
    engineStatus.querySelector(".engine-status-label").textContent = isAvailable ? "Engine disponível" : "Engine offline";
}

async function compileCode() {
    const code = codeEditor.value.trim();
    if (!code) {
        resultHero.classList.add("error");
        resultVal.textContent = "Sem código";
        resultStatus.textContent = "Escreva ou selecione um exemplo para compilar.";
        compileLogs.textContent = "[erro] O editor está vazio.";
        return;
    }

    setCompiling(true);
    resultStatus.textContent = "Executando pipeline de compilação…";

    try {
        const response = await fetch("/api/compile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code })
        });

        if (!response.ok) throw new Error(`O servidor respondeu com HTTP ${response.status}.`);
        const data = await response.json();
        setEngineAvailability(true);

        if (data.success) {
            resultHero.classList.remove("error");
            resultVal.textContent = data.result;
            resultStatus.textContent = "Compilação concluída sem erros";
            metricTokens.textContent = data.metrics.tokens_count;
            metricFunctions.textContent = data.metrics.functions_count;
            metricAssembly.textContent = data.metrics.assembly_lines;
            tokensCountBadge.textContent = data.metrics.tokens_count;
            compileLogs.textContent = [
                "[ok] Compilação concluída",
                `lexer       ${data.metrics.tokens_count} tokens`,
                `parser      ${data.metrics.functions_count} função(ões)`,
                "optimizer   constant folding aplicado",
                `codegen     ${data.metrics.assembly_lines} linhas x86-64`,
                `main        retorno ${data.result}`
            ].join("\n");

            renderTokens(data.tokens);
            astView.textContent = data.ast_pretty;
            irRaw.textContent = data.ir_unoptimized;
            irOptimized.textContent = data.ir_optimized;
            assemblyView.textContent = data.assembly;
            setPipelineComplete(true);
        } else {
            resultHero.classList.add("error");
            resultVal.textContent = "Falhou";
            resultStatus.textContent = `Erro em ${data.error_stage || "compilação"}`;
            compileLogs.textContent = `[erro] ${data.error}\nlinha ${data.line}, coluna ${data.column}`;
            setPipelineComplete(false);
        }
    } catch (error) {
        setEngineAvailability(false);
        resultHero.classList.add("error");
        resultVal.textContent = "Offline";
        resultStatus.textContent = "Não foi possível acessar o servidor local";
        compileLogs.textContent = `[conexão] ${error.message || String(error)}`;
        setPipelineComplete(false);
    } finally {
        setCompiling(false);
    }
}

function renderTokens(tokens) {
    const fragment = document.createDocumentFragment();
    tokensList.replaceChildren();

    tokens.forEach((token) => {
        const chip = document.createElement("div");
        const type = document.createElement("span");
        const value = document.createElement("span");
        const position = document.createElement("span");

        chip.className = "token-chip";
        type.className = `token-type ${getTokenCategory(token.type)}`;
        value.className = "token-val";
        position.className = "token-pos";
        type.textContent = token.type;
        value.textContent = token.value || " ";
        position.textContent = `${token.line}:${token.column}`;
        chip.append(type, value, position);
        fragment.appendChild(chip);
    });

    tokensList.appendChild(fragment);
}

window.addEventListener("DOMContentLoaded", () => {
    updateLineNumbers();
    compileCode();
});
