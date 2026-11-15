import sys

from src.compilador import compilar
from src.erros import ErroCompilacao


CODIGO_EXEMPLO = """int quantidade = 10;
float preco = 19.90;
char letra = 'A';
int erro = "texto";
return quantidade;
"""


def main(argumentos):
    if len(argumentos) > 1:
        with open(argumentos[1], encoding="utf-8") as arquivo:
            codigo = arquivo.read()
    else:
        codigo = CODIGO_EXEMPLO

    try:
        resultado = compilar(codigo)
    except ErroCompilacao as erro:
        print(f"ERRO {erro.etapa.upper()}: {erro}")
        return 1

    print("TOKENS")
    print("-" * 70)

    for token in resultado.tokens:
        print(token)

    resultado.tabela.exibir()

    print("\nÁRVORE SINTÁTICA")
    print("-" * 70)
    print(resultado.arvore.formatar())

    print("\nANÁLISE SEMÂNTICA")
    print("-" * 70)

    for diagnostico in resultado.semantico.diagnosticos:
        print(diagnostico)

    print(resultado.semantico.resumo())

    return 0 if resultado.sucesso else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
