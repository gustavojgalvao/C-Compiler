import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

from src.lexer import Lexer
from src.tabela_simbolos import TabelaSimbolos
from src.parser import Parser, ErroSintatico
from src.arvore_sintatica import (
    Programa,
    Declaracao,
    Atribuicao,
    Retorno,
    OperacaoBinaria,
    Identificador,
    Numero
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")


def ast_para_json(no):
    """Converte os nos da AST em uma arvore propria para a interface."""
    if isinstance(no, Programa):
        return {
            "kind": "program",
            "label": "Programa",
            "children": [ast_para_json(comando) for comando in no.comandos]
        }

    if isinstance(no, Declaracao):
        filhos = []
        if no.inicializador is not None:
            filhos.append(ast_para_json(no.inicializador))
        return {
            "kind": "declaration",
            "label": "Declaracao",
            "detail": f"{no.tipo} {no.nome}",
            "line": no.linha,
            "children": filhos
        }

    if isinstance(no, Atribuicao):
        return {
            "kind": "assignment",
            "label": "Atribuicao",
            "detail": no.nome,
            "line": no.linha,
            "children": [ast_para_json(no.valor)]
        }

    if isinstance(no, Retorno):
        return {
            "kind": "return",
            "label": "Return",
            "line": no.linha,
            "children": [ast_para_json(no.valor)]
        }

    if isinstance(no, OperacaoBinaria):
        return {
            "kind": "operator",
            "label": no.operador,
            "detail": "operador",
            "line": no.linha,
            "children": [ast_para_json(no.esquerda), ast_para_json(no.direita)]
        }

    if isinstance(no, Identificador):
        return {
            "kind": "identifier",
            "label": no.nome,
            "detail": "identificador",
            "line": no.linha,
            "children": []
        }

    if isinstance(no, Numero):
        return {
            "kind": "number",
            "label": no.valor,
            "detail": "numero",
            "line": no.linha,
            "children": []
        }

    raise TypeError(f"No desconhecido na AST: {type(no).__name__}")


class CompilerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def enviar_json(self, dados, status=200):
        conteudo = json.dumps(
            dados,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header(
            "Content-Length",
            str(len(conteudo))
        )
        self.end_headers()

        self.wfile.write(conteudo)

    def do_POST(self):
        caminho = urlparse(self.path).path

        if caminho != "/api/analyze":
            self.enviar_json(
                {
                    "success": False,
                    "error": "Endpoint não encontrado."
                },
                404
            )
            return

        try:
            tamanho = int(
                self.headers.get("Content-Length", 0)
            )

            corpo = self.rfile.read(tamanho)
            dados = json.loads(corpo.decode("utf-8"))

            codigo = dados.get("code", "")

            if not codigo.strip():
                self.enviar_json({
                    "success": False,
                    "error_stage": "Entrada",
                    "error": "O código-fonte está vazio.",
                    "line": 1,
                    "column": 1
                })
                return

            # Primeira etapa: análise léxica
            lexer = Lexer(codigo)
            tokens = lexer.tokenizar()

            # Tabela de símbolos
            tabela = TabelaSimbolos()
            tabela.construir(tokens)

            # Segunda etapa: análise sintática
            parser = Parser(tokens)
            arvore = parser.analisar()

            tokens_json = []

            for token in tokens:
                tokens_json.append({
                    "tipo": token.tipo,
                    "lexema": token.lexema,
                    "linha": token.linha,
                    "coluna": token.coluna
                })

            simbolos_json = []

            for simbolo in tabela.simbolos:
                simbolos_json.append({
                    "ordem": simbolo.ordem,
                    "lexema": simbolo.lexema,
                    "categoria": simbolo.categoria,
                    "tipo": simbolo.tipo,
                    "linha": simbolo.linha
                })

            resposta = {
                "success": True,
                "tokens": tokens_json,
                "symbols": simbolos_json,

                "ast": ast_para_json(arvore),
                "ast_pretty": arvore.formatar(),
                "semantic": {
                    "message": (
                        "Análise semântica ainda não implementada."
                    )
                }
            }

            self.enviar_json(resposta)
        
        except ErroSintatico as erro:
            self.enviar_json({
                "success": False,
                "error_stage": "Sintática",
                "error": str(erro),
                "line": erro.linha,
                "column": erro.coluna
            })

        except json.JSONDecodeError:
            self.enviar_json({
                "success": False,
                "error_stage": "Entrada",
                "error": "O servidor recebeu um JSON inválido.",
                "line": 1,
                "column": 1
            })

        except Exception as erro:
            self.enviar_json({
                "success": False,
                "error_stage": "Léxica",
                "error": str(erro),
                "line": 1,
                "column": 1
            })


def iniciar_servidor(porta=5000):
    endereco = ("localhost", porta)
    servidor = HTTPServer(endereco, CompilerHandler)

    print("-" * 60)
    print("Mini Compilador C")
    print(f"Servidor: http://localhost:{porta}")
    print("Use Ctrl+C para encerrar.")
    print("-" * 60)

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    iniciar_servidor()
