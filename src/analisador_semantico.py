"""
Análise semântica do Mini Compilador C.

Percorre a árvore sintática verificando escopos, tipos e o uso de
variáveis e funções. Os problemas são acumulados como diagnósticos
(erros e avisos) em vez de interromper a análise no primeiro.

Se o programa não tiver funções, os comandos soltos são tratados como o
corpo de 'int main()' (modo simplificado). Se tiver, comandos fora de
funções são erro, como em C.
"""

import re

from src.arvore_sintatica import (
    Funcao, Declaracao, DefinicaoStruct, ListaInicializadora, Bloco, Se, Enquanto,
    FacaEnquanto, Para, Escolha, Retorno, Pare, Continue,
    Numero, NumeroReal, Caractere, Texto, Identificador, OperacaoUnaria,
    OperacaoBinaria, IncrementoDecremento, Atribuicao, Condicional, Chamada,
    Indexacao, Conversao, Acesso, Sequencia, EXPRESSOES,
)
from src.lexer import ESCAPES


ERRO = "erro"
AVISO = "aviso"

# Tipo de retorno do programa no modo simplificado (comandos soltos).
TIPO_RETORNO = "int"

INTEIROS = {"int", "char"}
FLUTUANTES = {"float", "double"}

# nome: (tipo de retorno, tipos dos parâmetros fixos, aceita argumentos extras?)
FUNCOES_EMBUTIDAS = {
    # stdio.h
    "printf": ("int", ["char*"], True),
    "scanf": ("int", ["char*"], True),
    "sprintf": ("int", ["char*", "char*"], True),
    "snprintf": ("int", ["char*", "int", "char*"], True),
    "sscanf": ("int", ["char*", "char*"], True),
    "fprintf": ("int", ["void*", "char*"], True),
    "fscanf": ("int", ["void*", "char*"], True),
    "puts": ("int", ["char*"], False),
    "putchar": ("int", ["int"], False),
    "getchar": ("int", [], False),
    "gets": ("char*", ["char*"], False),
    "fgets": ("char*", ["char*", "int", "void*"], False),
    "fputs": ("int", ["char*", "void*"], False),
    "fopen": ("void*", ["char*", "char*"], False),
    "fclose": ("int", ["void*"], False),
    "fgetc": ("int", ["void*"], False),
    "fputc": ("int", ["int", "void*"], False),
    "feof": ("int", ["void*"], False),
    "fflush": ("int", ["void*"], False),
    "getc": ("int", ["void*"], False),
    "setbuf": ("void", ["void*", "char*"], False),
    # string.h
    "strlen": ("int", ["char*"], False),
    "strcpy": ("char*", ["char*", "char*"], False),
    "strncpy": ("char*", ["char*", "char*", "int"], False),
    "strcat": ("char*", ["char*", "char*"], False),
    "strncat": ("char*", ["char*", "char*", "int"], False),
    "strcmp": ("int", ["char*", "char*"], False),
    "strncmp": ("int", ["char*", "char*", "int"], False),
    "strchr": ("char*", ["char*", "int"], False),
    "strrchr": ("char*", ["char*", "int"], False),
    "strstr": ("char*", ["char*", "char*"], False),
    "strcspn": ("int", ["char*", "char*"], False),
    "strtok": ("char*", ["char*", "char*"], False),
    "strdup": ("char*", ["char*"], False),
    "memset": ("void*", ["void*", "int", "int"], False),
    "memcpy": ("void*", ["void*", "void*", "int"], False),
    # ctype.h
    "toupper": ("int", ["int"], False),
    "tolower": ("int", ["int"], False),
    "isdigit": ("int", ["int"], False),
    "isalpha": ("int", ["int"], False),
    "isalnum": ("int", ["int"], False),
    "isspace": ("int", ["int"], False),
    "isupper": ("int", ["int"], False),
    "islower": ("int", ["int"], False),
    "ispunct": ("int", ["int"], False),
    # stdlib.h
    "atoi": ("int", ["char*"], False),
    "atol": ("int", ["char*"], False),
    "atof": ("double", ["char*"], False),
    "malloc": ("void*", ["int"], False),
    "calloc": ("void*", ["int", "int"], False),
    "realloc": ("void*", ["void*", "int"], False),
    "free": ("void", ["void*"], False),
    "abs": ("int", ["int"], False),
    "labs": ("int", ["int"], False),
    "rand": ("int", [], False),
    "srand": ("void", ["int"], False),
    "exit": ("void", ["int"], False),
    "system": ("int", ["char*"], False),
    # math.h
    "fabs": ("double", ["double"], False),
    "sqrt": ("double", ["double"], False),
    "pow": ("double", ["double", "double"], False),
    "ceil": ("double", ["double"], False),
    "floor": ("double", ["double"], False),
    "round": ("double", ["double"], False),
    "fmod": ("double", ["double", "double"], False),
    "exp": ("double", ["double"], False),
    "log": ("double", ["double"], False),
    "log10": ("double", ["double"], False),
    "sin": ("double", ["double"], False),
    "cos": ("double", ["double"], False),
    "tan": ("double", ["double"], False),
    "atan": ("double", ["double"], False),
    # time.h, locale.h, conio.h, windows.h
    "time": ("int", ["void*"], False),
    "clock": ("int", [], False),
    "setlocale": ("char*", ["int", "char*"], False),
    "getch": ("int", [], False),
    "getche": ("int", [], False),
    "Sleep": ("void", ["int"], False),
    "sleep": ("int", ["int"], False),
}

CONSTANTES_EMBUTIDAS = {
    "NULL": "void*",
    "stdin": "void*",
    "stdout": "void*",
    "stderr": "void*",
    "EOF": "int",
    "RAND_MAX": "int",
    "CLOCKS_PER_SEC": "int",
    "EXIT_SUCCESS": "int",
    "EXIT_FAILURE": "int",
    "LC_ALL": "int",
    "LC_CTYPE": "int",
    "LC_NUMERIC": "int",
    "true": "int",
    "false": "int",
    "M_PI": "double",
    "INT_MAX": "int",
    "INT_MIN": "int",
}

