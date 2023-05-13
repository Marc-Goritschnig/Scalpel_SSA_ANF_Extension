import ast
import codegen
from src.scalpel.SSA.anf_syntax import parse_ssa_to_anf

from src.scalpel.SSA.ssa_syntax import SSACode, PY_to_SSA_AST

from src.scalpel.cfg import CFG

from src.scalpel.core.mnode import MNode
from src.scalpel.SSA.const import SSA

code_str = """
b = 10
a = 1
b=1 + b
v = b
c = 3
#z = {'a':1, 'b': 2}
#zz = z['a']
if b>110:
    a = a+b+c
    b = 2*a
else:
    a = 10
    a = 12


if b>110:
    a = a+b+c
    b = 2*a
else:
    a = 10
    a = 12

print(a)
print(b)

def aaa(b):
    b = b + 1
    print(b)
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


def recursive_parse_cfg_trees_to_ssa(cfg: CFG, m_ssa: SSA):
    print(cfg.entryblock)
    # Final blocks of the CFG.
    print(cfg.finalblocks)
    # Sub-CFGs for functions defined inside the current CFG.
    print(cfg.functioncfgs)
    print(cfg.class_cfgs)
    print(cfg.name)
    blocks = cfg.get_all_blocks

    ssa_results_stored, ssa_results, const_dict = m_ssa.compute_SSA2(cfg)
    for block_id, stmt_res in ssa_results.items():
        print("These are the results for block {}".format(block_id))
        print(stmt_res)
    for name, value in const_dict.items():
        print(name, codegen.to_source(value))

    print("ssa_results")
    print(ssa_results)
    print("ssa_results_stored")
    print(ssa_results_stored)
    print("")

    for key, sub_cfg in cfg.functioncfgs.items():
        print("New function")
        print(key)
        print(sub_cfg.entryblock.statements)
        recursive_parse_cfg_trees_to_ssa(sub_cfg, m_ssa)

    # for key, sub_cfg in cfg.finalblocks:
    #    print("New final block")
    #    print(key)
    #    recursive_parse_cfg_trees_to_ssa(sub_cfg, m_ssa)

    # for key, sub_cfg in cfg.class_cfgs.items():
    #    print("New class")
    #    print(key)
    #    recursive_parse_cfg_trees_to_ssa(sub_cfg, m_ssa)
    SSACode(cfg)


def toSSA_and_print():
    mnode = MNode("local")
    mnode.source = code_str
    mnode.gen_ast()
    cfg = mnode.gen_cfg()
    m_ssa = SSA()

    recursive_parse_cfg_trees_to_ssa(cfg, m_ssa)

    ssa_ast = PY_to_SSA_AST(code_str)
    print()
    print(ssa_ast.print())

    anf_ast = parse_ssa_to_anf(ssa_ast)
    print()
    print(anf_ast.print(0))


def main():
    mnode = MNode("local")
    mnode.source = code_str
    mnode.gen_ast()
    cfg = mnode.gen_cfg()
    m_ssa = SSA()
    ssa_results, const_dict = m_ssa.compute_SSA2(cfg)
    for block_id, stmt_res in ssa_results.items():
        print("These are the results for block ".format(block_id))
        print(stmt_res)
    for name, value in const_dict.items():
        print(name, value)
    print(ssa_results)


if __name__ == '__main__':
    # main()
    toSSA_and_print()