from __future__ import annotations
import ast

from src.scalpel.cfg import CFG
import codegen

from src.scalpel.core.mnode import MNode
from src.scalpel.SSA.const import SSA




class SSACode:

    def __init__(self, cfg: CFG):
        #pNode = ProcedureNodeP(VariableOrLabelNodeX('Name'),  VariableOrLabelListNodeXHead([]), BlockNodeB, procedure_after: ProcedureNodeP)
        self.parse_cfg_to_SSA_code(cfg)

    def parse_cfg(self, block):
        for stmt in block.statements:
            # New Function
            if isinstance(stmt, ast.FunctionDef):
                #print('Found Function')
                print(codegen.to_source(stmt))

            # New Class
            elif isinstance(stmt, ast.ClassDef):
                #print('Found Class')
                print(codegen.to_source(stmt))

            # Global assignments
            elif isinstance(stmt, ast.Assign):
                #print('Found assignment')
                print(codegen.to_source(stmt))
                pass

            # Others
            else:
                pass

    def parse_cfg_to_SSA_code(self, cfg: CFG):
        self.parse_cfg_bfs([cfg.entryblock], 0)

    def parse_cfg_bfs(self, blocks, depth):
        next_blocks = []
        print("Depth", depth)
        for block in blocks:
            self.parse_cfg(block)
            if block.exits:
                for exit in block.exits:
                    next_blocks.append(exit.target)
        if len(next_blocks) > 0:
            self.parse_cfg_bfs(next_blocks, depth + 1)
        # Id of the block.
#        self.id = id
        # Statements in the block.
#        self.statements = []
        # Calls to functions inside the block (represents context switches to
        # some functions' CFGs).
#        self.func_calls = []
        # Links to predecessors in a control flow graph.
#        self.predecessors = []
        # Links to the next blocks in a control flow graph.
#        self.exits = []


class SSANode:
    def __init__(self):
        pass

    def print(self, nesting_lvl):
        return 'not implemented'


class SSA_L(SSANode):
    def __init__(self, label: str):
        self.label: str = label

    def print(self, lvl):
        return f"{self.label}"


class SSA_V(SSANode):
    def __init__(self, value: SSA_V_CONST | SSA_V_VAR | SSA_V_FUNC_CALL):
        self.value: SSA_V_CONST | SSA_V_VAR | SSA_V_FUNC_CALL = value

    def print(self, lvl):
        return f"{self.value.print(lvl)}"


class SSA_V_CONST(SSANode):
    def __init__(self, value: str):
        self.value: str = value

    def print(self, lvl):
        return f"{self.value}"


class SSA_V_VAR(SSANode):
    def __init__(self, name: str):
        self.name: str = name

    def print(self, lvl):
        return f"{self.name}"


class SSA_V_FUNC_CALL(SSANode):
    def __init__(self, name: SSA_L | SSA_V, args: SSA_V):
        self.name: SSA_V_VAR = name
        self.args = args

    def print(self, lvl):
        return f"{self.name.print(lvl) + print_args(self.args, lvl)}"


class SSA_E(SSANode):
    def __init__(self, term: SSA_E_ASS | SSA_E_ASS_PHI | SSA_E_GOTO | SSA_E_IF_ELSE | SSA_E_RET):
        self.term: SSA_E_ASS | SSA_E_ASS_PHI | SSA_E_GOTO | SSA_E_IF_ELSE | SSA_E_RET = term

    def print(self, lvl):
        return "" # implemented in child nodes


class SSA_E_ASS_PHI(SSANode):
    def __init__(self, var: SSA_V, args: [SSA_V]):
        self.var: SSA_V = var
        self.args: [SSA_V] = args

    def print(self, lvl):
        return self.var.print(lvl) + ' ← φ' + print_args(self.args, lvl)


class SSA_E_ASS(SSANode):
    def __init__(self, var: SSA_V, value: SSA_V):
        self.var: SSA_V = var
        self.value: SSA_V = value

    def print(self, lvl):
        return f"{self.var.print(lvl)+ ' ← ' + self.value.print(lvl)}"


class SSA_E_GOTO(SSANode):
    def __init__(self, label: SSA_L):
        self.label: SSA_L = label

    def print(self, lvl):
        return f"{'goto L' + self.label.print(lvl)}"


class SSA_E_RET(SSANode):
    def __init__(self, func_call: SSA_V_FUNC_CALL):
        self.func_call: SSA_V_FUNC_CALL = func_call

    def print(self, lvl):
        if self.func_call is None:
            return 'ret'
        return f"ret {self.func_call.print(lvl)};"


class SSA_E_IF_ELSE(SSANode):
    def __init__(self, test: SSA_V, term_if: SSA_E, term_else: SSA_E):
        self.test: SSA_V = test
        self.term_if: SSA_E = term_if
        self.term_else: SSA_E = term_else

    def print(self, lvl):
        new_line = '\n'
        return f"{'if ' + self.test.print(lvl) + ' then ' + self.term_if.print(lvl) + new_line + get_indentation(lvl) + 'else ' + self.term_else.print(lvl)}"


