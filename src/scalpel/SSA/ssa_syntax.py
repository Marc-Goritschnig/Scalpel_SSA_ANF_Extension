from __future__ import annotations
import ast

from src.scalpel.cfg import CFG
import codegen

from src.scalpel.core.mnode import MNode
from src.scalpel.SSA.const import SSA

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
    def __init__(self, value: SSA_V_CONST | SSA_V_VAR | SSA_V_FUNC_CALL):
        self.value: SSA_V_CONST | SSA_V_VAR | SSA_V_FUNC_CALL = value

    def print(self, lvl):
        return f"{self.value.print(lvl)}"

    def print_latex(self, lvl):
        return ""

class SSA_L(SSA_V):
    def __init__(self, label: str):
        self.label: str = label

    def print(self, lvl):
        return f"{self.label}"

    def print_latex(self, lvl):
        return ""


class SSA_V_CONST(SSA_V):
    def __init__(self, value: str):
        self.value: str = value

    def print(self, lvl):
        return f"{self.value}"

    def print_latex(self, lvl):
        return ""


class SSA_V_VAR(SSA_V):
    def __init__(self, name: str):
        self.name: str = name

    def print(self, lvl):
        return f"{self.name}"

    def print_latex(self, lvl):
        return ""


class SSA_V_FUNC_CALL(SSA_V):
    def __init__(self, name: SSA_L | SSA_V, args: SSA_V):
        self.name: SSA_V_VAR = name
        self.args = args

    def print(self, lvl):
        return f"{self.name.print(lvl) + print_args(self.args, lvl)}"

    def print_latex(self, lvl):
        return ""


class SSA_E(SSANode):
    def __init__(self, term: SSA_E_ASS | SSA_E_ASS_PHI | SSA_E_GOTO | SSA_E_IF_ELSE | SSA_E_RET):
        self.term: SSA_E_ASS | SSA_E_ASS_PHI | SSA_E_GOTO | SSA_E_IF_ELSE | SSA_E_RET = term

    def print(self, lvl):
        return "" # implemented in child nodes

    def print_latex(self, lvl):
        return ""


class SSA_E_ASS_PHI(SSA_E):
    def __init__(self, var: SSA_V, args: [SSA_V]):
        self.var: SSA_V = var
        self.args: [SSA_V] = args

    def print(self, lvl):
        return self.var.print(lvl) + ' ' + font['assign'] + ' ' + font['phi'] + print_args(self.args, lvl)

    def print_latex(self, lvl):
        return ""


class SSA_E_ASS(SSA_E):
    def __init__(self, var: SSA_V, value: SSA_V):
        self.var: SSA_V = var
        self.value: SSA_V = value

    def print(self, lvl):
        return f"{self.var.print(lvl)+ ' ' + font['assign'] + ' ' + self.value.print(lvl)}"

    def print_latex(self, lvl):
        return ""


class SSA_E_GOTO(SSA_E):
    def __init__(self, label: SSA_L):
        self.label: SSA_L = label

    def print(self, lvl):
        return f"{'goto L' + self.label.print(lvl)}"

    def print_latex(self, lvl):
        return ""


class SSA_E_RET(SSA_E):
    def __init__(self, value: SSA_V):
        self.value: SSA_V = value

    def print(self, lvl):
        if self.value is None:
            return 'ret'
        return f"ret {self.value.print(lvl)}"

    def print_latex(self, lvl):
        return ""


class SSA_E_IF_ELSE(SSA_E):
    def __init__(self, test: SSA_V, term_if: SSA_E, term_else: SSA_E):
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
        self.name: SSA_V_VAR = name
        self.args: [SSA_V] = args
        self.blocks: [SSA_B] = blocks

    def print(self):
        # return '\n\n'.join([b.print(0) for b in self.blocks])
        return 'proc ' + self.name.print(0) + print_args(self.args, 0) + '\n{\n' + '\n\n'.join([b.print(1) for b in self.blocks]) + '\n}\n'

    def print_latex(self):
        return ""


class SSA_AST(SSANode):
    def __init__(self, procs: [SSA_P], blocks: [SSA_B]):
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


def get_block_by_id(ssa_ast: SSA_AST, id: str) -> SSA_B:
    for p in ssa_ast.procs:
        for b in p.blocks:
            if b.label.label == id:
                return b
    for b in ssa_ast.blocks:
        if b.label.label == id:
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


