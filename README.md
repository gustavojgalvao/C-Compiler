# Mini Compilador C em Python

Front-end de um compilador para um subconjunto didático de C, escrito em Python puro (sem dependências externas). Executa as etapas **léxica**, **sintática** e **semântica** e exibe o resultado em uma interface web.

---

## Estrutura do Projeto

```text
.
├── main.py                     # CLI: python main.py [arquivo.c]
├── server.py                   # Servidor web (http://localhost:5000)
├── src/
│   ├── token.py                # Classe Token
│   ├── lexer.py                # Análise léxica (tokens, comentários)
│   ├── tabela_simbolos.py      # Tabela de símbolos
│   ├── arvore_sintatica.py     # Nós da AST
│   ├── parser.py               # Análise sintática (descendente recursiva)
│   ├── analisador_semantico.py # Análise semântica (tipos e escopo)
│   ├── compilador.py           # Pipeline: léxico → símbolos → sintático → semântico
│   └── erros.py                # ErroLexico / ErroSintatico com linha e coluna
├── web/                        # Interface (HTML, CSS, JS)
└── tests/                      # Testes unitários (unittest)
```

---

## Linguagem suportada

```c
// comentário de linha
int idade = 20;
float preco = 19.90;
char letra = 'A';
idade = idade + 2 * 3;   /* comentário de bloco */
return -idade;
```

Gramática:

```text
programa    -> comando* FIM
comando     -> declaracao | atribuicao | retorno
declaracao  -> ("int" | "float" | "char") IDENT ("=" expressao)? ";"
atribuicao  -> IDENT "=" expressao ";"
retorno     -> "return" expressao ";"
expressao   -> termo (("+" | "-") termo)*
termo       -> fator (("*" | "/" | "%") fator)*
fator       -> ("+" | "-") fator | NUMERO | NUMERO_REAL | CARACTERE | TEXTO | IDENT | "(" expressao ")"
```

## Análise semântica

O programa é tratado como o corpo de `int main()`. Os problemas são acumulados (não para no primeiro).

| Erros | Avisos |
|---|---|
| Variável não declarada (uso ou atribuição) | Conversão `float` → `int`/`char` (perda de precisão) |
| Variável declarada mais de uma vez | Variável usada antes de receber valor |
| Texto atribuído/retornado como valor numérico | Divisão por zero com divisor constante |
| Operador aritmético aplicado a texto | Código inalcançável após `return` |
| `%` com operando `float` | Variável declarada e nunca utilizada |

Promoções implícitas válidas: `char` → `int` → `float`.

---

## Como usar

```bash
# Interface web
python server.py            # abre em http://localhost:5000

# Linha de comando (código de exemplo ou arquivo)
python main.py
python main.py programa.c   # código de saída 1 se houver erros

# Testes
python -m unittest discover tests
```