class SSA_B(SSANode):
    def __init__(self, label: SSA_L, terms: [SSA_E], first_in_proc: bool):
        self.label: SSA_L = label
        self.terms: [SSA_E] = terms
        self.first_in_proc: bool = first_in_proc

    def print(self, lvl):
        new_line = '\n'

        if self.first_in_proc:
            return print_terms(self.terms, lvl)
        return get_indentation(lvl) + f"{'L' + self.label.print(lvl+1) + ': ' + new_line + print_terms(self.terms, lvl+1)}"


class SSA_P(SSANode):
    def __init__(self, name: SSA_V_VAR, blocks: [SSA_B]):
        self.name: SSA_V_VAR = name
        self.blocks: [SSA_B] = blocks
        self.blocks.sort(key=lambda x: x.label.label)

    def print(self):
        # return '\n\n'.join([b.print(0) for b in self.blocks])
        return 'proc ' + self.name.print(0) + '()\n{\n' + '\n\n'.join([b.print(1) for b in self.blocks]) + '\n}\n'


class SSA_AST(SSANode):
    def __init__(self, procs: [SSA_P], blocks: [SSA_B]):
        self.procs: [SSA_P] = procs
        self.blocks: [SSA_B] = blocks

    def print(self):
        return '\n'.join([p.print() for p in self.procs]) + '\n\n'.join([b.print(0) for b in self.blocks]) # + '\n' + self.ret_term.print(0)


def print_args(args: [SSANode], lvl):
    return '(' + ', '.join([arg.print(lvl) for arg in args]) + ')'


def print_terms(terms: [SSANode], lvl):
    return ';\n'.join([(get_indentation(lvl) + term.print(lvl)) for term in terms if term is not None]) + ';'


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




block_counter = 1
block_refs = {}
ssa_results_stored = {}
ssa_results_loads = {}
ssa_results_phi_stored = {}
ssa_results_phi_loads = {}
const_dict = {}

# TODO include functions - ssa only uses all under entry block
def PY_to_SSA_AST(code_str: str):
    global ssa_results_stored, ssa_results_loads, ssa_results_phi_stored, ssa_results_phi_loads, const_dict

    mnode = MNode("local")
    mnode.source = code_str
    mnode.gen_ast()
    cfg = mnode.gen_cfg()
    m_ssa = SSA()

    procs = PS_FS(None, cfg.functioncfgs, m_ssa)
    ssa_results_stored, ssa_results_loads, ssa_results_phi_stored, ssa_results_phi_loads, const_dict = m_ssa.compute_SSA2(cfg)
    print('ssa_results_stored',ssa_results_stored)
    print('ssa_results_loads',ssa_results_loads)
    print('ssa_results_phi_stored',ssa_results_phi_stored)
    print('ssa_results_phi_loads',ssa_results_phi_loads)
    print('const_dict',const_dict)

    base_proc_name = "SSA_START_PROC"
    # proc = SSA_P(SSA_V_VAR(base_proc_name), ) #+ PS_FS(cfg.functioncfgs))
    ssa_ast = SSA_AST(procs, PS_BS(None, cfg.get_all_blocks()))
    return ssa_ast


def PS_PHI(curr_block):

    assignments = []
    for stored, loaded in zip(ssa_results_phi_stored[curr_block.id], ssa_results_phi_loads[curr_block.id]):
        var_name = list(stored.keys())[0]
        var_nr = str(stored[var_name])
        var_values = list(map(str, list(loaded[var_name])))
        assignments.append(SSA_E_ASS_PHI(SSA_V_VAR(var_name + '_' + var_nr), [SSA_V_VAR(var_name + '_' + var) for var in var_values]))

    return assignments


def PS_FS(prov_info, function_cfgs, m_ssa):
    global ssa_results_stored, ssa_results_loads, ssa_results_phi_stored, ssa_results_phi_loads, const_dict
    procs = []
    for key in function_cfgs:
        cfg = function_cfgs[key]
        ssa_results_stored, ssa_results_loads, ssa_results_phi_stored, ssa_results_phi_loads, const_dict = m_ssa.compute_SSA2(
            cfg)
        procs.append(SSA_P(SSA_V_VAR(cfg.name), PS_BS(prov_info, cfg.get_all_blocks())))
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

    stmts = PS_PHI(block)
    stmts += [PS_S(prov_info, block, stmt, idx) for idx, stmt in enumerate(block.statements) if not isinstance(stmt, ast.FunctionDef)]
    if len(block.exits) == 1:
        stmts += [SSA_E_GOTO(PS_B_REF(prov_info, block.exits[0].target))]
    b = SSA_B(block_ref, stmts, first_in_proc)

    if len(block.exits) == 0:
        return [b]
    #exits = reduce(lambda a, b: a+b, [PS_B(prov_info, exit_b.target) for exit_b in block.exits])
    return [b]# + exits


