from __future__ import annotations
import ast
import re

from src.scalpel.core.mnode import MNode
from src.scalpel.SSA.const import SSA

debug_mode = True
font = {'assign': '←',
        'phi': 'φ'}


class SSANode:
    def __init__(self):
        pass

    def print(self, lvl):
        return 'not implemented'

    def enable_print_ascii(self):
        global font
        font = {'assign': '<-',
                'phi': 'PHI'}

    def enable_print_code(self):
        global font
        font = {'assign': '←',
                'phi': 'φ'}


class SSA_V(SSANode):
    def __init__(self):
        super().__init__()

    def print(self, lvl):
        return ''

    def print_latex(self, lvl):
        return ''


class SSA_L(SSA_V):
    def __init__(self, label: str):
        super().__init__()
        self.label: str = label

    def print(self, lvl):
        return f"{self.label}"

    def print_latex(self, lvl):
        return ""


class SSA_V_CONST(SSA_V):
    def __init__(self, value: str):
        super().__init__()
        self.value: str = value

    def print(self, lvl):
        return f"{self.value}"

    def print_latex(self, lvl):
        return ""


class SSA_V_VAR(SSA_V):
    def __init__(self, name: str):
        super().__init__()
        self.name: str = name

    def print(self, lvl):
        return f"{self.name}"

    def print_latex(self, lvl):
        return ""


class SSA_V_FUNC_CALL(SSA_V):
    def __init__(self, name: SSA_L | SSA_V, args: [SSA_V]):
        super().__init__()
        self.name: SSA_L | SSA_V = name
        self.args: [SSA_V] = args

    def print(self, lvl):
        return f"{self.name.print(lvl) + print_args(self.args, lvl)}"

    def print_latex(self, lvl):
        return ""


class SSA_E(SSANode):
    def __init__(self):
        super().__init__()

    def print(self, lvl):
        return ""

    def print_latex(self, lvl):
        return ""


class SSA_E_ASS_PHI(SSA_E):
    def __init__(self, var: SSA_V, args: [SSA_V]):
        super().__init__()
        self.var: SSA_V = var
        self.args: [SSA_V] = args

    def print(self, lvl):
        return self.var.print(lvl) + ' ' + font['assign'] + ' ' + font['phi'] + print_args(self.args, lvl)

    def print_latex(self, lvl):
        return ""


class SSA_E_ASS(SSA_E):
    def __init__(self, var: SSA_V, value: SSA_V):
        super().__init__()
        self.var: SSA_V = var
        self.value: SSA_V = value

    def print(self, lvl):
        return f"{self.var.print(lvl)+ ' ' + font['assign'] + ' ' + self.value.print(lvl)}"

    def print_latex(self, lvl):
        return ""


class SSA_E_GOTO(SSA_E):
    def __init__(self, label: SSA_L):
        super().__init__()
        self.label: SSA_L = label

    def print(self, lvl):
        return f"{'goto L' + self.label.print(lvl)}"

    def print_latex(self, lvl):
        return ""


class SSA_E_RET(SSA_E):
    def __init__(self, value: SSA_V | None):
        super().__init__()
        self.value: SSA_V | None = value

    def print(self, lvl):
        if self.value is None:
            return 'ret'
        return f"ret {self.value.print(lvl)}"

    def print_latex(self, lvl):
        return ""


class SSA_E_IF_ELSE(SSA_E):
    def __init__(self, test: SSA_V, term_if: SSA_E, term_else: SSA_E):
        super().__init__()
        self.test: SSA_V = test
        self.term_if: SSA_E = term_if
        self.term_else: SSA_E = term_else

    def print(self, lvl):
        new_line = '\n'
        return f"{'if ' + self.test.print(lvl) + ' then ' + self.term_if.print(lvl) + new_line + get_indentation(lvl) + 'else ' + self.term_else.print(lvl)}"

    def print_latex(self, lvl):
        return ""


