"""Testes com programas em C "de verdade" (funções, controle de fluxo, ponteiros)."""
import glob
import os
import sys
import unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)

from src.lexer import Lexer
from src.parser import Parser, ErroSintatico
from src.compilador import compilar
from src.arvore_sintatica import (
    Funcao, Se, Para, Escolha, Chamada, OperacaoBinaria, Condicional, Conversao,
    Declaracao, Indexacao, OperacaoUnaria,
)


def tipos(codigo):
    return [t.tipo for t in Lexer(codigo).tokenizar()][:-1]


def analisar(codigo):
    return Parser(Lexer(codigo).tokenizar()).analisar()


def semantico(codigo):
    return compilar(codigo).semantico


def mensagens(diagnosticos):
    return [d.mensagem for d in diagnosticos]


PROGRAMA_COMPLETO = r"""
#include <stdio.h>
#include <string.h>
#define MAX 5

int soma(int v[], int n);

int main(void) {
    int numeros[MAX] = {4, 8, 15, 16, 23};
    char nome[20] = "Maria";
    int i, opcao;
    int *p = &numeros[0];

    scanf("%d", &opcao);

    switch (opcao) {
        case 1: printf("%d\n", soma(numeros, MAX)); break;
        default: printf("nada\n");
    }

    for (i = 0; i < MAX; i++) {
        if (numeros[i] % 2 == 0 && numeros[i] > 5) {
            opcao += 1;
        } else if (numeros[i] == 15) {
            continue;
        }
    }

    while (*p != 23) p++;

    printf("%s %d %.2f\n", nome, (int) strlen(nome), (double) opcao / 2);
    return opcao > 0 ? 0 : 1;
}

int soma(int v[], int n) {
    int total = 0;
    for (int k = 0; k < n; k++)
        total += v[k];
    return total;
}
"""


class TestLexerC(unittest.TestCase):
    def test_operadores_de_dois_caracteres(self):
        self.assertEqual(
            tipos("a == b != c <= d >= e && f || g ++ -- += -="),
            ["IDENTIFICADOR", "IGUAL_IGUAL", "IDENTIFICADOR", "DIFERENTE",
             "IDENTIFICADOR", "MENOR_IGUAL", "IDENTIFICADOR", "MAIOR_IGUAL",
             "IDENTIFICADOR", "E_LOGICO", "IDENTIFICADOR", "OU_LOGICO",
             "IDENTIFICADOR", "INCREMENTO", "DECREMENTO", "MAIS_IGUAL", "MENOS_IGUAL"],
        )

    def test_include_e_ignorado_e_define_e_expandido(self):
        lexer = Lexer("#include <stdio.h>\n#define TAM 10\nint v = TAM;")
        tokens = lexer.tokenizar()
        self.assertEqual(lexer.inclusoes, ["stdio.h"])
        self.assertEqual([t.lexema for t in tokens[:-1]], ["int", "v", "=", "10", ";"])
        self.assertEqual(tokens[3].linha, 3)

    def test_escapes_e_numeros(self):
        tokens = Lexer(r"'\n' " + '"a\\"b" 1e3 2.5f 10L').tokenizar()
        self.assertEqual(
            [(t.tipo, t.lexema) for t in tokens[:-1]],
            [("CARACTERE", "\\n"), ("TEXTO", 'a\\"b'), ("NUMERO_REAL", "1e3"),
             ("NUMERO_REAL", "2.5f"), ("NUMERO", "10L")],
        )