def PS_S(prov_info, curr_block, stmt, st_nr):
    if isinstance(stmt, ast.Assign):
        return SSA_E_ASS(PS_E(prov_info, curr_block, stmt.targets[0], st_nr, False), PS_E(prov_info, curr_block, stmt.value, st_nr, True))
    elif isinstance(stmt, ast.If):
        if_ref = SSA_E_GOTO(PS_B_REF(prov_info, curr_block.exits[0].target))
        if len(curr_block.exits) == 1:
            else_ref = SSA_E_RET(None)
        else:
            else_ref = SSA_E_GOTO(PS_B_REF(prov_info, curr_block.exits[1].target))
        return SSA_E_IF_ELSE(PS_E(prov_info, curr_block, stmt.test, st_nr, True), if_ref, else_ref)
    elif isinstance(stmt, ast.While):
        if_ref = SSA_E_GOTO(PS_B_REF(prov_info, curr_block.exits[0].target))
        if len(curr_block.exits) == 1:
            else_ref = SSA_E_RET(None)
        else:
            else_ref = SSA_E_GOTO(PS_B_REF(prov_info, curr_block.exits[1].target))
        return SSA_E_IF_ELSE(PS_E(prov_info, curr_block, stmt.test, st_nr, True), if_ref, else_ref)
    elif isinstance(stmt, ast.Expr):
        return PS_E(prov_info, curr_block, stmt.value, st_nr, True)


def PS_E(prov_info, curr_block, stmt, st_nr, is_load):
    if isinstance(stmt, ast.BinOp):
        return SSA_V_FUNC_CALL(SSA_V_VAR(type(stmt.op).__name__), [PS_E(prov_info, curr_block, stmt.left, st_nr, is_load), PS_E(prov_info, curr_block, stmt.right, st_nr, is_load)])
    elif isinstance(stmt, ast.BoolOp): # TODO
        return SSA_V_FUNC_CALL(SSA_V_VAR(type(stmt.op).__name__), [PS_E(prov_info, curr_block, stmt.values[0], st_nr, is_load), PS_E(prov_info, curr_block, stmt.values[1], st_nr, is_load)])
    elif isinstance(stmt, ast.UnaryOp):  # TODO
        return SSA_V_FUNC_CALL(SSA_V_VAR(type(stmt.op).__name__), [PS_E(prov_info, curr_block, stmt.operand, st_nr, is_load)])
    elif isinstance(stmt, ast.Call):
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
    elif isinstance(stmt, ast.Dict):
        return SSA_V_FUNC_CALL(SSA_V_VAR('new_dict_' + str(len(stmt.keys))), [PS_E(prov_info, curr_block, arg, st_nr, is_load) for args in zip(stmt.keys, stmt.values) for arg in args])
    elif isinstance(stmt, ast.Set):
        return SSA_V_FUNC_CALL(SSA_V_VAR('new_set_' + str(len(stmt.elts))), [PS_E(prov_info, curr_block, arg, st_nr, is_load) for arg in stmt.elts])
    elif isinstance(stmt, ast.List):
        return SSA_V_FUNC_CALL(SSA_V_VAR('new_list_' + str(len(stmt.elts))), [PS_E(prov_info, curr_block, arg, st_nr, is_load) for arg in stmt.elts])
    elif isinstance(stmt, ast.Subscript):
        if isinstance(stmt.slice, ast.Slice):
            return SSA_V_FUNC_CALL(SSA_V_VAR('List_Slice'), [PS_E(prov_info, curr_block, stmt.value, st_nr, is_load)] + ([PS_E(prov_info, curr_block, arg, st_nr, is_load) for arg in [stmt.slice.lower, stmt.slice.upper, stmt.slice.step] if arg is not None]))
        else:
            return SSA_V_FUNC_CALL(SSA_V_VAR('LSD_Get'), [PS_E(prov_info, curr_block, stmt.value, st_nr, is_load)] + [PS_E(prov_info, curr_block, stmt.slice, st_nr, is_load)])
    elif isinstance(stmt, ast.Attribute):
        return SSA_V_FUNC_CALL(SSA_V_VAR(stmt.attr), [PS_E(prov_info, curr_block, stmt.value, st_nr, is_load)])
    elif isinstance(stmt, ast.Name):
        if is_load:
            if stmt.id in ssa_results_loads[curr_block.id][st_nr]:
                var_list = [str(var) for var in list(ssa_results_loads[curr_block.id][st_nr][stmt.id])]
                var_list_join = str('_'.join(var_list))
                return SSA_V_VAR(stmt.id + '_' + str(var_list_join))
            return SSA_V_VAR(stmt.id)
        return SSA_V_VAR(stmt.id + '_' + str(ssa_results_stored[curr_block.id][st_nr][stmt.id]))
    return stmt


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
