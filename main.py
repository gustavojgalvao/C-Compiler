from src.lexer import Lexer
from src.tabela_simbolos import TabelaSimbolos
from src.parser import Parser

codigo = """int quantidade = 10;
float preco = 19.90;
char letra = 'A';
int erro = "texto";
return quantidade;
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