block_counter = 1
block_refs = {}
ssa_results_stored = {}
ssa_results_loads = {}
ssa_results_phi_stored = {}
ssa_results_phi_loads = {}
const_dict = {}
used_var_names = []


def update_used_vars():
    global used_var_names
    for block_vars in ssa_results_stored.values():
        for term_vars in block_vars:
            for var in term_vars:
                used_var_names.append(var)
    for tup in const_dict.keys():
        used_var_names.append(tup[1])


def PY_to_SSA_AST(code_str: str):
    global ssa_results_stored, ssa_results_loads, ssa_results_phi_stored, ssa_results_phi_loads, const_dict, used_var_names

    mnode = MNode("local")
    mnode.source = code_str
    mnode.gen_ast()
    cfg = mnode.gen_cfg()
    m_ssa = SSA()

    procs = PS_FS(None, cfg.functioncfgs, cfg.function_args, m_ssa)
    ssa_results_stored, ssa_results_loads, ssa_results_phi_stored, ssa_results_phi_loads, const_dict = m_ssa.compute_SSA2(cfg, used_var_names)
    print('ssa_results_stored',ssa_results_stored)
    print('ssa_results_loads',ssa_results_loads)
    print('ssa_results_phi_stored',ssa_results_phi_stored)
    print('ssa_results_phi_loads',ssa_results_phi_loads)
    print('const_dict',const_dict)

    base_proc_name = "SSA_START_PROC"
    # proc = SSA_P(SSA_V_VAR(base_proc_name), ) #+ PS_FS(cfg.functioncfgs))
    ssa_ast = SSA_AST(procs, PS_BS(None, sort_blocks(cfg.get_all_blocks())))
    update_used_vars()
    return ssa_ast


def sort_blocks(blocks):
    #blocks.sort(key=lambda x: x.id)
    #print([b.id for b in blocks])
    return blocks

def PS_PHI(curr_block):

    assignments = []
    for stored, loaded in zip(ssa_results_phi_stored[curr_block.id], ssa_results_phi_loads[curr_block.id]):
        var_name = list(stored.keys())[0]
        var_nr = str(stored[var_name])
        var_values = list(map(str, list(loaded[var_name])))
        assignments.append(SSA_E_ASS_PHI(SSA_V_VAR(var_name + '_' + var_nr), [SSA_V_VAR(var_name + '_' + var) for var in var_values]))

    return assignments


def PS_FS(prov_info, function_cfgs, function_args, m_ssa):
    global ssa_results_stored, ssa_results_loads, ssa_results_phi_stored, ssa_results_phi_loads, const_dict
    procs = []
    for key in function_cfgs:
        cfg = function_cfgs[key]
        args = function_args[key]
        ssa_results_stored, ssa_results_loads, ssa_results_phi_stored, ssa_results_phi_loads, const_dict = m_ssa.compute_SSA2(
            cfg)
        procs.append(SSA_P(SSA_V_VAR(cfg.name + '_0'), [SSA_V_VAR(arg) for arg in args], PS_BS(prov_info, sort_blocks(cfg.get_all_blocks()))))
        update_used_vars()
    return procs


# blocks_checked = []


def PS_BS(prov_info, blocks):
    blocks_parsed = []
    # Initialize block ids to have the same as in the parsed SSA / maybe change to block references instead of id
    #for b in blocks:
    #    PS_B_REF(prov_info, b)
    i = 0
    for b in blocks:
        blocks_parsed += PS_B(None, b, i == 0)
        i += 1

    return blocks_parsed


def PS_B(prov_info, block, first_in_proc):
    global block_counter, blocks_checked

    # if block in blocks_checked:
    #    return []
    # blocks_checked.append(block)
    block_ref = PS_B_REF(prov_info, block)

    if isinstance(block.statements[0], ast.For):
        return PS_FOR(prov_info, block_ref, block, block.statements[0], first_in_proc)
    else:
        stmts = PS_PHI(block)
        stmt_lists = [PS_S(prov_info, block, stmt, idx) for idx, stmt in enumerate(block.statements) if not isinstance(stmt, ast.FunctionDef)]
        stmts += [st for l in stmt_lists for st in l]

        if block in addon_statements_per_block:
            stmts += addon_statements_per_block[block]
        if len(block.exits) == 1:
            stmts += [SSA_E_GOTO(PS_B_REF(prov_info, block.exits[0].target))]
        b = SSA_B(block_ref, stmts, first_in_proc)

        if len(block.exits) == 0:
            return [b]
        #exits = reduce(lambda a, b: a+b, [PS_B(prov_info, exit_b.target) for exit_b in block.exits])
        return [b]# + exits