# Especificadores de formato do printf/scanf, como %d, %.2f, %lf, %s.
FORMATO = re.compile(
    r"%(?:%|[-+ #0]*(\d+|\*)?(?:\.(\d+|\*))?(hh|h|ll|l|L|z|j|t)?([diouxXfFeEgGcsp]))"
)


def eh_ponteiro(tipo):
    return tipo is not None and tipo.endswith("*")


def eh_inteiro(tipo):
    return tipo in INTEIROS


def eh_flutuante(tipo):
    return tipo in FLUTUANTES


def eh_aritmetico(tipo):
    return eh_inteiro(tipo) or eh_flutuante(tipo)


def eh_escalar(tipo):
    return eh_aritmetico(tipo) or eh_ponteiro(tipo)


def apontado(tipo):
    """Tipo do valor para onde um ponteiro aponta: 'int*' -> 'int'."""
    return tipo[:-1]


def promover(a, b):
    """Tipo do resultado de uma conta entre dois tipos aritméticos."""
    if "double" in (a, b):
        return "double"
    if "float" in (a, b):
        return "float"
    return "int"


def plural(n, singular, plural_):
    return f"{n} {singular if n == 1 else plural_}"


class Diagnostico:
    def __init__(self, severidade, mensagem, linha, coluna=None):
        self.severidade = severidade
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna

    def para_dict(self):
        return {
            "severity": self.severidade,
            "message": self.mensagem,
            "line": self.linha,
            "column": self.coluna,
        }

    def __repr__(self):
        posicao = f"linha {self.linha}"
        if self.coluna is not None:
            posicao += f", coluna {self.coluna}"
        return f"[{self.severidade.upper()}] {self.mensagem} ({posicao})"


class Variavel:
    def __init__(self, nome, tipo, linha, coluna, inicializada,
                 dimensoes=None, eh_parametro=False, embutida=False):
        self.nome = nome
        self.tipo = tipo
        self.linha = linha
        self.coluna = coluna
        self.inicializada = inicializada
        # Tamanho de cada dimensão de um array (None se desconhecido).
        self.dimensoes = dimensoes or []
        self.eh_parametro = eh_parametro
        self.embutida = embutida
        self.utilizada = embutida
        self.aviso_nao_inicializada = False

    @property
    def eh_array(self):
        return bool(self.dimensoes)

    @property
    def tamanho(self):
        return self.dimensoes[0] if self.dimensoes else None

    @property
    def tipo_valor(self):
        """Tipo ao aparecer numa expressão: um array vira ponteiro."""
        return self.tipo + "*" * len(self.dimensoes)

    def para_dict(self):
        tipo = self.tipo + "".join(
            f"[{d if d is not None else ''}]" for d in self.dimensoes
        )
        return {
            "name": self.nome,
            "type": tipo,
            "line": self.linha,
            "initialized": self.inicializada,
            "used": self.utilizada,
        }


class InfoFuncao:
    def __init__(self, nome, tipo_retorno, parametros, variadica, linha,
                 no=None, embutida=False):
        self.nome = nome
        self.tipo_retorno = tipo_retorno
        self.parametros = parametros
        self.variadica = variadica
        self.linha = linha
        self.no = no
        self.embutida = embutida
        self.declarada = embutida
        self.definida = embutida
        self.linha_definicao = None
        self.utilizada = False
        self.avisou_antes_de_declarar = False