class SSA_B(SSANode):
    def __init__(self, label: SSA_L, terms: [SSA_E], first_in_proc: bool):
        super().__init__()
        self.label: SSA_L = label
        self.terms: [SSA_E] = terms
        self.first_in_proc: bool = first_in_proc

    def print(self, lvl):
        new_line = '\n'

        #if self.first_in_proc:
        #    return print_terms(self.terms, lvl)
        return get_indentation(lvl) + f"{'L' + self.label.print(lvl+1) + ': ' + new_line + print_terms(self.terms, lvl+1)}"

    def print_latex(self, lvl):
        return ""


class SSA_P(SSANode):
    def __init__(self, name: SSA_V_VAR, args: [SSA_V], blocks: [SSA_B]):
        super().__init__()
        self.name: SSA_V_VAR = name
        self.args: [SSA_V] = args
        self.blocks: [SSA_B] = blocks

    def print(self, lvl=0):
        # return '\n\n'.join([b.print(0) for b in self.blocks])
        return 'proc ' + self.name.print(0) + print_args(self.args, 0) + '\n{\n' + '\n\n'.join([b.print(1) for b in self.blocks]) + '\n}\n'

    def print_latex(self):
        return ""


class SSA_AST(SSANode):
    def __init__(self, procs: [SSA_P], blocks: [SSA_B]):
        super().__init__()
        self.procs: [SSA_P] = procs
        self.blocks: [SSA_B] = blocks

    def print(self, lvl=0):
        return '\n'.join([p.print() for p in self.procs]) + '\n\n'.join([b.print(lvl) for b in self.blocks]) #  + '\n' + self.ret_term.print(0)

    def print_latex(self, lvl=0):
        return ""


def print_args(args: [SSANode], lvl):
    return '(' + ', '.join([arg.print(lvl) for arg in args]) + ')'


def print_args_latex(args: [SSANode], lvl):
    return ""


def print_terms(terms: [SSANode], lvl):
    return ';\n'.join([(get_indentation(lvl) + term.print(lvl)) for term in terms if term is not None]) + ';'


def print_terms_latex(terms: [SSANode], lvl):
    return ""


def get_indentation(nesting_lvl):
    return '  ' * nesting_lvl


def get_block_by_id(ssa_ast: SSA_AST, b_id: str) -> SSA_B | None:
    for p in ssa_ast.procs:
        for b in p.blocks:
            if b.label.label == b_id:
                return b
    for b in ssa_ast.blocks:
        if b.label.label == b_id:
            return b
    return None


def get_phi_vars_in_block(b: SSA_B) -> [str]:
    phi_vars = []
    for e in b.terms:
        if isinstance(e, SSA_E_ASS_PHI):
            phi_vars.append(e.var)
    return phi_vars


def get_phi_vars_for_jump(b_from: SSA_B, b_to: SSA_B) -> [str]:
    var_names = []
    vars_for_jump = []

    for e in b_from.terms:
        if isinstance(e, SSA_E_ASS):
            var_names.append(e.var.print(0))

    for e in b_to.terms:
        if isinstance(e, SSA_E_ASS_PHI):
            for phi_var in e.args:
                if phi_var.print(0) in var_names:
                    vars_for_jump.append(phi_var)

    return vars_for_jump


def get_first_block_in_proc(blocks: [SSA_B]):
    for b in blocks:
        if b.first_in_proc:
            return b


# Custom class to mock a cfg block
class CFGBlockMock:
    def __init__(self, b_id, exits):
        self.id = b_id
        self.exits = exits


# Class to store transformation information
class ProvInfo:
    def __init__(self):
        self.parent_vars = {}

    def copy(self):
        p = ProvInfo()
        p.parent_vars = self.parent_vars
        return p


# Global variables to store SSA variable data while transforming a single CFG
ssa_results_stored = {}
ssa_results_loads = {}
ssa_results_phi_stored = {}
ssa_results_phi_loads = {}
const_dict = {}

# Global used variable names to prevent duplicate names
used_var_names = {}

