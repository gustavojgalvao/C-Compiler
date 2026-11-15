class ErroCompilacao(Exception):
    """Erro base de todas as etapas do compilador (com posição no código)."""

    etapa = "Compilação"

    def __init__(self, mensagem, linha=None, coluna=None):
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna

        texto = mensagem

        if linha is not None:
            texto += f" na linha {linha}"

            if coluna is not None:
                texto += f", coluna {coluna}"

        super().__init__(texto)


class ErroLexico(ErroCompilacao):
    etapa = "Léxica"


class ErroSintatico(ErroCompilacao):
    etapa = "Sintática"

    def __init__(self, mensagem, token):
        super().__init__(mensagem, token.linha, token.coluna)
