"""
Nós da árvore sintática abstrata (AST).

Todo nó guarda 'linha' e 'coluna' (para mensagens de erro) e tem
formatar(nivel), que devolve a sua representação em texto indentado.
"""


def _recuo(nivel):
    return "  " * nivel


def _filhos(nivel, rotulo, nos):
    """Formata uma lista de nós sob um rótulo (ex.: 'Corpo')."""
    linhas = [f"{_recuo(nivel)}{rotulo}"]
    for no in nos:
        linhas.append(no.formatar(nivel + 1))
    return "\n".join(linhas)


# ----------------------------------------------------------------------
# Estrutura do programa
# ----------------------------------------------------------------------

class Programa:
    def __init__(self):
        self.comandos = []

    def adicionar(self, comando):
        self.comandos.append(comando)

    def formatar(self):
        linhas = ["Programa"]

        for comando in self.comandos:
            linhas.append(comando.formatar(1))

        return "\n".join(linhas)


class Parametro:
    def __init__(self, tipo, nome, linha, coluna=None, eh_array=False, dimensoes=None):
        self.tipo = tipo
        self.nome = nome
        self.linha = linha
        self.coluna = coluna
        self.dimensoes = dimensoes if dimensoes is not None else (1 if eh_array else 0)

    @property
    def eh_array(self):
        return self.dimensoes > 0

    @property
    def tipo_efetivo(self):
        # Um parâmetro "int v[]" é, na prática, um "int*" (e "int m[][3]", um "int**").
        return self.tipo + "*" * self.dimensoes

    def formatar(self, nivel=0):
        nome = self.nome or "(sem nome)"
        return f"{_recuo(nivel)}Parametro (tipo={self.tipo_efetivo}, nome={nome})"


class Funcao:
    def __init__(self, tipo_retorno, nome, parametros, corpo, linha, coluna=None,
                 variadica=False):
        self.tipo_retorno = tipo_retorno
        self.nome = nome
        self.parametros = parametros
        self.corpo = corpo          # None = apenas protótipo
        self.linha = linha
        self.coluna = coluna
        self.variadica = variadica

    def formatar(self, nivel=0):
        especie = "Funcao" if self.corpo is not None else "Prototipo"
        linhas = [f"{_recuo(nivel)}{especie} (retorno={self.tipo_retorno}, nome={self.nome})"]

        if self.parametros:
            linhas.append(_filhos(nivel + 1, "Parametros", self.parametros))

        if self.corpo is not None:
            linhas.append(self.corpo.formatar(nivel + 1))

        return "\n".join(linhas)


# ----------------------------------------------------------------------
# Comandos
# ----------------------------------------------------------------------

class Declaracao:
    def __init__(self, tipo, nome, inicializador, linha, coluna=None,
                 tamanho=None, eh_array=False, dimensoes=None):
        self.tipo = tipo
        self.nome = nome
        self.inicializador = inicializador
        self.linha = linha
        self.coluna = coluna
        # Expressão do tamanho de cada dimensão: "int m[2][3]" -> [2, 3].
        # Um tamanho omitido ("int v[] = {...}") fica como None.
        if dimensoes is None:
            dimensoes = [tamanho] if eh_array else []
        self.dimensoes = dimensoes

    @property
    def eh_array(self):
        return bool(self.dimensoes)

    @property
    def tamanho(self):
        return self.dimensoes[0] if self.dimensoes else None

    def formatar(self, nivel=0):
        tipo = self.tipo + "[]" * len(self.dimensoes)
        texto = f"{_recuo(nivel)}Declaracao (tipo={tipo}, nome={self.nome})"

        tamanhos = [d for d in self.dimensoes if d is not None]
        if tamanhos:
            texto += "\n" + _filhos(nivel + 1, "Tamanho", tamanhos)

        if self.inicializador is not None:
            texto += "\n" + self.inicializador.formatar(nivel + 1)

        return texto


class DefinicaoStruct:
    def __init__(self, nome, campos, linha, coluna=None):
        self.nome = nome
        self.campos = campos        # lista de Declaracao (sem valor inicial)
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return _filhos(nivel, f"Struct ({self.nome})", self.campos)


class ListaInicializadora:
    def __init__(self, elementos, linha, coluna=None):
        self.elementos = elementos
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return _filhos(nivel, "ListaInicializadora", self.elementos)


class Bloco:
    def __init__(self, comandos, linha, coluna=None):
        self.comandos = comandos
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return _filhos(nivel, "Bloco", self.comandos)