# Prefix for new variables from the transformation
buffer_var_name = "_ssa_buffer_"
buffer_counter = 0  # Index for new buffer variables (postfix)

# Mapping dict of nodes to their new buffer variable name to be replaced with when occurring in the translation
buffer_assignments = {}

# Mapping of blocks to their corresponding label if already created
block_refs = {}

# Stores additional statments to be added at the end of the block
addon_statements_per_block = {}


# Update the list of global names to include the new ones found in the last checked cfg
def update_used_vars(vars_stored, constants):
    global used_var_names
    used_var_names.update(get_used_vars(vars_stored, constants))


# Returns the variables set in the two given dicts together with their index
def get_used_vars(vars_stored, constants):
    used_vars = {}
    for block_terms in vars_stored.values():
        for term_vars in block_terms:
            for var, idx in term_vars.items():
                used_vars[var] = idx
    for tup in constants.keys():
        used_vars[tup[0]] = tup[1]
    return used_vars


# Replace the content in lines corresponding to the position given with line[from:to] and col[from:to] with content
def replace_code_with_content(lines, line_from, line_to, col_from, col_to, content):
    l_idx = line_from
    if line_from == line_to:
        line = lines[line_from]
        lines[line_from] = line[:col_from] + content + line[col_to:]
    else:
        while l_idx <= line_to:
            line = lines[l_idx]
            if l_idx == line_from:
                lines[l_idx] = line[:col_from]
            elif l_idx == line_to:
                lines[l_idx] = ''
            else:
                lines[l_idx] = line[col_to:]
            l_idx += 1


# Preprocessing of Python code before parsing it into SSA
# This function converts the following nodes into simpler nodes:
# Lambda, ListComp
def preprocess_py_code(code):
    replaced = True
    while replaced:
        if debug_mode:
            print("Preprocessing code version:")
            print(code)
        tree = ast.parse(code)
        replaced = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Lambda):
                lines = code.split('\n')
                line = lines[node.lineno - 1]
                buffer_var = get_buffer_var()
                replace_code_with_content(lines, node.lineno - 1, node.end_lineno - 1, node.col_offset, node.end_col_offset, buffer_var)

                new_lines = []
                indentation = len(re.findall(r"^ *", line)[0])
                new_lines.append(indentation * ' ' + 'def ' + buffer_var + '(' + ast.unparse(node.args) + '):')
                indentation += 4
                new_lines += [(' ' * indentation + body_l) for body_l in ('return ' + ast.unparse(node.body)).split('\n')]
                lines = lines[:node.lineno - 1] + new_lines + lines[node.lineno - 1:]
                code = '\n'.join(lines)
                replaced = True
            elif isinstance(node, ast.ListComp):
                lines = code.split('\n')
                line = lines[node.lineno - 1]
                buffer_var = get_buffer_var()
                lines[node.lineno - 1] = line[:node.col_offset] + buffer_var + line[node.end_col_offset:]

                new_lines = []
                indentation = len(re.findall(r"^ *", line)[0])
                new_lines.append(indentation * ' ' + buffer_var + ' = []')
                for g in node.generators:
                    new_lines.append(indentation * ' ' + 'for ' + ast.unparse(g.target) + ' in ' + ast.unparse(g.iter) + ':')
                    indentation += 4
                new_lines.append(indentation * ' ' + buffer_var + '.append(' + ast.unparse(node.elt) + ')')
                lines = lines[:node.lineno - 1] + new_lines + lines[node.lineno - 1:]
                code = '\n'.join(lines)
                replaced = True
                break
    return code


