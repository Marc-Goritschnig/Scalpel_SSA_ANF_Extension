from src.scalpel.SSA.anf_syntax import parse_ssa_to_anf
from src.scalpel.SSA.ssa_syntax import SSACode, PY_to_SSA_AST
from src.scalpel.core.mnode import MNode
from src.scalpel.SSA.const import SSA
from staticfg import CFGBuilder
import os

graphviz_path = 'C:/Program Files/Graphviz/bin'
os.environ["PATH"] += os.pathsep + graphviz_path

code_str = """
b = 10
a = 1
b=1 + b

if b>110:
    a = a+b
    b = 2*a
else:
    a = 10

print(a)
print(b)

"""


code_str2 = """
a = [1,2,3,4,5]
i = 0
while i < len(a):
    print(a[i])

"""

cc = """
def fib():
    a = 0
    b = 1
    while True:
        yield a
        a, b = b, a + b
fib()
"""

"""
List comprehension

s = [x for x in range(1, 5) if True == True]
 |
s = []
for x in range(1, 5):
    if True == True:
        s.append(x)
"""


def toSSA_and_print():
    mnode = MNode("local")
    mnode.source = code_str
    mnode.gen_ast()
    cfg = mnode.gen_cfg()
    m_ssa = SSA()


    ssa_ast = PY_to_SSA_AST(code_str)
    print()
    print(ssa_ast.print())

    anf_ast = parse_ssa_to_anf(ssa_ast)
    print()
    print(anf_ast.print(0))


    cfg = CFGBuilder().build_from_file('example.py', './cfg_example.py')
    cfg.build_visual('./output/exampleCFG', 'pdf')


if __name__ == '__main__':
    # main()
    toSSA_and_print()