class Se:
    def __init__(self, condicao, entao, senao, linha, coluna=None):
        self.condicao = condicao
        self.entao = entao
        self.senao = senao
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        linhas = [
            f"{_recuo(nivel)}Se",
            _filhos(nivel + 1, "Condicao", [self.condicao]),
            _filhos(nivel + 1, "Entao", [self.entao]),
        ]
        if self.senao is not None:
            linhas.append(_filhos(nivel + 1, "Senao", [self.senao]))
        return "\n".join(linhas)


class Enquanto:
    def __init__(self, condicao, corpo, linha, coluna=None):
        self.condicao = condicao
        self.corpo = corpo
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return "\n".join([
            f"{_recuo(nivel)}Enquanto",
            _filhos(nivel + 1, "Condicao", [self.condicao]),
            self.corpo.formatar(nivel + 1),
        ])


class FacaEnquanto:
    def __init__(self, corpo, condicao, linha, coluna=None):
        self.corpo = corpo
        self.condicao = condicao
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return "\n".join([
            f"{_recuo(nivel)}FacaEnquanto",
            self.corpo.formatar(nivel + 1),
            _filhos(nivel + 1, "Condicao", [self.condicao]),
        ])


class Para:
    def __init__(self, inicio, condicao, incremento, corpo, linha, coluna=None):
        self.inicio = inicio            # lista de comandos (pode ser vazia)
        self.condicao = condicao        # expressão ou None
        self.incremento = incremento    # expressão ou None
        self.corpo = corpo
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        linhas = [f"{_recuo(nivel)}Para"]
        if self.inicio:
            linhas.append(_filhos(nivel + 1, "Inicio", self.inicio))
        if self.condicao is not None:
            linhas.append(_filhos(nivel + 1, "Condicao", [self.condicao]))
        if self.incremento is not None:
            linhas.append(_filhos(nivel + 1, "Incremento", [self.incremento]))
        linhas.append(self.corpo.formatar(nivel + 1))
        return "\n".join(linhas)


class Caso:
    def __init__(self, valor, comandos, linha, coluna=None):
        self.valor = valor              # None = default
        self.comandos = comandos
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        if self.valor is None:
            linhas = [f"{_recuo(nivel)}Default"]
        else:
            linhas = [f"{_recuo(nivel)}Caso", self.valor.formatar(nivel + 1)]
        for comando in self.comandos:
            linhas.append(comando.formatar(nivel + 1))
        return "\n".join(linhas)


class Escolha:
    def __init__(self, expressao, casos, linha, coluna=None):
        self.expressao = expressao
        self.casos = casos
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        linhas = [f"{_recuo(nivel)}Escolha", self.expressao.formatar(nivel + 1)]
        for caso in self.casos:
            linhas.append(caso.formatar(nivel + 1))
        return "\n".join(linhas)


class Pare:
    def __init__(self, linha, coluna=None):
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return f"{_recuo(nivel)}Pare (break)"


class Continue:
    def __init__(self, linha, coluna=None):
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return f"{_recuo(nivel)}Continue"


class ComandoVazio:
    def __init__(self, linha, coluna=None):
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return f"{_recuo(nivel)}ComandoVazio"


class Retorno:
    def __init__(self, valor, linha, coluna=None):
        self.valor = valor              # None em "return;"
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        if self.valor is None:
            return f"{_recuo(nivel)}Retorno"

        return "\n".join([
            f"{_recuo(nivel)}Retorno",
            self.valor.formatar(nivel + 1)
        ])


# ----------------------------------------------------------------------
# Expressões
# ----------------------------------------------------------------------

class Numero:
    def __init__(self, valor, linha, coluna=None):
        self.valor = valor
        self.linha = linha
        self.coluna = coluna
        self.tipo = "int"

    def formatar(self, nivel=0):
        return f"{_recuo(nivel)}Numero ({self.valor})"


class NumeroReal:
    def __init__(self, valor, linha, coluna=None):
        self.valor = valor
        self.linha = linha
        self.coluna = coluna
        # Em C, 1.5 é double e 1.5f é float.
        self.tipo = "float" if valor.lower().endswith("f") else "double"

    def formatar(self, nivel=0):
        return f"{_recuo(nivel)}NumeroReal ({self.valor})"


class Caractere:
    def __init__(self, valor, linha, coluna=None):
        self.valor = valor
        self.linha = linha
        self.coluna = coluna
        self.tipo = "char"

    def formatar(self, nivel=0):
        return f"{_recuo(nivel)}Caractere ({self.valor})"


class Texto:
    def __init__(self, valor, linha, coluna=None):
        self.valor = valor
        self.linha = linha
        self.coluna = coluna
        self.tipo = "char*"

    def formatar(self, nivel=0):
        return f"{_recuo(nivel)}Texto ({self.valor})"


class Identificador:
    def __init__(self, nome, linha, coluna=None):
        self.nome = nome
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return f"{_recuo(nivel)}Identificador ({self.nome})"


