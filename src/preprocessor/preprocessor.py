"""
Módulo de pré-processamento de código-fonte C.
"""
import subprocess
import shutil

class Preprocessor:
    """Responsável por executar a etapa preliminar de pré-processamento."""

    @staticmethod
    def run_system_cpp(filepath: str) -> str:
        """Executa gcc -E ou clang -E se disponível."""
        compiler_cmd = shutil.which("gcc") or shutil.which("clang")
        if compiler_cmd:
            result = subprocess.run(
                [compiler_cmd, "-E", "-P", filepath],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def strip_comments(source_code: str) -> str:
        """Remove comentários simples de linha (//) e de bloco (/* ... */)."""
        result = []
        i = 0
        n = len(source_code)
        while i < n:
            if source_code[i:i+2] == "//":
                while i < n and source_code[i] != "\n":
                    i += 1
            elif source_code[i:i+2] == "/*":
                i += 2
                while i < n and source_code[i:i+2] != "*/":
                    i += 1
                i += 2
            else:
                result.append(source_code[i])
                i += 1
        return "".join(result)
