import os
import sys
import re
import argparse

import ast as ast2
import scalpel.ast_comments as ast
from scalpel.config import NEW_COMMENT_MARKER

from scalpel.functions import trim_double_spaces

print('Absolute path: ', os.path.abspath(__file__))
content_root = re.split(r'(\\|/)*scalpel', os.path.abspath(__file__))[0]
print(content_root)
if content_root not in sys.path:
    sys.path.append(content_root)

from scalpel.SSA.anf_syntax import parse_ssa_to_anf, parse_anf_from_text, print_anf_with_prov_info, print_anf_code_to_python
from scalpel.SSA.ssa_syntax import PY_to_SSA_AST, parse_ssa_to_python

output_folder = 'output'

ssa_file = 'ssa_parsed.txt'
anf_file = 'anf_parsed.txt'
anf_with_prov_file = 'anf_parsed_with_prov_info.txt'
compare_file = 'code_comparison.txt'

default_code_to_transform = ""  # Change this value to transform another code

python_code_path = None
debug_mode = True
print_CFG_graph = False
parse_back = False
only_parse_back = False
output_syntax = 0
no_output_files = False
no_pos = False
print_prov_info = False





def transform():
    # Print cfg into file
    #if print_CFG_graph:
    #    cfg = CFGBuilder().build_from_file('example.py', './cfg_example.py')
    #    cfg.build_visual('./output/exampleCFG', 'pdf')

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

    if only_parse_back:
        pass
    else:
        # Reformat the code
        x = ast.parse(py_code)
        py_code = ast.unparse(ast.parse(py_code))
        y = ast2.parse(py_code)
        # Create a SSA AST from python code
        ssa_ast = PY_to_SSA_AST(py_code, debug_mode)
        if output_syntax == 0:
            ssa_ast.enable_print_ascii()

        if debug_mode:
            print("Transformed SSA tree printed:")
            print(trim_double_spaces(ssa_ast.print(0), NEW_COMMENT_MARKER))
            print('\n\n\n')

        # Create an ANF AST from SSA AST
        anf_ast = parse_ssa_to_anf(ssa_ast, debug_mode, no_pos)
        if output_syntax == 0:
            anf_ast.enable_print_ascii()

        anf_w_prov = print_anf_with_prov_info(anf_ast)


        if debug_mode:
            print("Transformed AST tree printed:")

        if not parse_back:
            if print_prov_info:
                print(anf_w_prov)
            else:
                print(trim_double_spaces(anf_ast.print(0), NEW_COMMENT_MARKER))

        if debug_mode:
            print('\n\n\n')
            print("Transformed AST tree with provenance printed:")
            print(anf_w_prov)
            print('\n\n\n')

        # Print parsed SSA and ANF code to output files
        if not no_output_files:
            with open(output_folder + '/' + ssa_file, 'w', encoding="utf-8") as f:
                f.write(ssa_ast.print(0))
            with open(output_folder + '/' + anf_file, 'w', encoding="utf-8") as f:
                f.write(anf_ast.print(0))
            with open(output_folder + '/' + anf_with_prov_file, 'w', encoding="utf-8") as f:
                f.write(anf_w_prov)
            with open(output_folder + '/' + compare_file, 'w', encoding="utf-8") as f:
                f.write(ssa_ast.code + '\n##########\n' + anf_w_prov)

    if parse_back or only_parse_back:

        if only_parse_back:
            parsed = parse_anf_from_text(py_code)
        else:
            #with open(output_folder + '/' + anf_with_prov_file, 'r', encoding="utf-8") as f:
            #    # Parsing the anf code back to internal representation of anf
            #    parsed = parse_anf_from_text(f.read())
#
#                if debug_mode:
#                    print('Parsed anf tree printed:')
#                    print(trim_double_spaces(parsed.print(0), NEW_COMMENT_MARKER))
#                    print('\n\n\n')
            parsed = parse_anf_from_text(anf_w_prov)


        # Parsing the anf code back to Python
        anf_to_python = print_anf_code_to_python(parsed)
        # if debug_mode:
            # print('Parsed Python code from ANF to Python test printed:')
            # print(ast.unparse(ast.parse(anf_to_python)))
            # print('\n\n\n')
            # print('Parsed Python code from ANF to SSA test printed:')
            # print(parse_anf_to_ssa(parsed).print())
            # print(parse_ssa_to_python(parse_anf_to_ssa(parsed)))
            # print('\n\n\n')
            # print('\n\n\n')

        # print(anf_to_python)
        x = ast.parse(anf_to_python)
        # print(ast.unparse(x))
        print(add_missing_blank_lines(ast.unparse(x)).rstrip())

    # Transform the ast tree back to Python
    # TODO: Implementation of back transformation

    # Other TODOs test
    # TODO: SSA - ?? NamedExpr, SetComp, DictComp, GeneratorExp
    # TODO: LATEX format prints

