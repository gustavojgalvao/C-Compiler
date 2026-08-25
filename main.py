"""
Driver principal do compilador de C.
Compila o código-fonte C, gera o Assembly x86-64 e executa o programa para exibir o resultado final.
"""
import sys
import os
import argparse
import subprocess
import shutil

from src.preprocessor.preprocessor import Preprocessor
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.ir_builder import IRBuilder
from src.ir.optimizer import IROptimizer
from src.ir.interpreter import IRExecutor
from src.codegen.x86_generator import X86CodeGenerator
from src.utils.errors import CompilerError
from src.utils.diagnostics import format_error_snippet

def compile_and_run(source_code: str, emit_ir: bool = False, emit_assembly: bool = False):
    """Executa o pipeline completo de compilação e a execução do programa."""
    # 1. Análise Léxica
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()

    # 2. Análise Sintática
    parser = Parser(tokens)
    ast = parser.parse()

    # 3. Análise Semântica
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    # 4. Geração de Representação Intermediária (IR)
    ir_builder = IRBuilder()
    ir_prog = ir_builder.build(ast)

    # 5. Otimização de Código
    optimizer = IROptimizer()
    ir_prog = optimizer.optimize(ir_prog)

    if emit_ir:
        print("\n--- [Representação Intermediária (IR)] ---")
        for func in ir_prog.functions:
            print(func)
            print("-" * 35)

    # 6. Geração de Código Assembly x86-64
    codegen = X86CodeGenerator()
    assembly_code = codegen.generate(ir_prog)

    # 7. Execução direta para obter o resultado
    executor = IRExecutor(ir_prog)
    exit_code = executor.run("main")

    return assembly_code, exit_code

def main():
    parser = argparse.ArgumentParser(description="Compilador de C em Python (Subconjunto C0)")
    parser.add_argument("input_file", help="Arquivo-fonte C (.c) para compilar")
    parser.add_argument("-o", "--output", help="Nome do arquivo executável final de saída")
    parser.add_argument("-S", "--assembly", action="store_true", help="Salvar arquivo assembly (.s) em disco")
    parser.add_argument("--emit-ir", action="store_true", help="Imprimir a Representação Intermediária (IR)")
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Erro: Arquivo '{args.input_file}' não encontrado.", file=sys.stderr)
        sys.exit(1)

    try:
        raw_source = open(args.input_file, "r", encoding="utf-8").read()
        clean_source = Preprocessor.strip_comments(raw_source)

        print("=" * 50)
        print(f" Compilando: {os.path.basename(args.input_file)}")
        print("=" * 50)

        assembly, result = compile_and_run(clean_source, emit_ir=args.emit_ir, emit_assembly=args.assembly)

        # Salva o assembly se solicitado com -S
        if args.assembly:
            asm_file = args.output if args.output and args.output.endswith(".s") else f"{os.path.splitext(args.input_file)[0]}.s"
            with open(asm_file, "w", encoding="utf-8") as f:
                f.write(assembly)
            print(f"✔ Assembly x86-64 salvo em: {asm_file}")

        print("-" * 50)
        print(" [Status]: Compilado com Sucesso!")
        print(f" [Resultado / Retorno de main()]: {result}")
        print("=" * 50)

    except CompilerError as e:
        raw_source = open(args.input_file, "r", encoding="utf-8").read()
        print(format_error_snippet(raw_source, e.line, e.column, e.message), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Erro de compilação: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