buffer_var_name = "_ssa_buffer_"
buffer_counter = 0


def get_buffer_var():
    global buffer_counter
    buffer_counter = buffer_counter + 1
    return buffer_var_name + str(buffer_counter - 1)


def PS_FOR(prov_info, block_ref, block, stmt, first_in_proc):
    # LX
    # l = list
    # i = next(l)
    # LX_2:
    # i_1 <- PHI(i_0, i_1)
    # buf <- i is None
    # if buf:
    #   goto LX+2
    # else:
    #   goto LX+1
    # LX+1
    # Body of loop
    # i_1 = next(l)
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
    stmts2.append(SSA_E_ASS(SSA_V_VAR(buffer), SSA_V_FUNC_CALL(SSA_V_VAR(ast.Is.__name__), [next_iter_var, SSA_V_VAR("None")])))
    if len(block.exits) == 1:
        else_ref = SSA_E_RET(None)
    else:
        else_ref = SSA_E_GOTO(PS_B_REF(prov_info, block.exits[1].target))

    stmts2.append(SSA_E_IF_ELSE(SSA_V_VAR(buffer), SSA_E_GOTO(PS_B_REF(prov_info, block.exits[0].target)), else_ref))

    block.exits[0].target.exits[0].target = CFGBlockMock(new_block_name)
    addon_statements_per_block[block.exits[0].target] = [SSA_E_ASS(old_iter_var2, SSA_V_FUNC_CALL(SSA_V_VAR('next'), [SSA_V_VAR(iter_var)]))]
    b2 = SSA_B(SSA_L(new_block_name), stmts2, first_in_proc)

    return [b, b2]

addon_statements_per_block = {}

class CFGBlockMock:
  def __init__(self, id):
    self.id = id

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


def PS_E(prov_info, curr_block, stmt, st_nr, is_load):
    if isinstance(stmt, ast.BinOp):
        return SSA_V_FUNC_CALL(SSA_V_VAR(type(stmt.op).__name__), [PS_E(prov_info, curr_block, stmt.left, st_nr, is_load), PS_E(prov_info, curr_block, stmt.right, st_nr, is_load)])
    elif isinstance(stmt, ast.BoolOp):
        result = SSA_V_FUNC_CALL(SSA_V_VAR(type(stmt.op).__name__), [PS_E(prov_info, curr_block, arg, st_nr, is_load) for arg in stmt.values[:2]])
        values = stmt.values[2:]
        while len(values) > 0:
            result = SSA_V_FUNC_CALL(SSA_V_VAR(type(stmt.op).__name__), [result, PS_E(prov_info, curr_block, values[0], st_nr, is_load)])
            values = values[1:]
        return result
    elif isinstance(stmt, ast.UnaryOp):
        return SSA_V_FUNC_CALL(SSA_V_VAR(type(stmt.op).__name__), [PS_E(prov_info, curr_block, stmt.operand, st_nr, is_load)])
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
        name = get_global_unique_name(stmt.id)
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


def get_global_unique_name(var_name):
    idx = 2
    appendix = ""
    if var_name not in used_var_names:
        return var_name
    while (var_name + appendix) in used_var_names:
        appendix = "_" + str(idx)
        idx += 1
    return var_name + appendix

def PS_MAP2(prov_info, curr_block, left, ops, comparators, st_nr):
    if len(ops) == 1:
        return SSA_V_FUNC_CALL(SSA_V_VAR(type(ops[0]).__name__), (left, PS_E(prov_info, curr_block, comparators[0], st_nr, True)))
    new_left = SSA_V_FUNC_CALL(SSA_V_VAR(type(ops[0]).__name__), (left, PS_E(prov_info, curr_block, comparators[0], st_nr, True)))
    return PS_MAP2(new_left, ops[1:], comparators[1:], st_nr)


def PS_B_REF(prov_info, curr_block):
    global block_counter
    if curr_block in block_refs:
        return block_refs[curr_block]

    #block_refs[curr_block] = SSA_L(str(block_counter))
    block_refs[curr_block] = SSA_L(str(curr_block.id))
    block_counter += 1
    return block_refs[curr_block]

