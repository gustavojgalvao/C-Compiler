"""
Gerador de Código Assembly x86-64 (Sintaxe AT&T).
"""
from typing import Dict, List
from src.ir.ir_nodes import (
    IRProgram, IRFunction, IRConst, IRCopy, IRBinary,
    IRUnary, IRJump, IRJumpIfZero, IRReturn, IRCall, IRLabel,
    IRAddressOf, IRLoad, IRStore
)
from src.codegen.abi import SystemV_ABI
from src.codegen.registers import EAX, RAX, R10, R10D, R11, R11D, RBP, RSP

class X86CodeGenerator:
    """Emite código Assembly x86-64."""

    def __init__(self):
        self.output_lines: List[str] = []
        self.stack_offsets: Dict[str, int] = {}
        self.current_stack_offset = 0

    def _emit(self, line: str) -> None:
        self.output_lines.append(line)

    def _get_loc(self, name: str) -> str:
        if name not in self.stack_offsets:
            self.current_stack_offset += 8
            self.stack_offsets[name] = self.current_stack_offset
        offset = self.stack_offsets[name]
        return f"-{offset}({RBP})"

    def generate(self, program: IRProgram) -> str:
        self.output_lines = []
        self._emit(".text")

        for func in program.functions:
            self._generate_function(func)

        return "\n".join(self.output_lines) + "\n"

    def _generate_function(self, func: IRFunction) -> None:
        self.stack_offsets = {}
        self.current_stack_offset = 0

        self._emit(f".globl {func.name}")
        self._emit(f"{func.name}:")

        # Prólogo
        self._emit(f"    pushq {RBP}")
        self._emit(f"    movq {RSP}, {RBP}")

        for i, param in enumerate(func.params):
            if i < len(SystemV_ABI.ARG_REGISTERS_32):
                reg = SystemV_ABI.ARG_REGISTERS_32[i]
                loc = self._get_loc(param)
                self._emit(f"    movl {reg}, {loc}")

        self._emit("    subq $128, %rsp")

        for instr in func.instructions:
            self._generate_instruction(instr)

        # Epílogo
        self._emit("    leave")
        self._emit("    ret")

    def _generate_instruction(self, instr) -> None:
        if isinstance(instr, IRLabel):
            self._emit(f"{instr.name}:")
            return

        if isinstance(instr, IRConst):
            loc = self._get_loc(instr.dst)
            self._emit(f"    movl ${instr.value}, {loc}")
            return

        if isinstance(instr, IRCopy):
            src_loc = self._get_loc(instr.src)
            dst_loc = self._get_loc(instr.dst)
            self._emit(f"    movq {src_loc}, {R10}")
            self._emit(f"    movq {R10}, {dst_loc}")
            return

        if isinstance(instr, IRAddressOf):
            src_loc = self._get_loc(instr.src)
            dst_loc = self._get_loc(instr.dst)
            self._emit(f"    leaq {src_loc}, {R10}")
            self._emit(f"    movq {R10}, {dst_loc}")
            return

        if isinstance(instr, IRLoad):
            ptr_loc = self._get_loc(instr.ptr)
            dst_loc = self._get_loc(instr.dst)
            self._emit(f"    movq {ptr_loc}, {R10}")
            self._emit(f"    movl ({R10}), {R11D}")
            self._emit(f"    movl {R11D}, {dst_loc}")
            return

        if isinstance(instr, IRStore):
            ptr_loc = self._get_loc(instr.ptr)
            src_loc = self._get_loc(instr.src)
            self._emit(f"    movq {ptr_loc}, {R10}")
            self._emit(f"    movl {src_loc}, {R11D}")
            self._emit(f"    movl {R11D}, ({R10})")
            return

        if isinstance(instr, IRBinary):
            left_loc = self._get_loc(instr.left)
            right_loc = self._get_loc(instr.right)
            dst_loc = self._get_loc(instr.dst)

            self._emit(f"    movl {left_loc}, {R10D}")
            self._emit(f"    movl {right_loc}, {R11D}")

            if instr.op == "+":
                self._emit(f"    addl {R11D}, {R10D}")
                self._emit(f"    movl {R10D}, {dst_loc}")
            elif instr.op == "-":
                self._emit(f"    subl {R11D}, {R10D}")
                self._emit(f"    movl {R10D}, {dst_loc}")
            elif instr.op == "*":
                self._emit(f"    imull {R11D}, {R10D}")
                self._emit(f"    movl {R10D}, {dst_loc}")
            elif instr.op == "/":
                self._emit(f"    movl {left_loc}, {EAX}")
                self._emit("    cdq")
                self._emit(f"    idivl {right_loc}")
                self._emit(f"    movl {EAX}, {dst_loc}")
            elif instr.op in ("==", "!=", "<", "<=", ">", ">="):
                self._emit(f"    cmpl {R11D}, {R10D}")
                set_instr = {
                    "==": "sete", "!=": "setne", "<": "setl",
                    "<=": "setle", ">": "setg", ">=": "setge"
                }[instr.op]
                self._emit(f"    {set_instr} %al")
                self._emit(f"    movzbl %al, {EAX}")
                self._emit(f"    movl {EAX}, {dst_loc}")
            return

        if isinstance(instr, IRUnary):
            src_loc = self._get_loc(instr.src)
            dst_loc = self._get_loc(instr.dst)
            self._emit(f"    movl {src_loc}, {R10D}")
            if instr.op == "-":
                self._emit(f"    negl {R10D}")
            elif instr.op == "~":
                self._emit(f"    notl {R10D}")
            elif instr.op == "!":
                self._emit(f"    cmpl $0, {R10D}")
                self._emit("    sete %al")
                self._emit(f"    movzbl %al, {R10D}")
            self._emit(f"    movl {R10D}, {dst_loc}")
            return

        if isinstance(instr, IRJump):
            self._emit(f"    jmp {instr.target}")
            return

        if isinstance(instr, IRJumpIfZero):
            cond_loc = self._get_loc(instr.condition)
            self._emit(f"    cmpl $0, {cond_loc}")
            self._emit(f"    je {instr.target}")
            return

        if isinstance(instr, IRCall):
            for i, arg in enumerate(instr.args):
                if i < len(SystemV_ABI.ARG_REGISTERS_32):
                    reg = SystemV_ABI.ARG_REGISTERS_32[i]
                    loc = self._get_loc(arg)
                    self._emit(f"    movl {loc}, {reg}")
            self._emit(f"    call {instr.func_name}")
            if instr.dst:
                dst_loc = self._get_loc(instr.dst)
                self._emit(f"    movl {EAX}, {dst_loc}")
            return

        if isinstance(instr, IRReturn):
            if instr.value:
                loc = self._get_loc(instr.value)
                self._emit(f"    movl {loc}, {EAX}")
            self._emit("    leave")
            self._emit("    ret")
            return
