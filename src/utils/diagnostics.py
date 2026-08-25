"""
Utilitário para exibição formatada de diagnósticos e mensagens de erro com destaque visual.
"""

def format_error_snippet(source_code: str, line: int, column: int, message: str) -> str:
    """
    Formata o trecho do código onde ocorreu o erro, adicionando uma seta indicadora (^) na coluna exata.
    """
    lines = source_code.splitlines()
    if 1 <= line <= len(lines):
        error_line = lines[line - 1]
        pointer = " " * (max(0, column - 1)) + "^"
        return f"\n{line:4d} | {error_line}\n     | {pointer}\nErro: {message}"
    return f"Erro [Linha {line}, Coluna {column}]: {message}"
