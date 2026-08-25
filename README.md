# Compilador de C em Python (Do Zero)

Projeto estruturado para desenvolvimento de um compilador de subconjunto de C (C0 / Tiny C) em Python, sem dependências externas.

---

## Estrutura do Projeto

```text
.
├── main.py                         # Ponto de entrada (CLI do compilador)
├── README.md                       # Documentação do projeto
├── src/
│   ├── preprocessor/               # Pré-processamento (#include, #define)
│   ├── lexer/                      # Análise Léxica (Tokens)
│   ├── parser/                     # Análise Sintática (AST)
│   ├── semantic/                   # Análise Semântica (Tipos e Tabela de Símbolos)
│   ├── ir/                         # Representação Intermediária (TAC e Otimização)
│   ├── codegen/                    # Geração de Código (Assembly x86-64)
│   └── utils/                      # Erros e diagnósticos visuais
└── tests/                          # Testes unitários e programas C de exemplo
    └── c_samples/                  # Arquivos .c de teste incremental
```

---

## Pipeline de Compilação

1. **Pré-processador (`src/preprocessor/`)**: Processa diretivas básicas ou usa o pré-processador do sistema.
2. **Lexer (`src/lexer/`)**: Converte o código-fonte C em uma sequência de tokens tipados.
3. **Parser (`src/parser/`)**: Constrói a Árvore de Sintaxe Abstrata (AST) a partir dos tokens.
4. **Análise Semântica (`src/semantic/`)**: Valida tipos, escopos e coerência lógica da AST.
5. **Representação Intermediária (`src/ir/`)**: Converte a AST em instruções lineares (TAC) e aplica otimizações.
6. **Gerador de Código (`src/codegen/`)**: Emite o código Assembly x86-64 (.s) de acordo com a ABI.
7. **Montagem & Ligação (`main.py`)**: Chama o montador/ligador (`gcc` / `clang` / `as`+`ld`) para gerar o executável final.

---

## Roteiro de Testes Incremental (`tests/c_samples/`)

- `01_return_val.c`: `int main() { return 42; }`
- `02_arithmetic.c`: Operações aritméticas e precedência de operadores.
- `03_variables.c`: Declarações e atribuições de variáveis locais.
- `04_control_flow.c`: Estruturas `if`, `else`, `while` e `for`.
- `05_functions.c`: Chamadas e definições de funções com argumentos.
- `06_pointers.c`: Operadores de endereço (`&`), desreferência (`*`) e ponteiros.