def test_link(path: str, back: bool):
    global python_code_path, debug_mode, parse_back, no_pos
    python_code_path = path
    debug_mode = False
    parse_back = back
    no_pos = True
    transform()


def add_missing_blank_lines(input_code):
    # Parse the input code into an Abstract Syntax Tree (AST)
    tree = ast.parse(input_code)

    # Helper function to add two blank lines after the end of a function block
    def add_blank_lines(node, two_blank_lines: bool):
        lines = input_code.split('\n')
        end_lineno = node.end_lineno  # Line number of the last line of the function block
        added = False

        # Check if there are no blank lines after the function block
        if end_lineno < len(lines) and lines[end_lineno].strip() != '':
            lines.insert(end_lineno, '')  # Add a blank line after the end of the function block
            if two_blank_lines:
                lines.insert(end_lineno, '')  # Add a blank line after the end of the function block
            added = True
        elif two_blank_lines and end_lineno < len(lines) - 1 and lines[end_lineno + 1].strip() != '':
            lines.insert(end_lineno, '')  # Add a blank line after the end of the function block
            added = True

        return '\n'.join(lines), added

    new_code = input_code

    # recursively call the function until no more lines are added
    added = False
    for node in list(ast.iter_child_nodes(tree)):
        added = False
        if isinstance(node, ast.FunctionDef):
            # top-level function definition
            new_code, added = add_blank_lines(node, True)
        if added:
            break
    if not added:
        for node in ast.walk(tree):
            added = False
            if isinstance(node, ast.FunctionDef):
                # top-level function definition
                new_code, added = add_blank_lines(node, False)
            if added:
                break
    if added:
        return add_missing_blank_lines(new_code)
    return new_code


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='This is the discription')
    parser.add_argument('-i', '--input_path', required=True, default=None, type=str, help="The filepath for the python code to be transformed")
    parser.add_argument('-o', '--output_path', default='output', type=str, help="Under this path all saved files will be placed, if not given the files will be saved in a locally created output folder")
    # parser.add_argument("--ssa_out_name", '--ssa', default='ssa_parsed.txt', type=str, help="The filename for the generated SSA code")
    # parser.add_argument("--anf_out_name", '--anf', default='anf_parsed.txt', type=str, help="The filename for the generated ANF code")
    # parser.add_argument("--anf_with_prov_out_name", '-anf_plus', default='anf_parsed_with_prov_info.txt', type=str, help="The filename for the generated ANF code including provenance information")
    parser.add_argument('-d', '--debug_mode', action='store_true', help="Shows more information and logs when True")
    # parser.add_argument('-c', '--save_cfg', action='store_true', help="Saves the generated CFG in DOT format")
    parser.add_argument('-b', '--parse_back', action='store_true', help="When given the transformation back will be done and the result will be printed")
    parser.add_argument('-p', '--only_parse_back', action='store_true', help="When given the input file will be interpreted as ANF code with provenance information and parsed back into Python code")
    parser.add_argument('-s', '--output_syntax', default=0, type=int, help="The format in which the output is printed (0...ascii, 1...code)")
    parser.add_argument('-n', '--no_output_files', action='store_true', help="When given the library will save no files and only print onto the console")
    parser.add_argument('--print_prov_info', action='store_true', help="When given the library will print the anf together with its provenance info to the console")
    parser.add_argument('--no_pos', action='store_true', help="When given the library will not track positional info of variables etc.")

    args = parser.parse_args()

    output_folder = args.output_path
    # ssa_file = args.ssa_out_name
    # anf_file = args.anf_out_name
    # anf_with_prov_file = args.anf_with_prov_out_name
    no_output_files = args.no_output_files
    python_code_path = args.input_path
    debug_mode = str2bool(args.debug_mode)
    #print_CFG_graph = str2bool(args.save_cfg)
    parse_back = str2bool(args.parse_back)
    only_parse_back = str2bool(args.only_parse_back)
    output_syntax = args.output_syntax
    no_pos = args.no_pos
    print_prov_info = args.print_prov_info

    #if print_CFG_graph:
    #    from staticfg import CFGBuilder
    #    graphviz_path = 'C:/Program Files/Graphviz/bin'
    #    os.environ["PATH"] += os.pathsep + graphviz_path

    transform()

# TODO Talk about:
# TODO ast.Attrobute - class function calls like obj.getMap() => cl_fun_[#args](obj, getMap, args...)

# Wrong ast node types given for List, Tuple, Dict, Set replace all with strings to name comparisons
# Dict target is subscript preprocessing
# mark attribute functions and map them