def PY_to_SSA_AST(code_str: str, debug: bool):
    global ssa_results_stored, ssa_results_loads, ssa_results_phi_stored, ssa_results_phi_loads, const_dict, used_var_names, debug_mode

    debug_mode = debug
    # Preprocess Python code (Slicing and simple transformations (ex. List Comp -> For Loop))
    code_str = preprocess_py_code(code_str)

    # Create CFG from code and SSA parser Object
    mnode = MNode("local")
    mnode.source = code_str
    mnode.gen_ast()
    cfg = mnode.gen_cfg()
    m_ssa = SSA()

    # Compute the phi nodes of the main CFG
    ssa_results_stored, ssa_results_loads, ssa_results_phi_stored, ssa_results_phi_loads, const_dict = m_ssa.compute_SSA2(cfg, used_var_names)
    # Parse the main CFG
    main_cfg_proc = PS_BS(ProvInfo(), sort_blocks(cfg.get_all_blocks()))
    # Update global tracking variables of used variable names etc for main CFG
    update_used_vars(ssa_results_stored, const_dict)

    # Update the provenance info for the child cfgs (functions which have references to the parents variables)
    prov_info = ProvInfo()
    prov_info.parent_vars = get_used_vars(ssa_results_stored, const_dict)

    # Parse all the functions cfgs
    procs = PS_FS(prov_info, cfg.functioncfgs, cfg.function_args, m_ssa)

    # Create SSA AST
    ssa_ast = SSA_AST(procs, main_cfg_proc)

    if debug_mode:
        print('Main CFG SSA paring variable results:')
        print('ssa_results_stored', ssa_results_stored)
        print('ssa_results_loads', ssa_results_loads)
        print('ssa_results_phi_stored', ssa_results_phi_stored)
        print('ssa_results_phi_loads', ssa_results_phi_loads)
        print('const_dict', const_dict)
        print('\n\n\n')

    return ssa_ast


# Sorts the blocks
def sort_blocks(blocks):
    # blocks.sort(key=lambda x: x.id)
    # print([b.id for b in blocks])
    return blocks


# Collect all phi nodes in the given block
def PS_PHI(curr_block):
    assignments = []
    for stored, loaded in zip(ssa_results_phi_stored[curr_block.id], ssa_results_phi_loads[curr_block.id]):
        var_name = list(stored.keys())[0]
        var_nr = str(stored[var_name])
        var_values = list(map(str, list(loaded[var_name])))
        assignments.append(SSA_E_ASS_PHI(SSA_V_VAR(var_name + '_' + var_nr), [SSA_V_VAR(var_name + '_' + var) for var in var_values]))

    return assignments


# Parse the given function cfgs and sub functions
def PS_FS(prov_info, function_cfgs, function_args, m_ssa):
    global ssa_results_stored, ssa_results_loads, ssa_results_phi_stored, ssa_results_phi_loads, const_dict
    procs = []

    for key in function_cfgs:
        cfg = function_cfgs[key]
        args = function_args[key]

        # Compute the phi nodes of the current function CFG
        ssa_results_stored, ssa_results_loads, ssa_results_phi_stored, ssa_results_phi_loads, const_dict = m_ssa.compute_SSA2(cfg, used_var_names, prov_info.parent_vars)

        # Parse the current functino CFG into SSA
        procs.append(SSA_P(SSA_V_VAR(cfg.name + '_0'), [SSA_V_VAR(arg) for arg in args], PS_BS(prov_info, sort_blocks(cfg.get_all_blocks()))))

        # Update the used variable names
        update_used_vars(ssa_results_stored, const_dict)
        prov_info = prov_info.copy()
        prov_info.parent_vars = get_used_vars(ssa_results_stored, const_dict)

        # If there are function in this function, parse those now
        if len(cfg.functioncfgs) > 0:
            procs += PS_FS(prov_info, cfg.functioncfgs, cfg.function_args, m_ssa)

    return procs


# Parse a list of blocks from Python AST into SSA AST
def PS_BS(prov_info, blocks):
    blocks_parsed = []

    i = 0
    for b in blocks:
        blocks_parsed += PS_B(prov_info, b, i == 0)
        i += 1

    return blocks_parsed


