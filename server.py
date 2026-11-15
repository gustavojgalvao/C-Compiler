import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

from src.compilador import compilar
from src.erros import ErroCompilacao


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

    def enviar_erro(self, etapa, mensagem, linha=1, coluna=1):
        self.enviar_json({
            "success": False,
            "error_stage": etapa,
            "error": mensagem,
            "line": linha,
            "column": coluna
        })

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
                self.enviar_erro("Entrada", "O código-fonte está vazio.")
                return

            resultado = compilar(codigo)

            tokens_json = [
                {
                    "tipo": token.tipo,
                    "lexema": token.lexema,
                    "linha": token.linha,
                    "coluna": token.coluna
                }
                for token in resultado.tokens
            ]

            simbolos_json = [
                {
                    "ordem": simbolo.ordem,
                    "lexema": simbolo.lexema,
                    "categoria": simbolo.categoria,
                    "tipo": simbolo.tipo,
                    "linha": simbolo.linha
                }
                for simbolo in resultado.tabela.simbolos
            ]

            self.enviar_json({
                "success": True,
                "tokens": tokens_json,
                "symbols": simbolos_json,
                "ast_pretty": resultado.arvore.formatar(),
                "semantic": resultado.semantico.para_dict()
            })

        except ErroCompilacao as erro:
            self.enviar_erro(
                erro.etapa,
                str(erro),
                erro.linha,
                erro.coluna
            )

        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            self.enviar_erro(
                "Entrada",
                "O servidor recebeu uma requisição inválida."
            )

        except Exception as erro:
            self.enviar_erro("Interna", f"Erro interno: {erro}")


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
