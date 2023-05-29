from src.scalpel.SSA.anf_syntax import parse_ssa_to_anf, parse_anf_from_text, print_anf_with_prov_info
from src.scalpel.SSA.ssa_syntax import PY_to_SSA_AST
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

code_str3 = """
a = 10
b = 5

if b < 10:
    a = a + 2
else:
    a = 2
print(a)
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
    
"""
cc = """
t = "asd"
if (not a) != "live.com" and t != "google.com":
    pass
"""
c3 = """
print("asdf")
for i in a:
    print(1)
for i in [0, 1, 2]:
    print(1)
for i in [0, 1, 2]:
    print(1)
"""

xy="""
List comprehension

s = [x for x in range(1, 5) if True == True]
 |
s = []
for x in range(1, 5):
    if True == True:
        s.append(x)
"""

testc = """
a = a[len([2,3,4,4])]
a = [1,2,3]
b = {1,2,3}
c = {'A': 1, 'B': 2}

x = a[1]
x = b[:2]
x = c['A']
"""

tuple_test = """
a = 1
b = 2
a, b = b, a
"""
for_test = """
for i in range(5):
    print(i)
print("a")
"""
if_test = """
a = 1
if a == 1:
    a = 2
else:
    a = 3
print(a)
"""

global_renaming_test = """
def aaa():
    a = 1
    print(a)
a = 2
aaa()
"""
def toSSA_and_print():
    mnode = MNode("local")
    mnode.source = code_str
    mnode.gen_ast()
    cfg = mnode.gen_cfg()
    m_ssa = SSA()

    ssa_ast = PY_to_SSA_AST(for_test)
    ssa_ast.enable_print_ascii()
    print()
    print(ssa_ast.print(0))

    anf_ast = parse_ssa_to_anf(ssa_ast)
    anf_ast.enable_print_ascii()
    print()
    print(print_anf_with_prov_info(anf_ast))

    with open('output/ssa_parsed.txt', 'w') as f:
        f.write(ssa_ast.print(0))

    with open('output/anf_parsed.txt', 'w') as f:
        f.write(print_anf_with_prov_info(anf_ast))

    # TODO: ASCII and LATEX format prints
    parsed = parse_anf_from_text(print_anf_with_prov_info(anf_ast))
    print('parsed:')
    print(parsed.print(0))
    #cfg = CFGBuilder().build_from_file('example.py', './cfg_example.py')
    #cfg.build_visual('./output/exampleCFG', 'pdf')


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



