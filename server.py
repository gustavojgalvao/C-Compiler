"""
Servidor Web local em Python para o Compilador Visual de C.
Utiliza a biblioteca padrão do Python (http.server e json) sem necessidade de instalar pacotes externos.
"""
import sys
import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# Garante que a raiz do projeto está no sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.preprocessor.preprocessor import Preprocessor
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.ir_builder import IRBuilder
from src.ir.optimizer import IROptimizer
from src.ir.interpreter import IRExecutor
from src.codegen.x86_generator import X86CodeGenerator
from src.utils.errors import CompilerError

def ast_to_dict(node):
    """Converte nós da AST em formato serializável para JSON."""
    if node is None:
        return None
    if isinstance(node, (int, str, float, bool)):
        return node
    if isinstance(node, list):
        return [ast_to_dict(item) for item in node]
    if hasattr(node, "__dict__"):
        res = {"_type": node.__class__.__name__}
        for k, v in node.__dict__.items():
            res[k] = ast_to_dict(v)
        return res
    return str(node)

def format_ast_pretty(node, indent=0) -> str:
    """Gera uma visualização textual indentada da AST."""
    prefix = "  " * indent
    if node is None:
        return f"{prefix}None\n"
    if isinstance(node, (int, str, float, bool)):
        return f"{prefix}{node}\n"
    if isinstance(node, list):
        out = ""
        for item in node:
            out += format_ast_pretty(item, indent)
        return out
    if hasattr(node, "__dict__"):
        node_name = node.__class__.__name__
        out = f"{prefix}[{node_name}]\n"
        for k, v in node.__dict__.items():
            if isinstance(v, (list, tuple)):
                out += f"{prefix}  -> {k}: [\n{format_ast_pretty(v, indent + 2)}{prefix}  ]\n"
            elif hasattr(v, "__dict__"):
                out += f"{prefix}  -> {k}:\n{format_ast_pretty(v, indent + 2)}"
            else:
                out += f"{prefix}  -> {k}: {v}\n"
        return out
    return f"{prefix}{node}\n"

class CompilerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(BASE_DIR, "web"), **kwargs)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/compile":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")

            try:
                data = json.loads(body)
                source_code = data.get("code", "")
                clean_code = Preprocessor.strip_comments(source_code)

                # 1. Lexer
                lexer = Lexer(clean_code)
                tokens = lexer.tokenize()
                tokens_data = [
                    {
                        "type": t.type.name,
                        "value": t.value,
                        "line": t.line,
                        "column": t.column
                    }
                    for t in tokens
                ]

                # 2. Parser
                parser = Parser(tokens)
                ast = parser.parse()
                ast_dict = ast_to_dict(ast)
                ast_text = format_ast_pretty(ast)

                # 3. Semântica
                analyzer = SemanticAnalyzer()
                analyzer.analyze(ast)

                # 4. IR
                ir_builder = IRBuilder()
                ir_prog = ir_builder.build(ast)

                ir_unoptimized = [str(f) for f in ir_prog.functions]

                # 5. Otimização
                optimizer = IROptimizer()
                ir_prog = optimizer.optimize(ir_prog)
                ir_optimized = [str(f) for f in ir_prog.functions]

                # 6. Geração de Código x86-64
                codegen = X86CodeGenerator()
                assembly = codegen.generate(ir_prog)

                # 7. Execução
                executor = IRExecutor(ir_prog)
                result = executor.run("main")

                response_payload = {
                    "success": True,
                    "tokens": tokens_data,
                    "ast": ast_dict,
                    "ast_pretty": ast_text,
                    "ir_unoptimized": "\n\n".join(ir_unoptimized),
                    "ir_optimized": "\n\n".join(ir_optimized),
                    "assembly": assembly,
                    "result": result,
                    "metrics": {
                        "tokens_count": len(tokens),
                        "functions_count": len(ast.functions),
                        "assembly_lines": len(assembly.splitlines())
                    }
                }

            except CompilerError as e:
                response_payload = {
                    "success": False,
                    "error_stage": e.__class__.__name__,
                    "error": str(e),
                    "line": e.line,
                    "column": e.column
                }
            except Exception as e:
                response_payload = {
                    "success": False,
                    "error_stage": "InternalError",
                    "error": f"Erro interno: {str(e)}",
                    "line": 1,
                    "column": 1
                }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response_payload).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint não encontrado")

def run_server(port=5000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, CompilerHandler)
    print("=" * 60)
    print(f"[*] COMPILADOR VISUAL DE C (PYTHON ENGINE)")
    print(f"[*] Servidor aberto em: http://localhost:{port}")
    print(f"[*] Abra o link no seu navegador para usar a interface interativa!")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")

if __name__ == "__main__":
    run_server()
