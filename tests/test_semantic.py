"""Testes unitários para o Analisador Semântico."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.compilador import compilar


def semantico(codigo):
    return compilar(codigo).semantico


def mensagens(diagnosticos):
    return [d.mensagem for d in diagnosticos]


class TestSemantico(unittest.TestCase):
    def test_programa_valido(self):
        s = semantico(
            "int idade = 20; int total = 0; total = idade + 5 * 2; return total;"
        )
        self.assertTrue(s.sucesso)
        self.assertEqual(s.diagnosticos, [])

    def test_variavel_nao_declarada_em_expressao(self):
        s = semantico("int a = 1; return a + b;")
        self.assertFalse(s.sucesso)
        self.assertEqual(mensagens(s.erros), ["Variável 'b' não foi declarada"])
        self.assertEqual((s.erros[0].linha, s.erros[0].coluna), (1, 23))

    def test_atribuicao_a_variavel_nao_declarada(self):
        s = semantico("int resultado = 10; total = resultado + 5;")
        self.assertEqual(mensagens(s.erros), ["Variável 'total' não foi declarada"])

    def test_redeclaracao(self):
        s = semantico("int a = 1;\nfloat a = 2.0;\nreturn a;")
        self.assertEqual(len(s.erros), 1)
        self.assertIn("já foi declarada na linha 1", s.erros[0].mensagem)

    def test_texto_em_variavel_int(self):
        s = semantico('int resultado = "texto"; return resultado;')
        self.assertEqual(len(s.erros), 1)
        self.assertIn("Tipos incompatíveis", s.erros[0].mensagem)

    def test_operacao_com_texto(self):
        s = semantico('int a = 1 + "x"; return a;')
        self.assertEqual(
            mensagens(s.erros), ["Operador '+' não pode ser aplicado a texto"]
        )

    def test_modulo_com_float(self):
        s = semantico("float f = 2.5; int r = 7 % f; return r;")
        self.assertEqual(len(s.erros), 1)
        self.assertIn("'%'", s.erros[0].mensagem)

    def test_retorno_de_texto(self):
        s = semantico('return "oi";')
        self.assertEqual(len(s.erros), 1)

    def test_promocoes_validas(self):
        s = semantico(
            "char c = 'A'; int i = c + 1; float f = i * 2; f = f / 3; return i;"
        )
        self.assertTrue(s.sucesso)
        self.assertEqual(s.diagnosticos, [])

    def test_aviso_perda_de_precisao(self):
        s = semantico("float f = 1.5; int i = f * 2; return i;")
        self.assertTrue(s.sucesso)
        self.assertEqual(len(s.avisos), 1)
        self.assertIn("perder precisão", s.avisos[0].mensagem)

    def test_aviso_variavel_sem_valor(self):
        s = semantico("int a; int b = a + 1; return b;")
        self.assertTrue(s.sucesso)
        self.assertEqual(
            mensagens(s.avisos), ["Variável 'a' utilizada antes de receber um valor"]
        )

    def test_aviso_divisao_por_zero(self):
        s = semantico("int a = 10 / 0; return a;")
        self.assertEqual(mensagens(s.avisos), ["Divisão por zero"])

    def test_aviso_codigo_inalcancavel(self):
        s = semantico("int a = 1; return a; a = 2;")
        self.assertTrue(any("inalcançável" in m for m in mensagens(s.avisos)))

    def test_aviso_variavel_nao_utilizada(self):
        s = semantico("int a = 1; int b = 2; return a;")
        self.assertEqual(
            mensagens(s.avisos), ["Variável 'b' declarada mas nunca utilizada"]
        )

    def test_varios_erros_sao_acumulados(self):
        s = semantico('int a = x; int b = "t"; c = 1; return a + b;')
        self.assertEqual(len(s.erros), 3)

    def test_variavel_nao_pode_ser_usada_no_proprio_inicializador(self):
        s = semantico("int a = a + 1; return a;")
        self.assertEqual(mensagens(s.erros), ["Variável 'a' não foi declarada"])

    def test_para_dict(self):
        dados = semantico("int a = b; return a;").para_dict()
        self.assertFalse(dados["success"])
        self.assertEqual(dados["errors"], 1)
        self.assertEqual(dados["diagnostics"][0]["severity"], "erro")
        self.assertEqual(dados["diagnostics"][0]["line"], 1)


if __name__ == "__main__":
    unittest.main()