class AnalisadorSemantico:
    def __init__(self, inclusoes=None):
        # Arquivos de #include: com eles, uma função desconhecida provavelmente
        # vem de uma biblioteca e gera aviso em vez de erro.
        self.inclusoes = list(inclusoes or [])
        self.funcoes_desconhecidas = set()
        self.structs = {}           # nome -> {"campos": {nome: (tipo, dimensões)}, ...}
        self.escopos = []
        self.todas_variaveis = []
        self.funcoes = {}
        self.diagnosticos = []
        self.funcao_atual = None
        self.profundidade_laco = 0
        self.profundidade_escolha = 0
        self.modo_simplificado = False

    # ------------------------------------------------------------------
    # Interface pública
    # ------------------------------------------------------------------

    def analisar(self, programa):
        self.abrir_escopo()
        self.registrar_embutidos()

        funcoes = [c for c in programa.comandos if isinstance(c, Funcao)]
        self.modo_simplificado = not funcoes

        # 1ª passada: conhece todas as funções (permite avisar sobre uso
        # antes da declaração em vez de acusar "não declarada").
        for funcao in funcoes:
            existente = self.funcoes.get(funcao.nome)
            if existente is None or existente.embutida:
                self.funcoes[funcao.nome] = InfoFuncao(
                    funcao.nome,
                    funcao.tipo_retorno,
                    [p.tipo_efetivo for p in funcao.parametros],
                    funcao.variadica,
                    funcao.linha,
                    no=funcao
                )

        # 2ª passada: analisa tudo em ordem.
        validos = []
        for comando in programa.comandos:
            if (
                not self.modo_simplificado
                and not isinstance(comando, (Funcao, Declaracao, DefinicaoStruct))
            ):
                self.errar(
                    "Comando fora de uma função: em C, comandos devem "
                    "ficar dentro de funções como main()",
                    comando
                )
            else:
                validos.append(comando)

        self.visitar_lista(validos)

        # Variáveis globais de verdade não geram aviso de "nunca utilizada".
        self.fechar_escopo(avisar=self.modo_simplificado)

        if not self.modo_simplificado:
            self.verificar_funcoes_do_programa()

        self.diagnosticos.sort(
            key=lambda d: (d.linha or 0, d.coluna or 0)
        )

        return self

    @property
    def erros(self):
        return [d for d in self.diagnosticos if d.severidade == ERRO]

    @property
    def avisos(self):
        return [d for d in self.diagnosticos if d.severidade == AVISO]

    @property
    def sucesso(self):
        return not self.erros

    def resumo(self):
        total_erros = len(self.erros)
        total_avisos = len(self.avisos)

        if total_erros == 0 and total_avisos == 0:
            return "Nenhuma inconsistência semântica encontrada."

        partes = []
        if total_erros:
            partes.append(plural(total_erros, "erro", "erros"))
        if total_avisos:
            partes.append(plural(total_avisos, "aviso", "avisos"))

        return "Análise semântica concluída com " + " e ".join(partes) + "."

    def para_dict(self):
        return {
            "success": self.sucesso,
            "errors": len(self.erros),
            "warnings": len(self.avisos),
            "message": self.resumo(),
            "diagnostics": [d.para_dict() for d in self.diagnosticos],
            "variables": [v.para_dict() for v in self.todas_variaveis],
        }

    # ------------------------------------------------------------------
    # Auxiliares: diagnósticos, escopos, despacho
    # ------------------------------------------------------------------

    def errar(self, mensagem, no):
        self.diagnosticos.append(
            Diagnostico(ERRO, mensagem, no.linha, getattr(no, "coluna", None))
        )

    def avisar(self, mensagem, no):
        self.diagnosticos.append(
            Diagnostico(AVISO, mensagem, no.linha, getattr(no, "coluna", None))
        )

    def registrar_embutidos(self):
        for nome, (retorno, parametros, variadica) in FUNCOES_EMBUTIDAS.items():
            self.funcoes[nome] = InfoFuncao(
                nome, retorno, parametros, variadica, 0, embutida=True
            )

        for nome, tipo in CONSTANTES_EMBUTIDAS.items():
            self.escopos[0][nome] = Variavel(
                nome, tipo, 0, None, inicializada=True, embutida=True
            )

    def abrir_escopo(self):
        self.escopos.append({})

    def fechar_escopo(self, avisar=True):
        escopo = self.escopos.pop()

        if not avisar:
            return

        for variavel in escopo.values():
            if not (variavel.utilizada or variavel.eh_parametro or variavel.embutida):
                self.diagnosticos.append(Diagnostico(
                    AVISO,
                    f"Variável '{variavel.nome}' declarada mas nunca utilizada",
                    variavel.linha,
                    variavel.coluna
                ))

    def buscar_variavel(self, nome):
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        return None

    def declarar_variavel(self, variavel, no):
        escopo = self.escopos[-1]
        existente = escopo.get(variavel.nome)

        if existente is not None and not existente.embutida:
            self.errar(
                f"Variável '{variavel.nome}' já foi declarada na linha "
                f"{existente.linha}",
                no
            )
            return

        escopo[variavel.nome] = variavel
        self.todas_variaveis.append(variavel)

    def visitar(self, no):
        metodo = getattr(self, f"visitar_{type(no).__name__}", None)

        if metodo is None:
            raise NotImplementedError(
                f"Nó sem regra semântica: {type(no).__name__}"
            )

        return metodo(no)

    def visitar_lista(self, comandos):
        """Visita comandos em sequência, avisando sobre código inalcançável."""
        encerrou = None
        avisado = False

        for comando in comandos:
            if encerrou is not None and not avisado:
                palavra, linha = encerrou
                self.avisar(
                    f"Código inalcançável: comando após '{palavra}' (linha {linha})",
                    comando
                )
                avisado = True

            self.visitar_comando(comando)

            if encerrou is None:
                if isinstance(comando, Retorno):
                    encerrou = ("return", comando.linha)
                elif isinstance(comando, Pare):
                    encerrou = ("break", comando.linha)
                elif isinstance(comando, Continue):
                    encerrou = ("continue", comando.linha)

    def visitar_comando(self, comando):
        if not isinstance(comando, EXPRESSOES):
            self.visitar(comando)
            return

        self.visitar(comando)

        com_efeito = (Atribuicao, Chamada, IncrementoDecremento, Condicional, Sequencia)
        eh_void = isinstance(comando, Conversao) and comando.tipo == "void"

        if not isinstance(comando, com_efeito) and not eh_void:
            self.avisar("Expressão sem efeito: o resultado não é usado", comando)

    # ------------------------------------------------------------------
    # Auxiliares: constantes e compatibilidade de tipos
    # ------------------------------------------------------------------

    def valor_constante(self, no):
        """Valor inteiro de uma expressão constante (ou None)."""
        if isinstance(no, Numero):
            digitos = no.valor.rstrip("uUlL")
            if digitos[:2].lower() == "0x":
                return int(digitos, 16)
            if len(digitos) > 1 and digitos.startswith("0"):
                try:
                    return int(digitos, 8)      # 017 é octal em C
                except ValueError:
                    return None
            return int(digitos)

        if isinstance(no, Caractere):
            if no.valor.startswith("\\"):
                return ord(ESCAPES[no.valor[1]])
            return ord(no.valor)

        if isinstance(no, OperacaoUnaria) and no.operador in {"-", "+"}:
            valor = self.valor_constante(no.operando)
            if valor is None:
                return None
            return -valor if no.operador == "-" else valor

        if isinstance(no, OperacaoBinaria) and no.operador in {"+", "-", "*", "/", "%"}:
            a = self.valor_constante(no.esquerda)
            b = self.valor_constante(no.direita)
            if a is None or b is None:
                return None
            if no.operador == "+":
                return a + b
            if no.operador == "-":
                return a - b
            if no.operador == "*":
                return a * b
            if b == 0:
                return None
            quociente = abs(a) // abs(b) * (1 if (a >= 0) == (b >= 0) else -1)
            return quociente if no.operador == "/" else a - b * quociente

        return None

    def eh_zero_constante(self, no):
        if no is None:
            return False
        if isinstance(no, NumeroReal):
            return float(no.valor.rstrip("fFlL")) == 0
        return self.valor_constante(no) == 0

    def verificar_compatibilidade(self, destino, origem, no, contexto, expressao=None):
        """Verifica se um valor do tipo 'origem' pode ser guardado em 'destino'."""
        if origem is None or destino is None:
            return  # o erro da expressão já foi reportado

        if origem == "void":
            self.errar(
                f"Uma expressão void não tem valor para atribuir a {contexto}",
                no
            )
            return

        if destino == origem:
            return

        if eh_aritmetico(destino) and eh_aritmetico(origem):
            if eh_flutuante(origem) and eh_inteiro(destino):
                self.avisar(
                    f"Conversão implícita de {origem} para {destino} em "
                    f"{contexto} pode perder precisão",
                    no
                )
            return

        if eh_ponteiro(destino) and eh_ponteiro(origem):
            if destino == origem or "void*" in (destino, origem):
                return

        elif (
            eh_ponteiro(destino)
            and eh_inteiro(origem)
            and self.eh_zero_constante(expressao)
        ):
            return  # p = 0 equivale a p = NULL

        descricao = f"texto ({origem})" if isinstance(expressao, Texto) else origem

        self.errar(
            f"Tipos incompatíveis: não é possível atribuir {descricao} "
            f"a {contexto} do tipo {destino}",
            no
        )

    def verificar_condicao(self, expressao, palavra):
        if isinstance(expressao, Atribuicao) and expressao.operador == "=":
            self.avisar(
                f"Atribuição usada como condição do '{palavra}'; "
                "você quis dizer '=='?",
                expressao
            )

        tipo = self.visitar(expressao)

        if tipo is not None and not eh_escalar(tipo):
            self.errar(
                f"A condição do '{palavra}' precisa ser um número ou ponteiro "
                f"(recebeu {tipo})",
                expressao
            )

    def sempre_retorna(self, comando):
        """Aproximação: o comando sempre termina com 'return' (ou nunca termina)?"""
        if isinstance(comando, Retorno):
            return True
        if isinstance(comando, Bloco):
            return any(self.sempre_retorna(c) for c in comando.comandos)
        if isinstance(comando, Se):
            return (
                comando.senao is not None
                and self.sempre_retorna(comando.entao)
                and self.sempre_retorna(comando.senao)
            )
        if isinstance(comando, FacaEnquanto):
            return self.sempre_retorna(comando.corpo)
        if isinstance(comando, Enquanto):
            valor = self.valor_constante(comando.condicao)
            return valor is not None and valor != 0
        if isinstance(comando, Para):
            return comando.condicao is None
        if isinstance(comando, Chamada):
            return comando.nome == "exit"
        return False

    def verificar_funcoes_do_programa(self):
        principal = self.funcoes.get("main")

        if principal is None or principal.embutida:
            self.diagnosticos.append(Diagnostico(
                AVISO, "O programa não define a função 'main'", 1, 1
            ))

        for info in self.funcoes.values():
            if not info.embutida and info.utilizada and not info.definida:
                self.diagnosticos.append(Diagnostico(
                    ERRO,
                    f"A função '{info.nome}' foi declarada mas nunca foi definida",
                    info.linha,
                    info.no.coluna if info.no else None
                ))

    # ------------------------------------------------------------------
    # Funções
    # ------------------------------------------------------------------

    def visitar_Funcao(self, no):
        info = self.funcoes[no.nome]
        tipos = [p.tipo_efetivo for p in no.parametros]

        if info.no is not no and (
            info.tipo_retorno != no.tipo_retorno
            or info.parametros != tipos
            or info.variadica != no.variadica
        ):
            self.errar(
                f"A declaração de '{no.nome}' não confere com a da linha {info.linha}",
                no
            )

        for parametro in no.parametros:
            if parametro.tipo_efetivo == "void":
                self.errar("Um parâmetro não pode ser do tipo void", parametro)

        info.declarada = True

        if no.corpo is None:
            return

        self.verificar_tipo_existe(no.tipo_retorno, no)
        for parametro in no.parametros:
            self.verificar_tipo_existe(parametro.tipo_efetivo, parametro)

        if info.definida and info.linha_definicao is not None:
            self.errar(
                f"A função '{no.nome}' já foi definida na linha {info.linha_definicao}",
                no
            )

        info.definida = True
        info.linha_definicao = no.linha

        self.funcao_atual = no
        self.abrir_escopo()

        for parametro in no.parametros:
            if parametro.nome is None:
                continue
            self.declarar_variavel(
                Variavel(
                    parametro.nome,
                    parametro.tipo_efetivo,
                    parametro.linha,
                    parametro.coluna,
                    inicializada=True,
                    eh_parametro=True
                ),
                parametro
            )

        # O corpo compartilha o escopo dos parâmetros, como em C.
        self.visitar_lista(no.corpo.comandos)
        self.fechar_escopo()

        if (
            no.tipo_retorno != "void"
            and no.nome != "main"
            and not self.sempre_retorna(no.corpo)
        ):
            self.avisar(
                f"A função '{no.nome}' pode terminar sem retornar um valor",
                no
            )

        self.funcao_atual = None

    # ------------------------------------------------------------------
    # Comandos
    # ------------------------------------------------------------------

    @staticmethod
    def eh_struct(tipo):
        return tipo is not None and tipo.startswith("struct ") and not tipo.endswith("*")

    def verificar_tipo_existe(self, tipo, no):
        """Uma struct só pode ser usada por valor depois de definida."""
        if self.eh_struct(tipo) and tipo[len("struct "):] not in self.structs:
            self.errar(f"A struct '{tipo[len('struct '):]}' não foi definida", no)
            return False
        return True

    def tamanhos_das_dimensoes(self, no, descricao):
        """Avalia as expressões de tamanho de um array e devolve os valores."""
        tamanhos = []

        for i, expressao in enumerate(no.dimensoes):
            if expressao is None:
                if i > 0:
                    self.errar(
                        f"Só a primeira dimensão de {descricao} pode ficar sem tamanho",
                        no
                    )
                tamanhos.append(None)
                continue

            tipo = self.visitar(expressao)
            if tipo is not None and not eh_inteiro(tipo):
                self.errar("O tamanho do array precisa ser um número inteiro", expressao)

            valor = self.valor_constante(expressao)
            if valor is not None and valor <= 0:
                self.errar("O tamanho do array deve ser maior que zero", expressao)
                valor = None
            tamanhos.append(valor)

        return tamanhos

    def visitar_DefinicaoStruct(self, no):
        existente = self.structs.get(no.nome)

        if existente is not None:
            self.errar(
                f"A struct '{no.nome}' já foi definida na linha {existente['linha']}",
                no
            )
            return

        campos = {}

        for campo in no.campos:
            if campo.nome in campos:
                self.errar(f"Campo '{campo.nome}' repetido na struct '{no.nome}'", campo)
                continue

            if campo.tipo == f"struct {no.nome}":
                self.errar(
                    f"A struct '{no.nome}' não pode conter a si mesma; use um ponteiro",
                    campo
                )
            elif campo.tipo == "void":
                self.errar(f"O campo '{campo.nome}' não pode ser do tipo void", campo)
            else:
                self.verificar_tipo_existe(campo.tipo, campo)

            dimensoes = self.tamanhos_das_dimensoes(campo, f"o campo '{campo.nome}'")
            campos[campo.nome] = (campo.tipo, dimensoes)

        self.structs[no.nome] = {"campos": campos, "linha": no.linha}

    def visitar_Declaracao(self, no):
        eh_global = len(self.escopos) == 1 and not self.modo_simplificado

        if no.tipo == "void":
            self.errar(f"A variável '{no.nome}' não pode ser do tipo void", no)
        else:
            self.verificar_tipo_existe(no.tipo, no)

        dimensoes = self.tamanhos_das_dimensoes(no, f"o array '{no.nome}'")

        if no.eh_array and no.dimensoes[0] is None and no.inicializador is None:
            self.errar(
                f"O array '{no.nome}' precisa de um tamanho ou de valores iniciais",
                no
            )

        # O inicializador é analisado antes de a variável existir:
        # em "int a = a + 1;" o 'a' da direita ainda não foi declarado.
        if no.inicializador is not None:
            descricao = f"array '{no.nome}'" if no.eh_array else f"variável '{no.nome}'"
            quantidade = self.verificar_valor_inicial(
                no.tipo, dimensoes, no.inicializador, descricao, no
            )
            if dimensoes and dimensoes[0] is None:
                dimensoes[0] = quantidade

        # Arrays e structs são preenchidos por partes; não geram aviso de
        # "usada antes de receber um valor".
        self.declarar_variavel(
            Variavel(
                no.nome,
                no.tipo,
                no.linha,
                no.coluna,
                inicializada=(
                    no.inicializador is not None
                    or no.eh_array
                    or eh_global
                    or self.eh_struct(no.tipo)
                ),
                dimensoes=dimensoes
            ),
            no
        )

    def verificar_valor_inicial(self, tipo, dimensoes, inicial, descricao, ancora):
        """
        Confere um valor inicial contra o tipo (e as dimensões, se for array).
        Devolve quantos elementos a primeira dimensão recebeu (ou None).
        """
        if dimensoes:
            if isinstance(inicial, ListaInicializadora):
                for i, elemento in enumerate(inicial.elementos, start=1):
                    # Sem chaves internas ("int m[2][2] = {1, 2, 3, 4}"),
                    # cada valor é conferido contra o tipo base.
                    resto = dimensoes[1:]
                    if resto and not isinstance(elemento, (ListaInicializadora, Texto)):
                        resto = []
                    self.verificar_valor_inicial(
                        tipo, resto, elemento, f"elemento {i} do {descricao}", elemento
                    )

                quantidade = len(inicial.elementos)
                limite = dimensoes[0]
                if limite is not None and quantidade > limite and len(dimensoes) == 1:
                    self.avisar(
                        f"Excesso de valores na inicialização do {descricao} "
                        f"(tamanho {limite}, recebeu {quantidade})",
                        inicial
                    )
                return quantidade

            if isinstance(inicial, Texto) and tipo == "char" and len(dimensoes) == 1:
                comprimento = len(re.sub(r"\\.", "x", inicial.valor))
                limite = dimensoes[0]
                if limite is not None and comprimento > limite:
                    self.avisar(
                        f"O texto tem {comprimento} caracteres e não cabe no "
                        f"{descricao} (tamanho {limite})",
                        inicial
                    )
                return comprimento + 1

            self.visitar(inicial)
            self.errar(
                f"O {descricao} deve ser inicializado com {{ valores }}",
                inicial
            )
            return None

        if isinstance(inicial, ListaInicializadora):
            if self.eh_struct(tipo) and tipo[len("struct "):] in self.structs:
                campos = list(self.structs[tipo[len("struct "):]]["campos"].items())

                for elemento, (nome_campo, (tipo_campo, dims_campo)) in zip(
                    inicial.elementos, campos
                ):
                    self.verificar_valor_inicial(
                        tipo_campo, dims_campo, elemento,
                        f"campo '{nome_campo}' de {descricao}", elemento
                    )

                for elemento in inicial.elementos[len(campos):]:
                    self.visitar(elemento)
                if len(inicial.elementos) > len(campos):
                    self.avisar(
                        f"Excesso de valores na inicialização de {descricao} "
                        f"(a struct tem {len(campos)} campos)",
                        inicial
                    )
                return None

            if len(inicial.elementos) == 1 and not self.eh_struct(tipo):
                elemento = inicial.elementos[0]
                return self.verificar_valor_inicial(tipo, [], elemento, descricao, elemento)

            for elemento in inicial.elementos:
                if not isinstance(elemento, ListaInicializadora):
                    self.visitar(elemento)
            if not self.eh_struct(tipo):
                self.errar(
                    "Uma lista { ... } só pode inicializar arrays e structs",
                    inicial
                )
            return None

        tipo_valor = self.visitar(inicial)
        self.verificar_compatibilidade(tipo, tipo_valor, ancora, descricao, inicial)
        return None

    def visitar_ListaInicializadora(self, no):
        self.errar("Lista { ... } usada fora de uma declaração", no)
        return None

    def visitar_Bloco(self, no):
        self.abrir_escopo()
        self.visitar_lista(no.comandos)
        self.fechar_escopo()

    def visitar_Se(self, no):
        self.verificar_condicao(no.condicao, "if")
        self.visitar_comando(no.entao)
        if no.senao is not None:
            self.visitar_comando(no.senao)

    def visitar_Enquanto(self, no):
        self.verificar_condicao(no.condicao, "while")
        self.profundidade_laco += 1
        self.visitar_comando(no.corpo)
        self.profundidade_laco -= 1

    def visitar_FacaEnquanto(self, no):
        self.profundidade_laco += 1
        self.visitar_comando(no.corpo)
        self.profundidade_laco -= 1
        self.verificar_condicao(no.condicao, "while")

    def visitar_Para(self, no):
        self.abrir_escopo()

        for comando in no.inicio:
            self.visitar(comando)

        if no.condicao is not None:
            self.verificar_condicao(no.condicao, "for")

        self.profundidade_laco += 1
        self.visitar_comando(no.corpo)
        self.profundidade_laco -= 1

        if no.incremento is not None:
            self.visitar(no.incremento)

        self.fechar_escopo()

    def visitar_Escolha(self, no):
        tipo = self.visitar(no.expressao)

        if tipo is not None and not eh_inteiro(tipo):
            self.errar(
                f"O 'switch' exige uma expressão inteira (recebeu {tipo})",
                no.expressao
            )

        vistos = {}
        linha_default = None

        self.abrir_escopo()
        self.profundidade_escolha += 1

        for caso in no.casos:
            if caso.valor is None:
                if linha_default is not None:
                    self.errar(
                        f"Mais de um 'default' no switch (o primeiro está na linha {linha_default})",
                        caso
                    )
                linha_default = caso.linha
            else:
                valor = self.valor_constante(caso.valor)
                if valor is None:
                    self.visitar(caso.valor)
                    self.errar("O valor do 'case' precisa ser uma constante inteira", caso)
                elif valor in vistos:
                    self.errar(
                        f"Valor {valor} repetido no switch (já usado na linha {vistos[valor]})",
                        caso
                    )
                else:
                    vistos[valor] = caso.linha

            self.visitar_lista(caso.comandos)

        self.profundidade_escolha -= 1
        self.fechar_escopo()

    def visitar_Pare(self, no):
        if self.profundidade_laco == 0 and self.profundidade_escolha == 0:
            self.errar("'break' fora de um laço ou switch", no)

    def visitar_Continue(self, no):
        if self.profundidade_laco == 0:
            self.errar("'continue' fora de um laço", no)

    def visitar_ComandoVazio(self, no):
        pass

    def visitar_Retorno(self, no):
        if self.funcao_atual is not None:
            esperado = self.funcao_atual.tipo_retorno
            nome = self.funcao_atual.nome
        else:
            esperado = TIPO_RETORNO
            nome = "main"

        if no.valor is None:
            if esperado != "void":
                self.avisar(
                    f"'return' sem valor em uma função que retorna {esperado}",
                    no
                )
            return

        tipo = self.visitar(no.valor)

        if esperado == "void":
            self.errar(f"A função void '{nome}' não pode retornar um valor", no)
            return

        self.verificar_compatibilidade(
            esperado, tipo, no, "valor de retorno", no.valor
        )

    # ------------------------------------------------------------------
    # Expressões (devolvem o tipo resultante, ou None se houve erro)
    # ------------------------------------------------------------------

    def visitar_Numero(self, no):
        return "int"

    def visitar_NumeroReal(self, no):
        return no.tipo

    def visitar_Caractere(self, no):
        return "char"

    def visitar_Texto(self, no):
        return "char*"

    def reportar_nome_desconhecido(self, nome, no):
        if nome in self.funcoes:
            self.errar(
                f"'{nome}' é uma função; para chamá-la use {nome}(...)",
                no
            )
        else:
            self.errar(f"Variável '{nome}' não foi declarada", no)

    def visitar_Identificador(self, no):
        variavel = self.buscar_variavel(no.nome)

        if variavel is None:
            self.reportar_nome_desconhecido(no.nome, no)
            return None

        variavel.utilizada = True

        if not variavel.inicializada and not variavel.aviso_nao_inicializada:
            variavel.aviso_nao_inicializada = True
            self.avisar(
                f"Variável '{no.nome}' utilizada antes de receber um valor",
                no
            )

        return variavel.tipo_valor

    def visitar_lvalue(self, no, leitura):
        """Analisa o lado esquerdo de uma atribuição (ou operando de ++/--)."""
        if isinstance(no, Identificador):
            variavel = self.buscar_variavel(no.nome)

            if variavel is None:
                self.reportar_nome_desconhecido(no.nome, no)
                return None

            if variavel.eh_array:
                self.errar(
                    f"Não é possível atribuir a um array inteiro ('{no.nome}'); "
                    "atribua a cada elemento",
                    no
                )
                return None

            if variavel.embutida:
                self.errar(f"'{no.nome}' é uma constante e não pode receber valor", no)
                return None

            if leitura:
                return self.visitar_Identificador(no)

            return variavel.tipo

        if isinstance(no, (Indexacao, Acesso)) or (
            isinstance(no, OperacaoUnaria) and no.operador == "*"
        ):
            return self.visitar(no)

        self.visitar(no)
        self.errar(
            "O lado esquerdo precisa ser uma variável, um elemento de array "
            "ou *ponteiro",
            no
        )
        return None

    def marcar_inicializada(self, alvo):
        if isinstance(alvo, Identificador):
            variavel = self.buscar_variavel(alvo.nome)
            if variavel is not None:
                variavel.inicializada = True

    @staticmethod
    def descrever_alvo(alvo):
        if isinstance(alvo, Identificador):
            return f"variável '{alvo.nome}'"
        if isinstance(alvo, Indexacao):
            return "elemento do array"
        if isinstance(alvo, Acesso):
            return f"campo '{alvo.campo}'"
        return "valor apontado"

    def visitar_Atribuicao(self, no):
        tipo_valor = self.visitar(no.valor)
        composta = no.operador != "="
        tipo_alvo = self.visitar_lvalue(no.alvo, leitura=composta)

        if tipo_alvo is not None:
            if composta:
                self.tipo_binario(
                    no.operador[:-1], tipo_alvo, tipo_valor, no, no.alvo, no.valor
                )
            else:
                self.verificar_compatibilidade(
                    tipo_alvo, tipo_valor, no, self.descrever_alvo(no.alvo), no.valor
                )

        self.marcar_inicializada(no.alvo)

        return tipo_alvo

    def visitar_IncrementoDecremento(self, no):
        tipo = self.visitar_lvalue(no.operando, leitura=True)

        if tipo is not None and not (eh_aritmetico(tipo) or eh_ponteiro(tipo)):
            self.errar(f"Operador '{no.operador}' não pode ser aplicado a {tipo}", no)
            tipo = None

        self.marcar_inicializada(no.operando)

        return tipo

    def visitar_OperacaoUnaria(self, no):
        operador = no.operador

        if operador == "&":
            return self.endereco_de(no)

        tipo = self.visitar(no.operando)

        if tipo is None:
            return None

        if tipo == "void":
            self.errar(f"Operador '{operador}' não pode ser aplicado a um valor void", no)
            return None

        if operador == "*":
            if not eh_ponteiro(tipo):
                self.errar(f"O operador '*' exige um ponteiro (recebeu {tipo})", no)
                return None
            if tipo == "void*":
                self.errar("Não é possível acessar o valor apontado por um void*", no)
                return None
            return apontado(tipo)

        if operador in {"-", "+"}:
            if not eh_aritmetico(tipo):
                self.errar(f"Operador unário '{operador}' não pode ser aplicado a {tipo}", no)
                return None
            return tipo if eh_flutuante(tipo) else "int"

        if operador == "!":
            if not eh_escalar(tipo):
                self.errar(f"Operador '!' não pode ser aplicado a {tipo}", no)
                return None
            return "int"

        if operador == "~":
            if not eh_inteiro(tipo):
                self.errar(f"Operador '~' exige um inteiro (recebeu {tipo})", no)
                return None
            return "int"

        return None

    def endereco_de(self, no):
        alvo = no.operando

        if isinstance(alvo, Identificador):
            variavel = self.buscar_variavel(alvo.nome)

            if variavel is None:
                self.reportar_nome_desconhecido(alvo.nome, alvo)
                return None

            # Quem recebe o endereço (ex.: scanf) pode preencher a variável.
            variavel.utilizada = True
            variavel.inicializada = True
            return variavel.tipo + "*"

        if isinstance(alvo, (Indexacao, Acesso)) or (
            isinstance(alvo, OperacaoUnaria) and alvo.operador == "*"
        ):
            tipo = self.visitar(alvo)
            return tipo + "*" if tipo is not None else None

        self.visitar(alvo)
        self.errar("O operador '&' exige uma variável ou elemento de array", no)
        return None

    def visitar_OperacaoBinaria(self, no):
        tipo_esq = self.visitar(no.esquerda)
        tipo_dir = self.visitar(no.direita)
        return self.tipo_binario(
            no.operador, tipo_esq, tipo_dir, no, no.esquerda, no.direita
        )

    def tipo_binario(self, operador, tipo_esq, tipo_dir, no, esquerda, direita):
        if tipo_esq is None or tipo_dir is None:
            return None

        if "void" in (tipo_esq, tipo_dir):
            self.errar(f"Operador '{operador}' não pode ser aplicado a um valor void", no)
            return None

        if operador in {"*", "/"}:
            if not (eh_aritmetico(tipo_esq) and eh_aritmetico(tipo_dir)):
                self.errar(
                    f"Operador '{operador}' exige operandos numéricos "
                    f"(recebeu {tipo_esq} e {tipo_dir})",
                    no
                )
                return None
            if operador == "/" and self.eh_zero_constante(direita):
                self.avisar("Divisão por zero", no)
            return promover(tipo_esq, tipo_dir)

        if operador == "%":
            if not (eh_inteiro(tipo_esq) and eh_inteiro(tipo_dir)):
                self.errar(
                    f"Operador '%' exige operandos inteiros "
                    f"(recebeu {tipo_esq} e {tipo_dir})",
                    no
                )
                return None
            if self.eh_zero_constante(direita):
                self.avisar("Divisão por zero", no)
            return "int"

        if operador in {"+", "-"}:
            if eh_aritmetico(tipo_esq) and eh_aritmetico(tipo_dir):
                return promover(tipo_esq, tipo_dir)
            if eh_ponteiro(tipo_esq) and eh_inteiro(tipo_dir):
                return tipo_esq
            if operador == "+" and eh_inteiro(tipo_esq) and eh_ponteiro(tipo_dir):
                return tipo_dir
            if operador == "-" and eh_ponteiro(tipo_esq) and tipo_esq == tipo_dir:
                return "int"
            self.errar(
                f"Operador '{operador}' não pode ser aplicado a {tipo_esq} e {tipo_dir}",
                no
            )
            return None

        if operador in {"<", ">", "<=", ">=", "==", "!="}:
            if eh_aritmetico(tipo_esq) and eh_aritmetico(tipo_dir):
                return "int"
            if eh_ponteiro(tipo_esq) and eh_ponteiro(tipo_dir):
                return "int"
            if (eh_ponteiro(tipo_esq) and self.eh_zero_constante(direita)) or (
                eh_ponteiro(tipo_dir) and self.eh_zero_constante(esquerda)
            ):
                return "int"
            self.errar(
                f"Não é possível comparar {tipo_esq} com {tipo_dir}",
                no
            )
            return None

        if operador in {"&", "|", "^", "<<", ">>"}:
            if not (eh_inteiro(tipo_esq) and eh_inteiro(tipo_dir)):
                self.errar(
                    f"Operador '{operador}' exige operandos inteiros "
                    f"(recebeu {tipo_esq} e {tipo_dir})",
                    no
                )
                return None
            return "int"

        if operador in {"&&", "||"}:
            if not (eh_escalar(tipo_esq) and eh_escalar(tipo_dir)):
                self.errar(
                    f"Operador '{operador}' exige números ou ponteiros "
                    f"(recebeu {tipo_esq} e {tipo_dir})",
                    no
                )
                return None
            return "int"

        self.errar(f"Operador '{operador}' não suportado", no)
        return None

    def visitar_Condicional(self, no):
        self.verificar_condicao(no.condicao, "?:")
        tipo_a = self.visitar(no.se_verdadeiro)
        tipo_b = self.visitar(no.se_falso)

        if tipo_a is None or tipo_b is None:
            return None
        if eh_aritmetico(tipo_a) and eh_aritmetico(tipo_b):
            return promover(tipo_a, tipo_b)
        if tipo_a == tipo_b:
            return tipo_a
        if eh_ponteiro(tipo_a) and (tipo_b == "void*" or self.eh_zero_constante(no.se_falso)):
            return tipo_a
        if eh_ponteiro(tipo_b) and (tipo_a == "void*" or self.eh_zero_constante(no.se_verdadeiro)):
            return tipo_b

        self.errar(
            f"Os dois lados de '?:' têm tipos incompatíveis ({tipo_a} e {tipo_b})",
            no
        )
        return None

    def visitar_Chamada(self, no):
        tipos = [self.visitar(argumento) for argumento in no.argumentos]
        info = self.funcoes.get(no.nome)

        if info is None:
            if self.buscar_variavel(no.nome) is not None:
                self.errar(f"'{no.nome}' é uma variável, não uma função", no)
            elif self.inclusoes:
                # Provavelmente vem de uma biblioteca que este compilador não conhece.
                if no.nome not in self.funcoes_desconhecidas:
                    self.funcoes_desconhecidas.add(no.nome)
                    self.avisar(
                        f"Função '{no.nome}' não é conhecida por este compilador; "
                        "supondo que venha de uma biblioteca incluída",
                        no
                    )
            else:
                self.errar(f"Função '{no.nome}' não foi declarada", no)
            return None

        info.utilizada = True

        if not info.declarada and not info.avisou_antes_de_declarar:
            info.avisou_antes_de_declarar = True
            self.avisar(
                f"Função '{no.nome}' usada antes de ser declarada; "
                "declare um protótipo antes de usá-la",
                no
            )

        esperados = len(info.parametros)
        recebidos = len(no.argumentos)

        if recebidos < esperados or (recebidos > esperados and not info.variadica):
            minimo = "pelo menos " if info.variadica else ""
            self.errar(
                f"A função '{no.nome}' espera {minimo}"
                f"{plural(esperados, 'argumento', 'argumentos')}, mas recebeu {recebidos}",
                no
            )

        for i, (esperado, tipo, argumento) in enumerate(
            zip(info.parametros, tipos, no.argumentos), start=1
        ):
            self.verificar_compatibilidade(
                esperado, tipo, argumento,
                f"argumento {i} de '{no.nome}'", argumento
            )

        for tipo, argumento in zip(tipos[esperados:], no.argumentos[esperados:]):
            if tipo == "void":
                self.errar("Uma expressão void não pode ser passada como argumento", argumento)

        if no.nome in {"printf", "scanf"} and no.argumentos:
            self.verificar_formato(no, tipos)

        return info.tipo_retorno

    def verificar_formato(self, no, tipos):
        """Confere a quantidade de valores do printf/scanf e o '&' do scanf."""
        formato = no.argumentos[0]

        if not isinstance(formato, Texto):
            return

        especificadores = [
            m for m in FORMATO.finditer(formato.valor) if m.group(0) != "%%"
        ]
        # %*d e %.*f pedem um valor extra para a largura/precisão.
        pedidos = sum(
            1 + (m.group(1) == "*") + (m.group(2) == "*") for m in especificadores
        )
        passados = len(no.argumentos) - 1

        if pedidos != passados:
            self.avisar(
                f"O formato de '{no.nome}' pede "
                f"{plural(pedidos, 'valor', 'valores')}, mas "
                f"{plural(passados, 'foi passado', 'foram passados')}",
                no
            )

        if no.nome == "scanf":
            for i, (tipo, argumento) in enumerate(
                zip(tipos[1:], no.argumentos[1:]), start=2
            ):
                if tipo is not None and not eh_ponteiro(tipo):
                    self.avisar(
                        f"O argumento {i} do scanf deveria ser um endereço; "
                        "faltou o '&'?",
                        argumento
                    )

    def visitar_Indexacao(self, no):
        tipo_base = self.visitar(no.base)
        tipo_indice = self.visitar(no.indice)

        if tipo_base is None:
            return None

        if not eh_ponteiro(tipo_base):
            self.errar(
                f"Somente arrays e ponteiros podem usar [] (recebeu {tipo_base})",
                no
            )
            return None

        if tipo_indice is not None and not eh_inteiro(tipo_indice):
            self.errar(
                f"O índice do array precisa ser inteiro (recebeu {tipo_indice})",
                no.indice
            )

        if isinstance(no.base, Identificador):
            variavel = self.buscar_variavel(no.base.nome)
            indice = self.valor_constante(no.indice)
            if (
                variavel is not None
                and variavel.eh_array
                and variavel.tamanho is not None
                and indice is not None
                and not 0 <= indice < variavel.tamanho
            ):
                self.avisar(
                    f"Índice {indice} fora dos limites do array '{variavel.nome}' "
                    f"(posições válidas: 0 a {variavel.tamanho - 1})",
                    no.indice
                )

        if tipo_base == "void*":
            self.errar("Não é possível indexar um void*", no)
            return None

        return apontado(tipo_base)

    def visitar_Acesso(self, no):
        tipo_base = self.visitar(no.base)

        if tipo_base is None:
            return None

        if no.seta:
            if not (eh_ponteiro(tipo_base) and self.eh_struct(apontado(tipo_base))):
                self.errar(
                    f"O operador '->' exige um ponteiro para struct (recebeu {tipo_base})",
                    no
                )
                return None
            tipo_struct = apontado(tipo_base)
        else:
            if not self.eh_struct(tipo_base):
                dica = (
                    "; para ponteiros use '->'"
                    if eh_ponteiro(tipo_base) and self.eh_struct(apontado(tipo_base))
                    else ""
                )
                self.errar(
                    f"O operador '.' exige uma struct (recebeu {tipo_base}){dica}",
                    no
                )
                return None
            tipo_struct = tipo_base

        nome_struct = tipo_struct[len("struct "):]
        definicao = self.structs.get(nome_struct)

        if definicao is None:
            self.errar(f"A struct '{nome_struct}' não foi definida", no)
            return None

        campo = definicao["campos"].get(no.campo)

        if campo is None:
            self.errar(f"A struct '{nome_struct}' não tem o campo '{no.campo}'", no)
            return None

        tipo_campo, dimensoes = campo
        return tipo_campo + "*" * len(dimensoes)

    def visitar_Sequencia(self, no):
        tipo = None
        for expressao in no.expressoes:
            tipo = self.visitar(expressao)
        return tipo

    def visitar_Conversao(self, no):
        tipo = self.visitar(no.expressao)
        destino = no.tipo

        if tipo is None or destino == "void":
            return destino

        valida = (
            (eh_aritmetico(tipo) and eh_aritmetico(destino))
            or (eh_ponteiro(tipo) and eh_ponteiro(destino))
            or (eh_ponteiro(tipo) and eh_inteiro(destino))
            or (eh_inteiro(tipo) and eh_ponteiro(destino))
        )

        if not valida:
            self.errar(f"Conversão de {tipo} para {destino} não é permitida", no)

        return destino

    def visitar_Tamanho(self, no):
        if no.expressao is not None:
            self.visitar(no.expressao)
        return "int"
