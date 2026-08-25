"""
Executor / Máquina Virtual para a Representação Intermediária (IR).
"""
from typing import Dict, Any, List
from src.ir.ir_nodes import (
    IRProgram, IRFunction, IRConst, IRCopy, IRBinary,
    IRUnary, IRJump, IRJumpIfZero, IRReturn, IRCall, IRLabel,
    IRAddressOf, IRLoad, IRStore
)

class IRExecutor:
    """Máquina virtual baseada em frames e memória heap/stack para executar a IR."""

    def __init__(self, program: IRProgram):
        self.program = program
        self.functions: Dict[str, IRFunction] = {f.name: f for f in program.functions}
        self.heap: Dict[int, int] = {}
        self.next_address = 1000

    def run(self, entry_point: str = "main") -> int:
        if entry_point not in self.functions:
            raise RuntimeError(f"Ponto de entrada '{entry_point}' não encontrado.")

        return self._execute_function(self.functions[entry_point], [])

    def _execute_function(self, func: IRFunction, arg_values: List[int]) -> int:
        memory: Dict[str, Any] = {}
        var_addresses: Dict[str, int] = {}
        labels: Dict[str, int] = {}

        for idx, instr in enumerate(func.instructions):
            if isinstance(instr, IRLabel):
                labels[instr.name] = idx

        for param_name, val in zip(func.params, arg_values):
            memory[param_name] = val
            addr = self.next_address
            self.next_address += 4
            var_addresses[param_name] = addr
            self.heap[addr] = val

        pc = 0
        instructions = func.instructions
        n = len(instructions)

        while pc < n:
            instr = instructions[pc]

            if isinstance(instr, IRLabel):
                pc += 1
                continue

            elif isinstance(instr, IRConst):
                memory[instr.dst] = int(instr.value)
                pc += 1

            elif isinstance(instr, IRCopy):
                val = memory.get(instr.src, 0)
                memory[instr.dst] = val
                if instr.dst not in var_addresses:
                    addr = self.next_address
                    self.next_address += 4
                    var_addresses[instr.dst] = addr
                self.heap[var_addresses[instr.dst]] = val
                pc += 1

            elif isinstance(instr, IRAddressOf):
                if instr.src not in var_addresses:
                    addr = self.next_address
                    self.next_address += 4
                    var_addresses[instr.src] = addr
                    self.heap[addr] = memory.get(instr.src, 0)
                memory[instr.dst] = var_addresses[instr.src]
                pc += 1

            elif isinstance(instr, IRLoad):
                ptr_addr = memory.get(instr.ptr, 0)
                memory[instr.dst] = self.heap.get(ptr_addr, 0)
                pc += 1

            elif isinstance(instr, IRStore):
                ptr_addr = memory.get(instr.ptr, 0)
                val = memory.get(instr.src, 0)
                self.heap[ptr_addr] = val
                # Se esse endereço corresponder a uma variável local, atualiza seu valor local
                for vname, vaddr in var_addresses.items():
                    if vaddr == ptr_addr:
                        memory[vname] = val
                pc += 1

            elif isinstance(instr, IRBinary):
                v1 = memory.get(instr.left, 0)
                v2 = memory.get(instr.right, 0)
                res = 0

                if instr.op == "+":
                    res = v1 + v2
                elif instr.op == "-":
                    res = v1 - v2
                elif instr.op == "*":
                    res = v1 * v2
                elif instr.op == "/":
                    res = int(v1 / v2) if v2 != 0 else 0
                elif instr.op == "%":
                    res = v1 % v2 if v2 != 0 else 0
                elif instr.op == "==":
                    res = 1 if v1 == v2 else 0
                elif instr.op == "!=":
                    res = 1 if v1 != v2 else 0
                elif instr.op == "<":
                    res = 1 if v1 < v2 else 0
                elif instr.op == "<=":
                    res = 1 if v1 <= v2 else 0
                elif instr.op == ">":
                    res = 1 if v1 > v2 else 0
                elif instr.op == ">=":
                    res = 1 if v1 >= v2 else 0
                elif instr.op == "&&":
                    res = 1 if (v1 != 0 and v2 != 0) else 0
                elif instr.op == "||":
                    res = 1 if (v1 != 0 or v2 != 0) else 0

                memory[instr.dst] = res
                pc += 1

            elif isinstance(instr, IRUnary):
                v = memory.get(instr.src, 0)
                if instr.op == "-":
                    memory[instr.dst] = -v
                elif instr.op == "~":
                    memory[instr.dst] = ~v
                elif instr.op == "!":
                    memory[instr.dst] = 1 if v == 0 else 0
                pc += 1

            elif isinstance(instr, IRJump):
                pc = labels[instr.target]

            elif isinstance(instr, IRJumpIfZero):
                cond = memory.get(instr.condition, 0)
                if cond == 0:
                    pc = labels[instr.target]
                else:
                    pc += 1

            elif isinstance(instr, IRCall):
                callee_func = self.functions.get(instr.func_name)
                if not callee_func:
                    raise RuntimeError(f"Função '{instr.func_name}' não encontrada.")
                call_args = [memory.get(arg, 0) for arg in instr.args]
                ret_val = self._execute_function(callee_func, call_args)
                if instr.dst:
                    memory[instr.dst] = ret_val
                pc += 1

            elif isinstance(instr, IRReturn):
                if instr.value is not None:
                    return memory.get(instr.value, 0)
                return 0

            else:
                pc += 1

        return 0