class OperacaoUnaria:
    def __init__(self, operador, operando, linha, coluna=None):
        self.operador = operador
        self.operando = operando
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return "\n".join([
            f"{_recuo(nivel)}OperacaoUnaria ({self.operador})",
            self.operando.formatar(nivel + 1)
        ])


class IncrementoDecremento:
    def __init__(self, operador, operando, prefixo, linha, coluna=None):
        self.operador = operador        # "++" ou "--"
        self.operando = operando
        self.prefixo = prefixo
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        forma = "prefixo" if self.prefixo else "posfixo"
        return "\n".join([
            f"{_recuo(nivel)}IncrementoDecremento ({self.operador}, {forma})",
            self.operando.formatar(nivel + 1)
        ])


class OperacaoBinaria:
    def __init__(self, esquerda, operador, direita, linha, coluna=None):
        self.esquerda = esquerda
        self.operador = operador
        self.direita = direita
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return "\n".join([
            f"{_recuo(nivel)}OperacaoBinaria ({self.operador})",
            self.esquerda.formatar(nivel + 1),
            self.direita.formatar(nivel + 1)
        ])


class Atribuicao:
    def __init__(self, alvo, operador, valor, linha, coluna=None):
        self.alvo = alvo                # Identificador, Indexacao ou *ponteiro
        self.operador = operador        # "=", "+=", "-=", ...
        self.valor = valor
        self.linha = linha
        self.coluna = coluna

    @property
    def nome(self):
        return self.alvo.nome if isinstance(self.alvo, Identificador) else None

    def formatar(self, nivel=0):
        return "\n".join([
            f"{_recuo(nivel)}Atribuicao ({self.operador})",
            self.alvo.formatar(nivel + 1),
            self.valor.formatar(nivel + 1)
        ])


class Condicional:
    def __init__(self, condicao, se_verdadeiro, se_falso, linha, coluna=None):
        self.condicao = condicao
        self.se_verdadeiro = se_verdadeiro
        self.se_falso = se_falso
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return "\n".join([
            f"{_recuo(nivel)}Condicional (?:)",
            self.condicao.formatar(nivel + 1),
            self.se_verdadeiro.formatar(nivel + 1),
            self.se_falso.formatar(nivel + 1)
        ])


class Chamada:
    def __init__(self, nome, argumentos, linha, coluna=None):
        self.nome = nome
        self.argumentos = argumentos
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        linhas = [f"{_recuo(nivel)}Chamada ({self.nome})"]
        for argumento in self.argumentos:
            linhas.append(argumento.formatar(nivel + 1))
        return "\n".join(linhas)


class Indexacao:
    def __init__(self, base, indice, linha, coluna=None):
        self.base = base
        self.indice = indice
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return "\n".join([
            f"{_recuo(nivel)}Indexacao",
            self.base.formatar(nivel + 1),
            self.indice.formatar(nivel + 1)
        ])


class Acesso:
    def __init__(self, base, campo, seta, linha, coluna=None):
        self.base = base
        self.campo = campo
        self.seta = seta            # True para "p->campo", False para "s.campo"
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        operador = "->" if self.seta else "."
        return "\n".join([
            f"{_recuo(nivel)}Acesso ({operador}{self.campo})",
            self.base.formatar(nivel + 1)
        ])


class Sequencia:
    """Operador vírgula: em 'i++, j--' tudo é avaliado e vale o último."""

    def __init__(self, expressoes, linha, coluna=None):
        self.expressoes = expressoes
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return _filhos(nivel, "Sequencia (,)", self.expressoes)


class Conversao:
    def __init__(self, tipo, expressao, linha, coluna=None):
        self.tipo = tipo
        self.expressao = expressao
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        return "\n".join([
            f"{_recuo(nivel)}Conversao ({self.tipo})",
            self.expressao.formatar(nivel + 1)
        ])


class Tamanho:
    def __init__(self, tipo, expressao, linha, coluna=None):
        self.tipo = tipo                # sizeof(int)
        self.expressao = expressao      # sizeof x
        self.linha = linha
        self.coluna = coluna

    def formatar(self, nivel=0):
        if self.tipo is not None:
            return f"{_recuo(nivel)}Sizeof ({self.tipo})"
        return "\n".join([
            f"{_recuo(nivel)}Sizeof",
            self.expressao.formatar(nivel + 1)
        ])


EXPRESSOES = (
    Numero, NumeroReal, Caractere, Texto, Identificador, OperacaoUnaria,
    IncrementoDecremento, OperacaoBinaria, Atribuicao, Condicional, Chamada,
    Indexacao, Conversao, Tamanho, Acesso, Sequencia,
)
