from src.lexer import Lexer

codigo = """
int idade = 20;
return idade;
"""

lexer = Lexer(codigo)
tokens = lexer.tokenizar()

for token in tokens: 
    print(token)