# Parse a block from Python AST into SSA AST
def PS_B(prov_info, block, first_in_proc):
    global block_counter, blocks_checked

    # Init the block reference
    block_ref = PS_B_REF(prov_info, block)

    # Handle for nodes separately (in case of a for the first node will be the for node)
    if isinstance(block.statements[0], ast.For):
        return PS_FOR(prov_info, block_ref, block, block.statements[0], first_in_proc)
    else:
        # Build the statement list beginning with phi assignments, the stmts and a goto
        stmts = PS_PHI(block)
        stmt_lists = [PS_S(prov_info, block, stmt, idx) for idx, stmt in enumerate(block.statements) if not isinstance(stmt, ast.FunctionDef)]
        stmts += [st for l in stmt_lists for st in l]

        # Add additional statements generated by sub processes like in the case of for nodes
        if block in addon_statements_per_block:
            stmts += addon_statements_per_block[block]

        # If there is only one exit add a goto otherwise the exits will be handled in the node itself (like if-block)
        if len(block.exits) == 1:
            stmts += [SSA_E_GOTO(PS_B_REF(prov_info, block.exits[0].target))]

        # Create a new SSA Block
        b = SSA_B(block_ref, stmts, first_in_proc)

        return [b]


# Returns a new buffer variable with a unique name
def get_buffer_var():
    global buffer_counter
    buffer_counter = buffer_counter + 1
    return buffer_var_name + str(buffer_counter - 1)


def PS_FOR(prov_info, block_ref, block, stmt, first_in_proc):
    global addon_statements_per_block
    new_block_name = block_ref.label + '_2'

    stmts = []
    iter_var = get_buffer_var()
    stmts.append(SSA_E_ASS(SSA_V_VAR(iter_var), PS_E(prov_info, block, stmt.iter, 0, False)))

    old_iter_var = PS_E(prov_info, block, stmt.target, 0, False)
    var_name, idx = old_iter_var.name.rsplit('_')
    old_iter_var.name = var_name + '_' + str(int(idx) - 1)
    old_iter_var2 = PS_E(prov_info, block, stmt.target, 0, False)
    old_iter_var2.name = old_iter_var2.name + '_2'
    stmts.append(SSA_E_ASS(old_iter_var, SSA_V_FUNC_CALL(SSA_V_VAR('next'), [SSA_V_VAR(iter_var)])))
    stmts.append(SSA_E_GOTO(SSA_L(new_block_name)))

    b = SSA_B(block_ref, stmts, first_in_proc)

    stmts2 = []
    next_iter_var = PS_E(prov_info, block, stmt.target, 0, False)
    stmts2.append(SSA_E_ASS_PHI(next_iter_var, [old_iter_var, old_iter_var2]))
    buffer = get_buffer_var()
    stmts2.append(SSA_E_ASS(SSA_V_VAR(buffer), SSA_V_FUNC_CALL(SSA_V_VAR('_' + ast.Is.__name__), [next_iter_var, SSA_V_VAR("None")])))
    if len(block.exits) == 1:
        else_ref = SSA_E_RET(None)
    else:
        else_ref = SSA_E_GOTO(PS_B_REF(prov_info, block.exits[1].target))

    stmts2.append(SSA_E_IF_ELSE(SSA_V_VAR(buffer), SSA_E_GOTO(PS_B_REF(prov_info, block.exits[0].target)), else_ref))

    block.exits[0].target.exits[len(block.exits[0].target.exits) - 1].target = CFGBlockMock(new_block_name, block.exits)
    addon_statements_per_block[block.exits[0].target] = [SSA_E_ASS(old_iter_var2, SSA_V_FUNC_CALL(SSA_V_VAR('next'), [SSA_V_VAR(iter_var)]))]
    b2 = SSA_B(SSA_L(new_block_name), stmts2, first_in_proc)

    return [b, b2]


