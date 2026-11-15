"""
Análise semântica do Mini Compilador C.

Percorre a árvore sintática verificando:

Erros
  - variável usada ou atribuída sem ter sido declarada;
  - variável declarada mais de uma vez;
  - texto ("...") atribuído a variável numérica (int, float, char);
  - operadores aritméticos aplicados a texto;
  - operador '%' com operandos do tipo float;
  - retorno de um valor do tipo texto.

Avisos
  - conversão implícita de float para int/char (perda de precisão);
  - variável usada antes de receber um valor;
  - divisão por zero com divisor constante;
  - código inalcançável após 'return';
  - variável declarada e nunca utilizada.

O programa é tratado como o corpo de 'int main()', portanto o valor
retornado deve ser compatível com int.
"""

from src.arvore_sintatica import Numero, NumeroReal, Caractere


ERRO = "erro"
AVISO = "aviso"

TIPO_RETORNO = "int"


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
    def __init__(self, nome, tipo, linha, coluna, inicializada):
        self.nome = nome
        self.tipo = tipo
        self.linha = linha
        self.coluna = coluna
        self.inicializada = inicializada
        self.utilizada = False
        self.aviso_nao_inicializada = False

    def para_dict(self):
        return {
            "name": self.nome,
            "type": self.tipo,
            "line": self.linha,
            "initialized": self.inicializada,
            "used": self.utilizada,
        }


