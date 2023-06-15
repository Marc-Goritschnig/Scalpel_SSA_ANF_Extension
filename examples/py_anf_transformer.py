import os
import sys
import re

print('Absolute path: ', os.path.abspath(__file__))
content_root = re.split(r'(\\|/)*examples(\\|/)*py_anf_transformer', os.path.abspath(__file__))[0]
# content_root = os.path.abspath(__file__).split('\examples\py_anf_transformer.py')[0]
if content_root not in sys.path:
    sys.path.append(content_root)

from src.scalpel.SSA.anf_syntax import parse_ssa_to_anf, parse_anf_from_text, print_anf_with_prov_info, parse_anf_to_ssa
from src.scalpel.SSA.ssa_syntax import PY_to_SSA_AST

# ###########################
# Testing code strings ######
# ###########################

code_str = """
def aaa():
    print('123')

b = 10
aaa()

"""

if_else_test = """
a = 10
b = 5

if b < 10:
    a = a + 2
else:
    a = 2
print(a)
"""

while_test = """
a = [1,2,3,4,5]
i = 0
while i < len(a):
    print(a[i])

"""
easy_chair_test = """
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

xy = """
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

for_3_test = """
for i in range(5):
    print(i)
for i in range(5):
    print(i)
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
    b = 1
    print(a)
def aaa2():
    a = 1
    b = 2
    print(a)
a = 2
aaa()
"""

bool_op_test = """
if (a or b or c or d):
    print("asdf")
"""

lambda_test = """
def ab():
    x = lambda a : a + 10
    print(x(5))
ab()
"""

list_comp_test = """
x = [1,2,3,4,5]
y = [i + y for i in x for y in x]
print(y)
"""
list_comp_test2 = """
x = [1,2,3,4,5]
_buffer_py_0 = []
for i in x:
    for y in x:
        _buffer_py_0.append(i + y)
y = _buffer_py_0
print(y)
"""

fun_in_fun_test = """
def a():
    b = 2
    def a2():
        c = b + 2
        b = 2
        c = b
    a2()
a()
"""

output_folder = 'output'

ssa_file = 'ssa_parsed.txt'
anf_file = 'anf_parsed.txt'
anf_with_prov_file = 'anf_parsed_with_prov_info.txt'

default_code_to_transform = if_else_test  # Change this value to transform another code

python_code_path = None
debug_mode = True
print_CFG_graph = False


def transform():
    # Print cfg into file
    if print_CFG_graph:
        cfg = CFGBuilder().build_from_file('example.py', './cfg_example.py')
        cfg.build_visual('./output/exampleCFG', 'pdf')

    # Check if output folder exists
    if not os.path.exists(output_folder):
        # If it doesn't exist, create it
        os.makedirs(output_folder)

    # Default code to be parsed if no file is given (for quick testing with above created examples)
    py_code = default_code_to_transform

    # Read python code from input file given
    if python_code_path is not None:
        with open(python_code_path, 'r') as file:
            py_code = file.read()

    # Create a SSA AST from python code
    ssa_ast = PY_to_SSA_AST(py_code, debug_mode)
    ssa_ast.enable_print_ascii()
    if debug_mode:
        print("Transformed SSA tree printed:")
        print(ssa_ast.print(0))
        print('\n\n\n')

    # Create an ANF AST from SSA AST
    anf_ast = parse_ssa_to_anf(ssa_ast, debug_mode)
    anf_ast.enable_print_ascii()
    if debug_mode:
        print("Transformed AST tree printed:")
        print(anf_ast.print(0))
        print('\n\n\n')

        print("Transformed AST tree with provenance printed:")
        print(print_anf_with_prov_info(anf_ast))
        print('\n\n\n')

    # Print parsed SSA and ANF code to output files
    with open(output_folder + '/' + ssa_file, 'w') as f:
        f.write(ssa_ast.print(0))
    with open(output_folder + '/' + anf_file, 'w') as f:
        f.write(anf_ast.print(0))
    with open(output_folder + '/' + anf_with_prov_file, 'w') as f:
        f.write(print_anf_with_prov_info(anf_ast))

    # Parsing the anf code back to internal representation of anf
    parsed = parse_anf_from_text(print_anf_with_prov_info(anf_ast))
    if debug_mode:
        print('Parsed anf tree printed:')
        print(parsed.print(0))
        print('\n\n\n')

    # Parsing the anf code back to Python
    anf_to_python = parsed.parse_anf_to_python({})
    if debug_mode:
        print('Parsed Python code from ANF to Python test printed:')
        print(anf_to_python)
        print('\n\n\n')
        print('Parsed Python code from ANF to SSA test printed:')
        print(parse_anf_to_ssa(parsed).print())
        print('\n\n\n')


# Transform the ast tree back to Python
    # TODO: Implementation of back transformation

    # Other TODOs
    # TODO: SSA - ?? NamedExpr, SetComp, DictComp, GeneratorExp
    # TODO: LATEX format prints


if __name__ == '__main__':
    # Check if both arguments are provided
    if len(sys.argv) < 4 and len(sys.argv) > 1:
        print("Usage: python script.py <file_path> <debug_mode> <visualize_cfg>")
        sys.exit(1)

    # Debug active when no arguments given
    if len(sys.argv) == 1:
        print("Usage: python script.py <file_path> <debug_mode> <visualize_cfg>")
        print('Debug mode is active, local code will be transformed\n')
    else:
        # Retrieve the arguments
        python_code_path = sys.argv[1]
        debug_mode = sys.argv[2].lower() == "true"
        print_CFG_graph = sys.argv[3].lower() == "true"

    if print_CFG_graph:
        from staticfg import CFGBuilder
        graphviz_path = 'C:/Program Files/Graphviz/bin'
        os.environ["PATH"] += os.pathsep + graphviz_path

    transform()