# Parse a Python statement
def PS_S(prov_info, curr_block, stmt, st_nr):
    if isinstance(stmt, ast.Assign):
        if isinstance(stmt.targets[0], ast.Tuple):
            tuple_name = get_buffer_var()
            post_stmts = [SSA_E_ASS(PS_E(prov_info, curr_block, var, st_nr, False), SSA_V_FUNC_CALL(SSA_V_VAR('tuple_get'), [SSA_V_VAR(tuple_name), SSA_V_CONST(str(idx))])) for idx, var in enumerate(stmt.targets[0].elts)]
            return [SSA_E_ASS(SSA_V_VAR(tuple_name), PS_E(prov_info, curr_block, stmt.value, st_nr, True))] + post_stmts
        return [SSA_E_ASS(PS_E(prov_info, curr_block, stmt.targets[0], st_nr, False), PS_E(prov_info, curr_block, stmt.value, st_nr, True))]
    elif isinstance(stmt, ast.If):
        if_ref = SSA_E_GOTO(PS_B_REF(prov_info, curr_block.exits[0].target))
        if len(curr_block.exits) == 1:
            else_ref = SSA_E_RET(None)
        else:
            else_ref = SSA_E_GOTO(PS_B_REF(prov_info, curr_block.exits[1].target))
        return [SSA_E_IF_ELSE(PS_E(prov_info, curr_block, stmt.test, st_nr, True), if_ref, else_ref)]
    elif isinstance(stmt, ast.While):
        if_ref = SSA_E_GOTO(PS_B_REF(prov_info, curr_block.exits[0].target))
        if len(curr_block.exits) == 1:
            else_ref = SSA_E_RET(None)
        else:
            else_ref = SSA_E_GOTO(PS_B_REF(prov_info, curr_block.exits[1].target))
        return [SSA_E_IF_ELSE(PS_E(prov_info, curr_block, stmt.test, st_nr, True), if_ref, else_ref)]
    elif isinstance(stmt, ast.Expr):
        return [PS_E(prov_info, curr_block, stmt.value, st_nr, True)]
    elif isinstance(stmt, ast.Return):
        return [SSA_E_RET(PS_E(prov_info, curr_block, stmt.value, st_nr, True))]
    elif isinstance(stmt, ast.For):
        # Handled separately
        return []


