from src.lexer import Lexer
from src.tabela_simbolos import TabelaSimbolos

codigo = """int idade = 20;
int total = idade + 5;
return total;
"""

lexer = Lexer(codigo)
tokens = lexer.tokenizar()

print("TOKENS")
print("-" * 70)

for token in tokens:
    print(token)

tabela = TabelaSimbolos()
tabela.construir(tokens)
tabela.exibir()