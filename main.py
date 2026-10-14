from src.lexer import Lexer

codigo = """int idade = 20;
int total = idade + 5;
return total;
"""

lexer = Lexer(codigo)
tokens = lexer.tokenizar()

for token in tokens: 
    print(token)
