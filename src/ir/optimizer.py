"""
Otimizador de Código Intermediário (Middle-End Optimizer).
"""
from src.ir.ir_nodes import IRProgram, IRFunction, IRConst, IRBinary

class IROptimizer:
    """Aplica passadas de otimização sobre a representação intermediária."""

    def optimize(self, program: IRProgram) -> IRProgram:
        optimized_functions = []
        for func in program.functions:
            optimized_functions.append(self._optimize_function(func))
        return IRProgram(functions=optimized_functions)

    def _optimize_function(self, func: IRFunction) -> IRFunction:
        instructions = list(func.instructions)
        instructions = self._constant_folding(instructions)
        return IRFunction(name=func.name, params=func.params, instructions=instructions)

    def _constant_folding(self, instructions: list) -> list:
        const_map = {}
        new_instructions = []

        for instr in instructions:
            if isinstance(instr, IRConst):
                const_map[instr.dst] = instr.value
                new_instructions.append(instr)
            elif isinstance(instr, IRBinary) and instr.left in const_map and instr.right in const_map:
                v1 = const_map[instr.left]
                v2 = const_map[instr.right]
                folded_val = None

                if instr.op == "+":
                    folded_val = v1 + v2
                elif instr.op == "-":
                    folded_val = v1 - v2
                elif instr.op == "*":
                    folded_val = v1 * v2
                elif instr.op == "/" and v2 != 0:
                    folded_val = v1 // v2

                if folded_val is not None:
                    const_map[instr.dst] = folded_val
                    new_instructions.append(IRConst(dst=instr.dst, value=folded_val))
                else:
                    new_instructions.append(instr)
            else:
                new_instructions.append(instr)

        return new_instructions
