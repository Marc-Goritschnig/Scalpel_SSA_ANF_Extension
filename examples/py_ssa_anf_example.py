from src.scalpel.SSA.anf_syntax import parse_ssa_to_anf
from src.scalpel.SSA.ssa_syntax import SSACode, PY_to_SSA_AST
from src.scalpel.core.mnode import MNode
from src.scalpel.SSA.const import SSA
from staticfg import CFGBuilder
import os

graphviz_path = 'C:/Program Files/Graphviz/bin'
os.environ["PATH"] += os.pathsep + graphviz_path

code_str = """
def aaa():
    print('123')
    
b = 10
aaa()

"""


code_str2 = """
a = [1,2,3,4,5]
i = 0
while i < len(a):
    print(a[i])

"""
ccc="""
def IsEasyChairQuery(input: str) -> bool:
    # (1) check that input contains "/" followed by anything not
    # containing "/" and containing "EasyChair"
    lastSlash = input.rindex('/')
    if lastSlash < 0:
        return False
    rest = input[lastSlash + 1:]
    if "EasyChair" not in rest:
        return False
    # (2) Check that input starts with "http://"
    if not input.startswith("http://"):
        return False
    # (3) Take the string between "http://" and the last "/".
    # if it starts with "www." strip the "www." off
    t = input[len("http://"): lastSlash]
    if t.startswith("www."):
        t = t[len("www.")]
    # (4) Check that after stripping we have either "live.com"
    # or "google.com"
    if t != "live.com" and t != "google.com":
        return False
    # s survived all checks
    return True
IsEasyChairQuery('test')

a = 1
print(a)
print(a)
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


def IsEasyChairQuery(input: str) -> bool:
    # (1) check that input contains "/" followed by anything not
    # containing "/" and containing "EasyChair"
    lastSlash = input.rindex('/')
    if lastSlash < 0:
        return False
    rest = input[lastSlash + 1:]
    if "EasyChair" not in rest:
        return False
    # (2) Check that input starts with "http://"
    if not input.startswith("http://"):
        return False
    # (3) Take the string between "http://" and the last "/".
    # if it starts with "www." strip the "www." off
    t = input[len("http://"): lastSlash]
    if t.startswith("www."):
        t = t[len("www.")]
    # (4) Check that after stripping we have either "live.com"
    # or "google.com"
    if t != "live.com" and t != "google.com":
        return False
    # s survived all checks
    return True



if __name__ == '__main__':
    # main()
    toSSA_and_print()
    #print(IsEasyChairQuery("http://live.com/EasyChair"))
    #print(IsEasyChairQuery("http://www.live.com"))
    #print(IsEasyChairQuery("http://www.live.com/sedrgerg/sdfsefes/EasyChair"))
    #print(IsEasyChairQuery("https://www.live.com/sedrgerg/sdfsefes/EasyChair"))
    #print(IsEasyChairQuery("http://www.livecom/sedrgerg/sdfsefes/EasyChair"))