class AnalisadorSemantico:
    def __init__(self):
        self.variaveis = {}
        self.diagnosticos = []
        self.linha_retorno = None
        self.aviso_inalcancavel = False

    # ------------------------------------------------------------------
    # Interface pública
    # ------------------------------------------------------------------

    def analisar(self, programa):
        for comando in programa.comandos:
            if self.linha_retorno is not None and not self.aviso_inalcancavel:
                self.aviso_inalcancavel = True
                self.avisar(
                    "Código inalcançável: comando após 'return' "
                    f"(linha {self.linha_retorno})",
                    comando
                )

            self.visitar(comando)

        for variavel in self.variaveis.values():
            if not variavel.utilizada:
                self.diagnosticos.append(Diagnostico(
                    AVISO,
                    f"Variável '{variavel.nome}' declarada mas nunca utilizada",
                    variavel.linha,
                    variavel.coluna
                ))

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
            partes.append(f"{total_erros} erro{'s' if total_erros > 1 else ''}")
        if total_avisos:
            partes.append(f"{total_avisos} aviso{'s' if total_avisos > 1 else ''}")

        return "Análise semântica concluída com " + " e ".join(partes) + "."

    def para_dict(self):
        return {
            "success": self.sucesso,
            "errors": len(self.erros),
            "warnings": len(self.avisos),
            "message": self.resumo(),
            "diagnostics": [d.para_dict() for d in self.diagnosticos],
            "variables": [v.para_dict() for v in self.variaveis.values()],
        }

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------

    def errar(self, mensagem, no):
        self.diagnosticos.append(
            Diagnostico(ERRO, mensagem, no.linha, getattr(no, "coluna", None))
        )

    def avisar(self, mensagem, no):
        self.diagnosticos.append(
            Diagnostico(AVISO, mensagem, no.linha, getattr(no, "coluna", None))
        )

    def visitar(self, no):
        metodo = getattr(self, f"visitar_{type(no).__name__}", None)

        if metodo is None:
            raise NotImplementedError(
                f"Nó sem regra semântica: {type(no).__name__}"
            )

        return metodo(no)

    def verificar_compatibilidade(self, destino, origem, no, contexto):
        """Verifica se um valor do tipo 'origem' pode ser guardado em 'destino'."""
        if origem is None:
            # O erro da expressão já foi reportado.
            return

        if origem == "texto":
            self.errar(
                f"Tipos incompatíveis: não é possível atribuir texto "
                f"a {contexto} do tipo {destino}",
                no
            )
            return

        if origem == "float" and destino in {"int", "char"}:
            self.avisar(
                f"Conversão implícita de float para {destino} em "
                f"{contexto} pode perder precisão",
                no
            )

    @staticmethod
    def eh_zero_constante(no):
        if isinstance(no, (Numero, NumeroReal)):
            return float(no.valor) == 0
        if isinstance(no, Caractere):
            return no.valor == "\0"
        return False

    # ------------------------------------------------------------------
    # Comandos
    # ------------------------------------------------------------------

    def visitar_Declaracao(self, no):
        tipo_valor = None

        if no.inicializador is not None:
            tipo_valor = self.visitar(no.inicializador)

        existente = self.variaveis.get(no.nome)

        if existente is not None:
            self.errar(
                f"Variável '{no.nome}' já foi declarada na linha "
                f"{existente.linha}",
                no
            )
        else:
            self.variaveis[no.nome] = Variavel(
                no.nome,
                no.tipo,
                no.linha,
                no.coluna,
                inicializada=no.inicializador is not None
            )

        if no.inicializador is not None:
            self.verificar_compatibilidade(
                no.tipo,
                tipo_valor,
                no,
                f"variável '{no.nome}'"
            )

    def visitar_Atribuicao(self, no):
        tipo_valor = self.visitar(no.valor)

        variavel = self.variaveis.get(no.nome)

        if variavel is None:
            self.errar(f"Variável '{no.nome}' não foi declarada", no)
            return

        self.verificar_compatibilidade(
            variavel.tipo,
            tipo_valor,
            no,
            f"variável '{no.nome}'"
        )

        variavel.inicializada = True

    def visitar_Retorno(self, no):
        tipo_valor = self.visitar(no.valor)

        if tipo_valor == "texto":
            self.errar(
                f"Tipos incompatíveis: o retorno deve ser do tipo "
                f"{TIPO_RETORNO}, mas recebeu texto",
                no
            )
        elif tipo_valor is not None:
            self.verificar_compatibilidade(
                TIPO_RETORNO,
                tipo_valor,
                no,
                "valor de retorno"
            )

        if self.linha_retorno is None:
            self.linha_retorno = no.linha

    # ------------------------------------------------------------------
    # Expressões (retornam o tipo resultante ou None em caso de erro)
    # ------------------------------------------------------------------

    def visitar_Numero(self, no):
        return "int"

    def visitar_NumeroReal(self, no):
        return "float"

    def visitar_Caractere(self, no):
        return "char"

    def visitar_Texto(self, no):
        return "texto"

    def visitar_Identificador(self, no):
        variavel = self.variaveis.get(no.nome)

        if variavel is None:
            self.errar(f"Variável '{no.nome}' não foi declarada", no)
            return None

        variavel.utilizada = True

        if not variavel.inicializada and not variavel.aviso_nao_inicializada:
            variavel.aviso_nao_inicializada = True
            self.avisar(
                f"Variável '{no.nome}' utilizada antes de receber um valor",
                no
            )

        return variavel.tipo

    def visitar_OperacaoUnaria(self, no):
        tipo = self.visitar(no.operando)

        if tipo is None:
            return None

        if tipo == "texto":
            self.errar(
                f"Operador unário '{no.operador}' não pode ser aplicado a texto",
                no
            )
            return None

        # char é promovido para int em expressões aritméticas.
        return "float" if tipo == "float" else "int"

    def visitar_OperacaoBinaria(self, no):
        tipo_esq = self.visitar(no.esquerda)
        tipo_dir = self.visitar(no.direita)

        if tipo_esq is None or tipo_dir is None:
            return None

        if "texto" in (tipo_esq, tipo_dir):
            self.errar(
                f"Operador '{no.operador}' não pode ser aplicado a texto",
                no
            )
            return None

        if no.operador == "%" and "float" in (tipo_esq, tipo_dir):
            self.errar(
                "Operador '%' exige operandos inteiros (recebeu float)",
                no
            )
            return None

        if no.operador in {"/", "%"} and self.eh_zero_constante(no.direita):
            self.avisar("Divisão por zero", no)

        if "float" in (tipo_esq, tipo_dir):
            return "float"

        return "int"
