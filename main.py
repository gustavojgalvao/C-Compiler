import sys

from src.compilador import compilar
from src.erros import ErroCompilacao


CODIGO_EXEMPLO = """double nota1, nota2, media;
    printf("Informe as notas do aluno:\n");
    scanf("%lf %lf", &nota1, &nota2);
    media = (nota1 + nota2) / 2;
    printf("A média do aluno é: %lf\n", media);
    return 0;
"""


def ler_arquivo(caminho):
    """Lê o arquivo em UTF-8 (com ou sem BOM) ou, se falhar, em Windows-1252 (ANSI)."""
    with open(caminho, "rb") as arquivo:
        dados = arquivo.read()

    try:
        return dados.decode("utf-8-sig")
    except UnicodeDecodeError:
        return dados.decode("cp1252", errors="replace")


def main(argumentos):
    if len(argumentos) > 1:
        try:
            codigo = ler_arquivo(argumentos[1])
        except OSError as erro:
            print(f"Não foi possível abrir '{argumentos[1]}': {erro.strerror}")
            return 1
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
