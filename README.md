# Mini Compilador C em Python

Front-end de um compilador para um subconjunto de C, escrito em Python puro (sem bibliotecas externas). Ele lê um programa, confere se está correto em três níveis (**léxico**, **sintático** e **semântico**) e mostra o resultado no terminal ou numa página web. Não gera código executável.

---

## Sumário

1. [Linguagem aceita](#linguagem-aceita)
2. [Como executar](#como-executar)
3. [Arquitetura](#arquitetura)
4. [Análise léxica — `token.py` e `lexer.py`](#análise-léxica--tokenpy-e-lexerpy)
5. [Tabela de símbolos — `tabela_simbolos.py`](#tabela-de-símbolos--tabela_simbolospy)
6. [Análise sintática — `arvore_sintatica.py` e `parser.py`](#análise-sintática--arvore_sintaticapy-e-parserpy)
7. [Análise semântica — `analisador_semantico.py`](#análise-semântica--analisador_semanticopy)
8. [Erros e pipeline — `erros.py` e `compilador.py`](#erros-e-pipeline--errospy-e-compiladorpy)
9. [Pontos de entrada — `main.py` e `server.py`](#pontos-de-entrada--mainpy-e-serverpy)
10. [Interface web — `web/`](#interface-web--web)
11. [Testes](#testes)

---

## Linguagem aceita

Programas C comuns de exercício são aceitos:

```c
#include <stdio.h>
#define MAX 5

int soma(int v[], int n);            // protótipo

int main(void) {
    int numeros[MAX] = {4, 8, 15, 16, 23};
    int i, pares = 0;

    for (i = 0; i < MAX; i++) {
        if (numeros[i] % 2 == 0 && numeros[i] > 5) {
            pares++;
        }
    }

    printf("Soma: %d, pares: %d\n", soma(numeros, MAX), pares);
    return 0;
}

int soma(int v[], int n) {
    int total = 0;
    for (int k = 0; k < n; k++)
        total += v[k];
    return total;
}
```

| Recurso | Suportado |
| --- | --- |
| Tipos | `int`, `char`, `float`, `double`, `void`, `long`, `short`, `unsigned`, `signed`, `const`, `bool`, `size_t`, `FILE` |
| Structs | `struct Nome { ... }`, `typedef struct { ... } Nome;`, `s.campo`, `p->campo`, `{1, 2}` |
| Ponteiros e arrays | `int *p`, `&x`, `*p`, `int v[10]`, matrizes `int m[3][3]`, `{{1, 2}, {3, 4}}`, `char s[] = "oi"`, `NULL` |
| Funções | Definição, protótipo, parâmetros, recursão, `void` |
| Controle | `if`/`else`, `while`, `do-while`, `for`, `switch`/`case`/`default`, `break`, `continue`, `return` |
| Operadores | `+ - * / %`, `== != < > <= >=`, `&& \|\| !`, `& \| ^ ~ << >>`, `++ --`, `= += -= ...`, `?:`, vírgula, `(tipo)`, `sizeof` |
| Números | Decimais, reais (`2.5`, `1e3`, `2.5f`), hexadecimais (`0xFF`), octais (`017`) |
| Pré-processador | `#include` (ignorado) e `#define NOME valor` |
| Biblioteca | `stdio.h`, `string.h`, `ctype.h`, `stdlib.h`, `math.h`, `time.h`, `locale.h` e `conio.h` mais comuns (`printf`, `scanf`, `fgets`, `strlen`, `strcmp`, `toupper`, `malloc`, `sqrt`, `pow`, `rand`, `setlocale`, `getch`...) |

Uma função que o compilador não conhece gera **aviso** (não erro) quando o arquivo tem algum `#include`, porque ela provavelmente vem de uma biblioteca.

Arquivos salvos em UTF-8 (com ou sem BOM) ou em ANSI/Windows-1252 são lidos corretamente, tanto pelo `main.py` quanto pelo botão **Abrir .c**.

**Não suportado:** `enum`, `union`, macros com parâmetros (`#define MAX(a,b)`), `#ifdef`, ponteiros para função e funções com número variável de argumentos definidas pelo usuário.

**Modo simplificado:** um arquivo sem nenhuma função (só comandos soltos, como `int x = 5; return x;`) também é aceito e tratado como o corpo de `int main()`.

---

## Como executar

Requer Python 3.8 ou mais recente. Na pasta do projeto:

```bash
python -m unittest discover tests   # roda os testes
python main.py                      # analisa o exemplo embutido
python main.py programa.c           # analisa um arquivo (sai com código 1 se houver erros)
python server.py                    # interface em http://localhost:5000
```

---

## Arquitetura

```text
 Código-fonte ──► Lexer ──► Parser ──► Semântico ──► Resultado
                    │        (AST)    (acumula      (terminal
                    │                  erros e        ou web)
                    ▼                  avisos)          ▲
            Tabela de símbolos ─────────────────────────┘

 Lexer e Parser param na hora com ErroLexico / ErroSintatico.
```

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Linha de comando: analisa um arquivo `.c` e imprime tudo no terminal |
| `server.py` | Servidor HTTP: entrega a página web e responde `POST /api/analyze` |
| `src/compilador.py` | Pipeline: chama cada etapa na ordem e junta os resultados |
| `src/token.py` | Classe `Token` (tipo, lexema, linha, coluna) |
| `src/lexer.py` | Análise léxica: texto → tokens, comentários, `#include`/`#define` |
| `src/tabela_simbolos.py` | Tabela de símbolos montada a partir dos tokens |
| `src/arvore_sintatica.py` | Classes dos nós da árvore sintática (AST) |
| `src/parser.py` | Análise sintática: tokens → AST |
| `src/analisador_semantico.py` | Análise semântica: escopos, tipos, funções e chamadas |
| `src/erros.py` | Exceções com etapa, linha e coluna |
| `web/` | Interface: `index.html`, `style.css`, `app.js` |
| `tests/` | Testes unitários de cada etapa |

---

## Análise léxica — `token.py` e `lexer.py`

O lexer lê o texto caractere por caractere e o divide em **tokens**, as "palavras" da linguagem:

```text
if (x >= 10) x++;   →   IF  PAREN_ESQ  IDENTIFICADOR(x)  MAIOR_IGUAL  NUMERO(10)  PAREN_DIR
                        IDENTIFICADOR(x)  INCREMENTO  PONTO_VIRGULA  FIM
```

**`Token`** guarda `tipo`, `lexema` (o texto original), `linha` e `coluna` onde começa.

**`Lexer`** mantém um `cursor` sobre o texto e atualiza `linha` e `coluna` a cada passo.

| Método | O que faz |
| --- | --- |
| `caractere_atual()` / `espiar(n)` | Lê o caractere no cursor, ou `n` posições à frente, sem avançar |
| `avancar()` | Move o cursor; ao passar por `\n` soma 1 na linha e volta a coluna para 1 |
| `pular_espacos()` | Ignora espaços, comentários `//` e `/* */` e linhas do pré-processador (`#` no início da linha) |
| `ler_diretiva()` | Lê uma linha `#...`: guarda `#include` em `inclusoes` e registra `#define NOME valor` em `macros` |
| `proximo_token()` | Decide qual leitor chamar: dígito → número, letra → palavra, `'` → caractere, `"` → texto; tenta operadores de dois caracteres (`TOKENS_DUPLOS`) antes dos de um (`TOKENS_SIMPLES`) |
| `ler_numero()` | Inteiros, reais (`2.5`), notação científica (`1e3`) e sufixos (`2.5f`, `10L`). `12abc` é erro |
| `ler_palavra()` | Identificador ou palavra reservada (`PALAVRAS_RESERVADAS`) |
| `ler_caractere()` / `ler_texto()` | Literais `'A'` e `"texto"`, com escapes como `\n`, `\t`, `\0`, `\"` (`ler_escape()`) |
| `expandir_macro()` | Troca um nome definido por `#define` pelos tokens do seu valor (inclusive macros que usam outras) |
| `tokenizar()` | Junta todos os tokens até `FIM`, expandindo macros |

Qualquer caractere desconhecido (como `@` ou `$`) gera `ErroLexico` com a posição exata.

---

## Tabela de símbolos — `tabela_simbolos.py`

Lista cada palavra reservada, variável e função do programa, uma vez só, na ordem em que surgem. É montada direto da lista de tokens.

**`Simbolo`** guarda `ordem`, `lexema`, `categoria` (`PALAVRA_RESERVADA`, `IDENTIFICADOR` ou `FUNCAO`), `tipo` e `linha` da primeira aparição.

**`TabelaSimbolos.construir(tokens)`** acompanha as declarações enquanto percorre os tokens:

- uma palavra de tipo (`int`, `double`...) inicia uma declaração; `*` logo depois soma um nível de ponteiro (`int*`);
- o identificador seguinte recebe esse tipo; depois de uma vírgula no mesmo nível de parênteses (`int a, b;`) o próximo também recebe;
- um identificador seguido de `(` é registrado como `FUNCAO`;
- `;`, `{`, `}` ou o fechamento do parêntese onde a declaração começou encerram a declaração.

A tabela não sabe em que escopo cada nome vale; isso é trabalho do analisador semântico.

---

## Análise sintática — `arvore_sintatica.py` e `parser.py`

O parser confere se os tokens formam frases válidas de C e monta a **árvore sintática abstrata (AST)**. É um parser *descendente recursivo*: cada regra da gramática vira um método.

### Gramática

```text
programa     -> externo* FIM
externo      -> funcao | declaracao | comando
funcao       -> tipo IDENT "(" parametros ")" (bloco | ";")
declaracao   -> tipo declarador ("," declarador)* ";"
declarador   -> "*"* IDENT ("[" expressao? "]")? ("=" (atribuicao | "{" lista "}"))?
comando      -> bloco | if | while | do-while | for | switch
              | break ";" | continue ";" | return expressao? ";"
              | declaracao | expressao ";" | ";"

expressao    -> atribuicao
atribuicao   -> condicional (("=" | "+=" | "-=" | "*=" | "/=" | "%=") atribuicao)?
condicional  -> ou ("?" expressao ":" condicional)?
ou           -> e ("||" e)*
e            -> igualdade ("&&" igualdade)*
igualdade    -> relacional (("==" | "!=") relacional)*
relacional   -> soma (("<" | ">" | "<=" | ">=") soma)*
soma         -> termo (("+" | "-") termo)*
termo        -> unario (("*" | "/" | "%") unario)*
unario       -> ("-" | "+" | "!" | "~" | "&" | "*" | "++" | "--") unario
              | "(" tipo ")" unario | "sizeof" ... | posfixo
posfixo      -> primario ("(" argumentos ")" | "[" expressao "]" | "++" | "--")*
primario     -> NUMERO | NUMERO_REAL | CARACTERE | TEXTO | IDENT | "(" expressao ")"
```

A **precedência** sai da gramática: cada nível chama o seguinte, mais forte. `ler_binaria(nivel)` implementa todos os níveis binários com uma única função, guiada pela lista `NIVEIS_BINARIOS`. Assim `a == 1 || b < 2 && c` vira `(a == 1) || ((b < 2) && c)`, e `10 - 4 - 3` vira `(10 - 4) - 3`. A atribuição é associativa à direita: `a = b = 0`.

### Nós da AST

| Grupo | Classes |
| --- | --- |
| Estrutura | `Programa`, `Funcao` (com `corpo = None` num protótipo), `Parametro` |
| Declarações | `Declaracao` (`tipo`, `nome`, `inicializador`, `eh_array`, `tamanho`), `ListaInicializadora` |
| Comandos | `Bloco`, `Se`, `Enquanto`, `FacaEnquanto`, `Para`, `Escolha` + `Caso`, `Pare`, `Continue`, `Retorno`, `ComandoVazio` |
| Expressões | `Numero`, `NumeroReal`, `Caractere`, `Texto`, `Identificador`, `OperacaoBinaria`, `OperacaoUnaria`, `IncrementoDecremento`, `Atribuicao` (`alvo`, `operador`, `valor`), `Condicional` (`?:`), `Chamada`, `Indexacao`, `Conversao` (cast), `Tamanho` (`sizeof`) |

Todo nó guarda `linha` e `coluna` e tem `formatar(nivel)`, que gera o texto indentado da aba "Árvore". Uma expressão usada como comando (`x = 1;`, `f();`) entra na árvore diretamente, sem nó intermediário.

### Métodos do `Parser`

- `token_atual()`, `espiar()`, `avancar()`, `verificar(*tipos)` e `consumir(tipo, mensagem)` navegam pelos tokens; `consumir` lança `ErroSintatico` se vier outro token.
- `analisar()` → `ler_externo()`: depois de um tipo e um nome, um `(` indica função (`ler_funcao`), senão é declaração (`ler_declaradores`).
- `ler_tipo_base()` junta palavras como `unsigned long int` num tipo só; `ler_ponteiros()` lê os `*`.
- `ler_comando()` escolhe pelo primeiro token: `{`, `if`, `while`, `do`, `for`, `switch`, `return`, `break`, `continue`, tipo (declaração) ou expressão. Devolve uma lista, porque `int a, b;` gera duas declarações.
- `ler_comando_unico()` lê o corpo de `if`/laços e proíbe declaração solta ali.
- `ler_unario()` reconhece um cast quando um `(` é seguido de um tipo.

Exemplo: `int a = 1 + 2 * 3;` gera:

```text
Programa
  Declaracao (tipo=int, nome=a)
    OperacaoBinaria (+)
      Numero (1)
      OperacaoBinaria (*)
        Numero (2)
        Numero (3)
```

---

## Análise semântica — `analisador_semantico.py`

Confere o **significado** do programa: se nomes existem no escopo certo, se os tipos combinam e se as funções são chamadas corretamente. Diferente das etapas anteriores, **não para no primeiro problema**: acumula erros e avisos.

### Como funciona

1. **Embutidos:** registra as funções da biblioteca (`FUNCOES_EMBUTIDAS`, com tipo de retorno, parâmetros e se aceitam argumentos extras, como `printf`) e constantes como `NULL` e `EOF`.
2. **1ª passada:** conhece todas as funções do arquivo (`InfoFuncao`). Assim, chamar uma função definida mais abaixo gera só um aviso, não um erro.
3. **2ª passada:** visita tudo em ordem. `visitar(no)` despacha pelo nome da classe (`Se` → `visitar_Se`...), o padrão *visitor*. Expressões **devolvem o seu tipo** (`"int"`, `"double"`, `"char*"`...) ou `None` quando já houve erro, evitando mensagens em cascata.

**Escopos** são uma pilha de dicionários: global → função (parâmetros e corpo) → cada bloco `{ }` e cada `for`. Uma variável interna pode esconder outra de fora com o mesmo nome. Ao fechar um escopo, variáveis nunca lidas geram aviso.

### Regras de tipo

- Contas: `char` → `int` → `float` → `double`; o resultado é o tipo "maior" dos dois lados. `1.5` é `double`, `1.5f` é `float`.
- Guardar real em inteiro é permitido, com aviso de perda de precisão.
- Um array vira ponteiro ao ser usado (`int v[3]` → `int*`). Ponteiro + inteiro é ponteiro; ponteiro − ponteiro é inteiro.
- Ponteiros só recebem ponteiro do mesmo tipo, `void*` (ex.: `malloc`, `NULL`) ou a constante `0`.
- Texto (`"..."`) é `char*`.

### O que é verificado

| Severidade | Situação | Exemplo |
| --- | --- | --- |
| Erro | Variável ou função não declarada | `total = 1;`, `calcular();` |
| Erro | Nome declarado duas vezes no mesmo escopo | `int a; int a;` |
| Erro | Tipos incompatíveis em atribuição, argumento ou retorno | `int n = "Maria";`, `char *s = 5;` |
| Erro | Número errado de argumentos | `dobro(1, 2)` para `int dobro(int x)` |
| Erro | `return valor` em função `void` | `void f() { return 1; }` |
| Erro | Operador com tipos inválidos | `7 % 2.5`, `"x" * 2`, `*x` com `x` inteiro |
| Erro | `break`/`continue` fora de laço | `break;` solto no `main` |
| Erro | Atribuir a array inteiro ou a algo que não é variável | `v = 0;`, `5 = x;` |
| Erro | `case` repetido ou não constante | `case 1: ... case 1:` |
| Erro | Comando fora de função (quando o arquivo tem funções) | `x = 2;` no nível global |
| Erro | Função declarada, usada e nunca definida | protótipo sem corpo |
| Aviso | Real guardado em inteiro | `int v = 2.5 * 2;` |
| Aviso | Variável lida antes de receber valor | `int a; int b = a;` |
| Aviso | `scanf` sem `&` | `scanf("%d", idade);` |
| Aviso | Quantidade de `%` diferente da de valores no `printf`/`scanf` | `printf("%d %d", x);` |
| Aviso | `=` usado como condição | `if (x = 18)` |
| Aviso | Índice constante fora do array | `v[3]` com `int v[3]` |
| Aviso | Função pode terminar sem `return` | `if (a) return 1;` e mais nada |
| Aviso | Divisão por zero constante | `x / 0` |
| Aviso | Código depois de `return`/`break`/`continue` | `return 0; x++;` |
| Aviso | Expressão sem efeito | `x + 1;` |
| Aviso | Variável declarada e nunca lida | `int sobra = 1;` |
| Aviso | Função chamada antes de ser declarada | uso antes do protótipo |

Passar `&x` (como no `scanf`) conta como inicializar `x`. No modo simplificado, o `return` deve ser compatível com `int`.

No fim, os diagnósticos são ordenados por linha e coluna. `erros`, `avisos` e `sucesso` filtram a lista; `resumo()` gera a frase final; `para_dict()` prepara o JSON da interface.

---

## Erros e pipeline — `erros.py` e `compilador.py`

**`erros.py`** define as exceções. A base `ErroCompilacao` guarda `mensagem`, `linha`, `coluna` e o atributo `etapa`, e monta o texto "mensagem na linha X, coluna Y".

- `ErroLexico` (`etapa = "Léxica"`) recebe a posição diretamente.
- `ErroSintatico` (`etapa = "Sintática"`) recebe o token problemático e tira a posição dele.

**`compilador.py`** tem `compilar(codigo)`, o único lugar que conhece a ordem das etapas:

```python
tokens    = Lexer(codigo).tokenizar()
tabela    = TabelaSimbolos().construir(tokens)
arvore    = Parser(tokens).analisar()
semantico = AnalisadorSemantico().analisar(arvore)
```

Devolve um `ResultadoCompilacao` com `tokens`, `tabela`, `arvore`, `semantico` e `sucesso` (verdadeiro quando não há erros semânticos). Terminal e web usam essa mesma função.

---

## Pontos de entrada — `main.py` e `server.py`

**`main.py`**: `main(argumentos)` lê o arquivo passado (ou usa `CODIGO_EXEMPLO`), chama `compilar()` e imprime tokens, tabela de símbolos, árvore e diagnósticos. Com erro léxico ou sintático, imprime só o erro. Sai com código 0 sem erros e 1 com erros.

**`server.py`**: servidor feito com `http.server`, na porta 5000. A classe `CompilerHandler`:

- herda de `SimpleHTTPRequestHandler` apontado para `web/`, servindo a página em requisições `GET`;
- em `do_POST` atende `/api/analyze`: lê `{"code": "..."}`, chama `compilar()` e responde em JSON;
- usa `enviar_json()` e `enviar_erro()` para montar as respostas.

Resposta de sucesso:

```json
{
  "success": true,
  "tokens":  [{"tipo": "INT", "lexema": "int", "linha": 1, "coluna": 1}],
  "symbols": [{"ordem": 1, "lexema": "main", "categoria": "FUNCAO", "tipo": "int", "linha": 1}],
  "ast_pretty": "Programa\n  Funcao ...",
  "semantic": {"success": false, "errors": 1, "warnings": 0, "message": "...",
               "diagnostics": [{"severity": "erro", "message": "...", "line": 1, "column": 9}]}
}
```

Erro léxico ou sintático: `{"success": false, "error_stage": "Sintática", "error": "...", "line": 2, "column": 1}`. Requisições inválidas recebem `error_stage = "Entrada"`; falhas inesperadas, `"Interna"`, sem derrubar o servidor.

---

## Interface web — `web/`

Editor à esquerda, resultado à direita (empilhados em telas estreitas). Sem frameworks nem recursos externos.

- **`index.html`**: topo com título, **Exemplos**, **Abrir .c** e **Analisar**; abaixo, o editor (`<textarea>` com números de linha) e o painel de resultado, com uma frase de resumo e as abas Problemas, Tokens, Símbolos e Árvore.
- **`style.css`**: cores em variáveis no `:root` (`--success`, `--warning`, `--error`) e *grid* para os dois painéis; abaixo de 860 px os painéis ficam empilhados.
- **`app.js`**:

| Parte | O que faz |
| --- | --- |
| `SAMPLES` | Quatro exemplos: modo simplificado válido e com erros, C completo válido e com erros |
| `updateLineNumbers()` | Redesenha os números de linha e acompanha a rolagem; Tab insere 4 espaços |
| `loadCode()` | Coloca um exemplo ou arquivo aberto no editor e limpa o resultado |
| `openTab(id)` | Troca a aba visível |
| `analyze()` | Envia o código para `POST /api/analyze`; também disparado por Ctrl + Enter |
| `showResult()` | Preenche as abas e o resumo: verde sem problemas, amarelo só com avisos, vermelho com erros |
| `showFailure()` | Mostra um erro léxico, sintático ou de conexão na aba Problemas |
| `fillTable()` | Monta as linhas de qualquer tabela, ou a mensagem de vazio |

Os dados do servidor são inseridos com `textContent`, nunca como HTML, então um `<script>` digitado no editor aparece como texto e não é executado.

---

## Testes

Usam `unittest`, da biblioteca padrão:

| Arquivo | Testes | O que cobre |
| --- | --- | --- |
| `tests/test_lexer.py` | 9 | Tipos de token, literais, linha/coluna, comentários, erros léxicos |
| `tests/test_parser.py` | 10 | Comandos, precedência, associatividade, parênteses, menos unário, `formatar()`, erros de sintaxe |
| `tests/test_semantic.py` | 17 | Regras de tipo e de variáveis no modo simplificado, acúmulo de erros, `para_dict()` |
| `tests/test_programas_c.py` | 23 | Operadores de C, `#include`/`#define`, funções, laços, `switch`, ponteiros, escopos, `printf`/`scanf`, structs, matrizes, BOM, hexadecimal e os programas de `tests/c_samples/` |
