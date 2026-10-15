import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

from src.lexer import Lexer
from src.tabela_simbolos import TabelaSimbolos
from src.parser import Parser, ErroSintatico


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")


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
