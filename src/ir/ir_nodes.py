"""
Instruções da Representação Intermediária (Three-Address Code - TAC).
"""
from dataclasses import dataclass
from typing import Optional, List

class IRInstruction:
    pass

@dataclass
class IRLabel(IRInstruction):
    name: str

    def __repr__(self) -> str:
        return f"{self.name}:"

@dataclass
class IRConst(IRInstruction):
    dst: str
    value: int

    def __repr__(self) -> str:
        return f"  {self.dst} = {self.value}"

@dataclass
class IRCopy(IRInstruction):
    dst: str
    src: str

    def __repr__(self) -> str:
        return f"  {self.dst} = {self.src}"

@dataclass
class IRBinary(IRInstruction):
    op: str
    dst: str
    left: str
    right: str

    def __repr__(self) -> str:
        return f"  {self.dst} = {self.left} {self.op} {self.right}"

@dataclass
class IRUnary(IRInstruction):
    op: str
    dst: str
    src: str

    def __repr__(self) -> str:
        return f"  {self.dst} = {self.op}{self.src}"

@dataclass
class IRAddressOf(IRInstruction):
    dst: str
    src: str

    def __repr__(self) -> str:
        return f"  {self.dst} = &{self.src}"

@dataclass
class IRLoad(IRInstruction):
    dst: str
    ptr: str

    def __repr__(self) -> str:
        return f"  {self.dst} = *{self.ptr}"

@dataclass
class IRStore(IRInstruction):
    ptr: str
    src: str

    def __repr__(self) -> str:
        return f"  *{self.ptr} = {self.src}"

@dataclass
class IRJump(IRInstruction):
    target: str

    def __repr__(self) -> str:
        return f"  jmp {self.target}"

@dataclass
class IRJumpIfZero(IRInstruction):
    condition: str
    target: str

    def __repr__(self) -> str:
        return f"  jz {self.condition}, {self.target}"

@dataclass
class IRReturn(IRInstruction):
    value: Optional[str] = None

    def __repr__(self) -> str:
        return f"  ret {self.value if self.value else ''}"

@dataclass
class IRCall(IRInstruction):
    dst: Optional[str]
    func_name: str
    args: List[str]

    def __repr__(self) -> str:
        args_str = ", ".join(self.args)
        if self.dst:
            return f"  {self.dst} = call {self.func_name}({args_str})"
        return f"  call {self.func_name}({args_str})"

@dataclass
class IRFunction:
    name: str
    params: List[str]
    instructions: List[IRInstruction]

    def __repr__(self) -> str:
        lines = [f"func {self.name}({', '.join(self.params)}):"]
        for instr in self.instructions:
            lines.append(str(instr))
        return "\n".join(lines)

@dataclass
class IRProgram:
    functions: List[IRFunction]