class TestParserC(unittest.TestCase):
    def test_funcoes_e_prototipos(self):
        arvore = analisar("int f(int a, char *b); int f(int a, char *b) { return a; }")
        prototipo, definicao = arvore.comandos
        self.assertIsInstance(prototipo, Funcao)
        self.assertIsNone(prototipo.corpo)
        self.assertEqual([p.tipo for p in definicao.parametros], ["int", "char*"])

    def test_controle_de_fluxo(self):
        corpo = analisar(
            "int main() { if (a) b = 1; else b = 2; for (int i = 0; i < 3; i++) {} "
            "switch (x) { case 1: break; default: ; } }"
        ).comandos[0].corpo.comandos
        self.assertEqual([type(c) for c in corpo], [Se, Para, Escolha])
        self.assertEqual(len(corpo[2].casos), 2)

    def test_precedencia_logica(self):
        expr = analisar("x = a == 1 || b < 2 && c;").comandos[0].valor
        self.assertEqual(expr.operador, "||")
        self.assertEqual(expr.esquerda.operador, "==")
        self.assertEqual(expr.direita.operador, "&&")

    def test_posfixos_cast_e_ternario(self):
        expr = analisar("y = (double) f(v[1], &x) > 0 ? -1 : *p;").comandos[0].valor
        self.assertIsInstance(expr, Condicional)
        conversao = expr.condicao.esquerda
        self.assertIsInstance(conversao, Conversao)
        self.assertIsInstance(conversao.expressao, Chamada)
        self.assertIsInstance(conversao.expressao.argumentos[0], Indexacao)
        self.assertIsInstance(expr.se_falso, OperacaoUnaria)

    def test_declaracao_multipla(self):
        decls = analisar("int a = 1, *p, v[3] = {1, 2, 3};").comandos
        self.assertEqual([type(d) for d in decls], [Declaracao] * 3)
        self.assertEqual([(d.tipo, d.eh_array) for d in decls],
                         [("int", False), ("int*", False), ("int", True)])

    def test_erros_de_sintaxe(self):
        for codigo in ["int main() { if x > 1 return 0; }",
                       "int main() { return 0;",
                       "int main() { for (i = 0; i < 3) {} }",
                       "int main() { p.; }"]:
            with self.subTest(codigo=codigo), self.assertRaises(ErroSintatico):
                analisar(codigo)


class TestSemanticoC(unittest.TestCase):
    def test_amostras_validas(self):
        arquivos = sorted(glob.glob(os.path.join(RAIZ, "tests", "c_samples", "*.c")))
        self.assertTrue(arquivos)
        for arquivo in arquivos:
            with self.subTest(arquivo=os.path.basename(arquivo)):
                with open(arquivo, encoding="utf-8") as f:
                    s = semantico(f.read())
                self.assertEqual(mensagens(s.diagnosticos), [])

    def test_programa_completo_valido(self):
        s = semantico(PROGRAMA_COMPLETO)
        self.assertEqual(mensagens(s.diagnosticos), [])

    def esperar_erro(self, codigo, trecho):
        s = semantico(codigo)
        self.assertTrue(
            any(trecho in m for m in mensagens(s.erros)),
            f"esperado erro com {trecho!r}, veio {mensagens(s.diagnosticos)}",
        )

    def esperar_aviso(self, codigo, trecho):
        s = semantico(codigo)
        self.assertTrue(
            any(trecho in m for m in mensagens(s.avisos)),
            f"esperado aviso com {trecho!r}, veio {mensagens(s.diagnosticos)}",
        )

    def test_erros_de_funcao(self):
        self.esperar_erro("int main() { return f(1); }", "Função 'f' não foi declarada")
        self.esperar_erro("int g(int a) { return a; } int main() { return g(1, 2); }",
                          "espera 1 argumento, mas recebeu 2")
        self.esperar_erro("void g() { return 1; } int main() { g(); return 0; }",
                          "não pode retornar um valor")
        self.esperar_erro("int g(); int main() { return g(); }",
                          "declarada mas nunca foi definida")
        self.esperar_erro("int main() { int x = 1; return x(); }", "não uma função")

    def test_erros_de_comando(self):
        self.esperar_erro("int main() { break; return 0; }", "'break' fora")
        self.esperar_erro("int main() { continue; return 0; }", "'continue' fora")
        self.esperar_erro("int x = 1; x = 2; int main() { return x; }", "fora de uma função")
        self.esperar_erro("int main() { int v[3]; v = 0; return 0; }", "array inteiro")
        self.esperar_erro(
            "int main() { int x = 1; switch (x) { case 1: break; case 1: break; } return 0; }",
            "repetido",
        )

    def test_erros_de_ponteiro(self):
        self.esperar_erro("int main() { int x = 1; return *x; }", "exige um ponteiro")
        self.esperar_erro("int main() { char *s = 5; return 0; }", "Tipos incompatíveis")
        self.esperar_erro("int main() { int *p; float *q = p; return 0; }", "Tipos incompatíveis")

    def test_ponteiro_nulo_e_aritmetica_sao_validos(self):
        s = semantico(
            "int main() { int v[2] = {1, 2}; int *p = 0; int *q = NULL; "
            "p = v + 1; q = p; return *q - (int) (p - v); }"
        )
        self.assertEqual(mensagens(s.diagnosticos), [])

    def test_escopos(self):
        s = semantico("int main() { int a = 1; { int a = 2; a++; } return a; }")
        self.assertTrue(s.sucesso)
        self.esperar_erro("int main() { { int b = 2; b++; } return b; }",
                          "Variável 'b' não foi declarada")

    def test_avisos_de_c(self):
        self.esperar_aviso("int main() { int x; scanf(\"%d\", x); return x; }", "faltou o '&'")
        self.esperar_aviso("int main() { printf(\"%d %d\", 1); return 0; }", "pede 2 valores")
        self.esperar_aviso("int main() { int x = 1; if (x = 2) x++; return x; }", "'=='")
        self.esperar_aviso("int main() { int v[3]; v[3] = 1; return v[0]; }", "fora dos limites")
        self.esperar_aviso("int f(int a) { if (a) return 1; } int main() { return f(1); }",
                           "pode terminar sem retornar")
        self.esperar_aviso("int main() { int a = 1; a + 1; return a; }", "sem efeito")
        self.esperar_aviso("int main() { return f(); } int f() { return 1; }",
                           "antes de ser declarada")

    def test_scanf_inicializa_variavel(self):
        s = semantico('int main() { int n; scanf("%d", &n); return n; }')
        self.assertEqual(mensagens(s.diagnosticos), [])


