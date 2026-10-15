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

class Declaracao:
    def __init__(self, tipo, nome, inicializador, linha):
        self.tipo = tipo
        self.nome = nome
        self.inicializador = inicializador
        self.linha = linha

    def formatar(self, nivel=0):
        espacos = "  " * nivel

        texto = (
            f"{espacos}Declaracao "
            f"(tipo={self.tipo}, nome={self.nome})"
        )

        if self.inicializador is not None:
            texto += "\n"
            texto += self.inicializador.formatar(nivel + 1)

        return texto

class Numero:
    def __init__(self, valor, linha):
        self.valor = valor
        self.linha = linha
    
    def formatar(self, nivel=0):
        espacos = "  " * nivel
        return f"{espacos}Numero ({self.valor})"
    
class Identificador:
    def __init__(self, nome, linha):
        self.nome = nome
        self.linha = linha

    def formatar(self, nivel=0):
        espacos = "  " * nivel
        return f"{espacos}Identificador ({self.nome})"

class OperacaoBinaria:
    def __init__(
        self,
        esquerda,
        operador,
        direita,
        linha
    ):
        self.esquerda = esquerda
        self.operador = operador
        self.direita = direita
        self.linha = linha

    def formatar(self, nivel=0):
        espacos = "  " * nivel
        
        linhas = [
            f"{espacos}OperacaoBinaria ({self.operador})",
            self.esquerda.formatar(nivel + 1),
            self.direita.formatar(nivel + 1)
        ]

        return "\n".join(linhas)

class Atribuicao:
    def __init__(self, nome, valor, linha):
        self.nome = nome
        self.valor = valor
        self.linha = linha

    def formatar(self, nivel=0):
        espacos = "  " * nivel

        linhas = [
            f"{espacos}Atribuicao (nome={self.nome})",
            self.valor.formatar(nivel + 1)
        ]

        return "\n".join(linhas)
    
class Retorno:
    def __init__(self, valor, linha):
        self.valor = valor
        self.linha = linha

    def formatar(self, nivel=0):
        espacos = "  " * nivel

        linhas = [
            f"{espacos}Retorno",
            self.valor.formatar(nivel + 1)
        ]

        return "\n".join(linhas)