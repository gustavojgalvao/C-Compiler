.text
.globl main
main:
    pushq %rbp
    movq %rsp, %rbp
    subq $128, %rsp
    movl $0, -4(%rbp)
    movl -4(%rbp), %r10d
    movl %r10d, -8(%rbp)
    movl $0, -12(%rbp)
    movl -12(%rbp), %r10d
    movl %r10d, -16(%rbp)
loop_start_1:
    movl $10, -20(%rbp)
    movl -8(%rbp), %r10d
    movl -20(%rbp), %r11d
    cmpl %r11d, %r10d
    setl %al
    movzbl %al, %eax
    movl %eax, -24(%rbp)
    cmpl $0, -24(%rbp)
    je loop_end_2
    movl -16(%rbp), %r10d
    movl -8(%rbp), %r11d
    addl %r11d, %r10d
    movl %r10d, -28(%rbp)
    movl -28(%rbp), %r10d
    movl %r10d, -16(%rbp)
    movl $1, -32(%rbp)
    movl -8(%rbp), %r10d
    movl -32(%rbp), %r11d
    addl %r11d, %r10d
    movl %r10d, -36(%rbp)
    movl -36(%rbp), %r10d
    movl %r10d, -8(%rbp)
    jmp loop_start_1
loop_end_2:
    movl $45, -40(%rbp)
    movl -16(%rbp), %r10d
    movl -40(%rbp), %r11d
    cmpl %r11d, %r10d
    sete %al
    movzbl %al, %eax
    movl %eax, -44(%rbp)
    cmpl $0, -44(%rbp)
    je else_3
    movl $1, -48(%rbp)
    movl -48(%rbp), %eax
    leave
    ret
    jmp endif_4
else_3:
    movl $0, -52(%rbp)
    movl -52(%rbp), %eax
    leave
    ret
endif_4:
    movl $0, -56(%rbp)
    movl -56(%rbp), %eax
    leave
    ret
    leave
    ret