PROGRAMA_STRUCTS = r"""
#include <stdio.h>
#include <stdbool.h>
#include <locale.h>

struct Ponto { int x, y; };

typedef struct {
    char nome[30];
    float notas[3];
    struct Ponto posicao;
} Aluno;

float media(Aluno *a) {
    float soma = 0;
    for (int i = 0, j = 2; i < 3; i++, j--)
        soma += a->notas[i];
    return soma / 3;
}

int main() {
    setlocale(LC_ALL, "Portuguese");
    int m[2][3] = {{1, 2, 3}, {4, 5, 6}};
    Aluno turma[2];
    struct Ponto p = {1, 2};
    bool ok = true;
    int flags = 0x0F & (1 << 2) | 8;

    turma[0].notas[0] = 9.5;
    turma[0].posicao = p;
    fgets(turma[0].nome, 30, stdin);
    printf("%.1f %d %d\n", media(&turma[0]), m[1][2], flags);
    return ok ? 0 : 1;
}
"""


class TestRecursosAvancados(unittest.TestCase):
    def test_programa_com_structs_matrizes_e_bibliotecas(self):
        s = semantico(PROGRAMA_STRUCTS)
        self.assertEqual(mensagens(s.diagnosticos), [])

    def test_bom_e_hexadecimal(self):
        tokens = Lexer("﻿int x = 0xFF;").tokenizar()
        self.assertEqual(tokens[0].tipo, "INT")
        self.assertEqual(tokens[3].lexema, "0xFF")

    def test_erros_de_struct(self):
        casos = [
            ("struct P { int x; }; int main() { struct P p; p.y = 1; return 0; }",
             "não tem o campo 'y'"),
            ("struct P { int x; }; int main() { struct P *p; p.x = 1; return 0; }",
             "use '->'"),
            ("int main() { struct Q q; return 0; }", "não foi definida"),
            ("struct P { int x; }; int main() { struct P p = {1}; int n = p; return n; }",
             "Tipos incompatíveis"),
        ]
        for codigo, trecho in casos:
            with self.subTest(codigo=codigo):
                s = semantico(codigo)
                self.assertTrue(any(trecho in m for m in mensagens(s.erros)),
                                mensagens(s.diagnosticos))

    def test_funcao_desconhecida_com_include_vira_aviso(self):
        s = semantico("#include <conio2.h>\nint main() { textcolor(2); return 0; }")
        self.assertTrue(s.sucesso)
        self.assertIn("não é conhecida", s.avisos[0].mensagem)

        s = semantico("int main() { textcolor(2); return 0; }")
        self.assertFalse(s.sucesso)

    def test_operadores_bit_a_bit_exigem_inteiros(self):
        s = semantico("int main() { float f = 1.5; int x = f << 1; return x; }")
        self.assertIn("'<<' exige operandos inteiros", s.erros[0].mensagem)


if __name__ == "__main__":
    unittest.main()