# Parse a Python expression
def PS_E(prov_info, curr_block, stmt, st_nr, is_load):
    if isinstance(stmt, ast.BinOp):
        return SSA_V_FUNC_CALL(SSA_V_VAR('_' + type(stmt.op).__name__), [PS_E(prov_info, curr_block, stmt.left, st_nr, is_load), PS_E(prov_info, curr_block, stmt.right, st_nr, is_load)])
    elif isinstance(stmt, ast.BoolOp):
        result = SSA_V_FUNC_CALL(SSA_V_VAR('_' + type(stmt.op).__name__), [PS_E(prov_info, curr_block, arg, st_nr, is_load) for arg in stmt.values[:2]])
        values = stmt.values[2:]
        while len(values) > 0:
            result = SSA_V_FUNC_CALL(SSA_V_VAR('_' + type(stmt.op).__name__), [result, PS_E(prov_info, curr_block, values[0], st_nr, is_load)])
            values = values[1:]
        return result
    elif isinstance(stmt, ast.ListComp):
        return buffer_assignments[stmt]
    elif isinstance(stmt, ast.UnaryOp):
        return SSA_V_FUNC_CALL(SSA_V_VAR('_' + type(stmt.op).__name__), [PS_E(prov_info, curr_block, stmt.operand, st_nr, is_load)])
    elif isinstance(stmt, ast.Call):
        if isinstance(stmt.func, ast.Attribute):
            return SSA_V_FUNC_CALL(SSA_V_VAR(stmt.func.attr), [PS_E(prov_info, curr_block, arg, st_nr, is_load) for arg in ([stmt.func.value] + stmt.args)])
        else:
            return SSA_V_FUNC_CALL(PS_E(prov_info, curr_block, stmt.func, st_nr, is_load), [PS_E(prov_info, curr_block, arg, st_nr, is_load) for arg in stmt.args])
    elif isinstance(stmt, ast.Compare):
        return PS_MAP2(prov_info, curr_block, PS_E(prov_info, curr_block, stmt.left, st_nr, is_load), stmt.ops, stmt.comparators, st_nr)
    elif isinstance(stmt, ast.Constant):
        if isinstance(stmt.value, str):
            return SSA_V_CONST("'" + stmt.value + "'")
        else:
            return SSA_V_CONST(stmt.value)
    elif isinstance(stmt, ast.Slice):
        return SSA_V_CONST(stmt.value)
    elif isinstance(stmt, ast.Tuple):
        return SSA_V_FUNC_CALL(SSA_V_VAR('new_tuple_' + str(len(stmt.elts))), [PS_E(prov_info, curr_block, arg, st_nr, is_load) for arg in stmt.elts])
    elif isinstance(stmt, ast.Dict):
        return SSA_V_FUNC_CALL(SSA_V_VAR('new_dict_' + str(len(stmt.keys))), [PS_E(prov_info, curr_block, arg, st_nr, is_load) for args in zip(stmt.keys, stmt.values) for arg in args])
    elif isinstance(stmt, ast.Set):
        return SSA_V_FUNC_CALL(SSA_V_VAR('new_set_' + str(len(stmt.elts))), [PS_E(prov_info, curr_block, arg, st_nr, is_load) for arg in stmt.elts])
    elif isinstance(stmt, ast.List):
        return SSA_V_FUNC_CALL(SSA_V_VAR('new_list_' + str(len(stmt.elts))), [PS_E(prov_info, curr_block, arg, st_nr, is_load) for arg in stmt.elts])
    elif isinstance(stmt, ast.Subscript):
        if isinstance(stmt.slice, ast.Slice):
            appendix = ""
            if stmt.slice.lower is not None:
                appendix += "L"
            if stmt.slice.upper is not None:
                appendix += "U"
            if stmt.slice.step is not None:
                appendix += "S"
            if len(appendix) > 0:
                appendix = "_" + appendix
            return SSA_V_FUNC_CALL(SSA_V_VAR('List_Slice' + appendix), [PS_E(prov_info, curr_block, stmt.value, st_nr, is_load)] + ([PS_E(prov_info, curr_block, arg, st_nr, is_load) for arg in [stmt.slice.lower, stmt.slice.upper, stmt.slice.step] if arg is not None]))
        else:
            return SSA_V_FUNC_CALL(SSA_V_VAR('LSD_Get'), [PS_E(prov_info, curr_block, stmt.value, st_nr, is_load)] + [PS_E(prov_info, curr_block, stmt.slice, st_nr, is_load)])
    elif isinstance(stmt, ast.Attribute):
        return SSA_V_FUNC_CALL(SSA_V_VAR(stmt.attr), [PS_E(prov_info, curr_block, stmt.value, st_nr, is_load)])
    elif isinstance(stmt, ast.Name):
        name = get_global_unique_name(stmt.id, prov_info.parent_vars)
        if is_load:
            if name in ssa_results_loads[curr_block.id][st_nr]:
                var_list = [str(var) for var in list(ssa_results_loads[curr_block.id][st_nr][name])]
                var_list_join = str('_'.join(var_list))
                if len(var_list) > 0:
                    return SSA_V_VAR(name + '_' + str(var_list_join))
                else:
                    return SSA_V_VAR(name)
            return SSA_V_VAR(name)
        if name in ssa_results_stored[curr_block.id][st_nr]:
            return SSA_V_VAR(name + '_' + str(ssa_results_stored[curr_block.id][st_nr][name]))
        return SSA_V_VAR(name)
    return stmt


# Get the variables global unique name, considers parent variables to be used
def get_global_unique_name(var_name, parent_vars):
    if var_name in parent_vars:
        return var_name
    idx = 2
    appendix = ""
    if var_name not in used_var_names:
        return var_name
    while (var_name + appendix) in used_var_names:
        appendix = "_" + str(idx)
        idx += 1
    return var_name + appendix


