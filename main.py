from src.lexer import Lexer
from src.tabela_simbolos import TabelaSimbolos
from src.parser import Parser

codigo = """int idade = 20;
int total = idade + 5 * 2;
int resultado = (idade + 5) * 2;
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

parser = Parser(tokens)
arvore = parser.analisar()

print("\nÁRVORE SINTÁTICA")
print("-" * 70)
print(arvore.formatar())