# Recursively generate a call stack with ops and comparators
def PS_MAP2(prov_info, curr_block, left, ops, comparators, st_nr):
    if len(ops) == 1:
        return SSA_V_FUNC_CALL(SSA_V_VAR('_' + type(ops[0]).__name__), (left, PS_E(prov_info, curr_block, comparators[0], st_nr, True)))
    new_left = SSA_V_FUNC_CALL(SSA_V_VAR('_' + type(ops[0]).__name__), (left, PS_E(prov_info, curr_block, comparators[0], st_nr, True)))
    return PS_MAP2(new_left, ops[1:], comparators[1:], st_nr)


# Saves a blocks unique references and returns it
def PS_B_REF(prov_info, curr_block):
    if curr_block in block_refs:
        return block_refs[curr_block]

    block_refs[curr_block] = SSA_L(str(curr_block.id))
    return block_refs[curr_block]


#################################################################################################################################
##### Parsing SSA back to Python ################################################################################################
#################################################################################################################################

# Custom simple CFG representation
class SimpleCFG:
    def __init__(self, name, func_cfgs, entry_block):
        self.name = name
        self.func_cfgs = func_cfgs
        self.entry_block = entry_block

class SimpleCFGBlock:
    def __init__(self, name, exits, ssa_terms):
        self.name = name
        self.exits = exits
        self.ssa_terms = ssa_terms


mapping_label_to_block = {}
def get_simple_cfg_from_ssa(ssa_ast: SSA_AST):
    func_cfgs: [SimpleCFG] = []
    entry_block = None

    for proc in ssa_ast.procs:
        func_cfgs += get_simple_cfg_from_ssa_proc(proc)
    first = True
    for b in ssa_ast.blocks:
        cfg_block = SimpleCFGBlock(b.label.label, get_exits_from_ssa_block(b), b.terms)
        mapping_label_to_block[b.label.label] = cfg_block
        if first:
            first = False
            entry_block = cfg_block

    for (l, b) in mapping_label_to_block.items():
        for idx, e in enumerate(b.exits):
            b.exits[idx] = mapping_label_to_block[b.exits[idx]]
    return SimpleCFG('', func_cfgs, entry_block)


def get_simple_cfg_from_ssa_proc(proc: SSA_P):
    func_cfgs: [SimpleCFG] = []
    entry_block = None

    first = True
    for b in proc.blocks:
        cfg_block = SimpleCFGBlock(b.label.label, get_exits_from_ssa_block(b), b.terms)
        mapping_label_to_block[b.label.label] = cfg_block
        if first:
            first = False
            entry_block = cfg_block

    return [SimpleCFG(proc.name, func_cfgs, entry_block)]


def get_exits_from_ssa_block(block: SSA_B):
    exits = []
    mapping_label_to_block[block.label.label] = block
    for term in block.terms:
        if isinstance(term, SSA_E_GOTO):
            exits.append(term.label.label)
        else:
            exits += recursive_find_exits(term)
    return exits


def recursive_find_exits(cl):
    exits = []
    if hasattr(cl, '__dict__'):
        names = filter(lambda a: not a.startswith('__'), dir(cl))
        dict_of_class = vars(cl)
        for (name, value) in dict_of_class.items():
            if isinstance(value, SSA_E_GOTO):
                exits.append(value.label.label)
            else:
                exits += recursive_find_exits(value)
    return exits

def parse_ssa_to_python(ssa_ast: SSA_AST):
    cfg_simple = get_simple_cfg_from_ssa(ssa_ast)

    blocks_visited = set()
    next_exits = [cfg_simple.entry_block]
    while len(next_exits) > 0:
        exits = next_exits
        next_exits = []
        for block in exits:
            if block not in blocks_visited:
                blocks_visited.add(block)
                next_exits += block.exits
                for term in block.ssa_terms:
                    print(term.print(0))

block_phi_assignment_vars = {}
buffer_assignments_ssa_py = {}
def parse_ssa_to_anf2(term):
    pass