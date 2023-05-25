from __future__ import annotations

from src.scalpel.SSA.ssa_syntax import *


class ANFNode:
    def __init__(self):
        pass

    def print(self, nesting_lvl):
        return 'not implemented'


class ANF_V(ANFNode):
    def __init__(self, value: ANF_V_CONST | ANF_V_VAR | ANF_V_FUNC):
        self.value: ANF_V_CONST | ANF_V_VAR | ANF_V_FUNC = value

    def print(self, lvl):
        return f"{self.value.print()}"


class ANF_V_CONST(ANF_V):
    def __init__(self, value: str):
        self.value: str = value

    def print(self, lvl):
        return f"{self.value}"


class ANF_V_VAR(ANF_V):
    def __init__(self, name: str):
        self.name: str = name

    def print(self, lvl):
        return f"{self.name}"


class ANF_V_UNIT(ANF_V):
    def __init__(self):
        pass

    def print(self, lvl):
        return get_indentation(lvl) + "unit"


class ANF_V_FUNC(ANF_V):
    def __init__(self, input_var: ANF_V, term: ANF_E):
        self.input_var: ANF_V = input_var
        self.term: ANF_E = term

    def print(self, lvl):
        if self.input_var is None:
            if issubclass(type(self.term), ANF_V):
                return f"λ . {self.term.print(lvl)}"
            return f"λ . \n{self.term.print(lvl)}"
        if issubclass(type(self.term), ANF_V):
            return f"λ{self.input_var.print(0)} . {self.term.print(lvl)}"
        return f"λ{self.input_var.print(0)} . \n{self.term.print(lvl)}"


class ANF_E(ANFNode):
    def __init__(self):
        pass

    def print(self, lvl):
        pass


class ANF_E_APP(ANF_E):
    def __init__(self, params: [ANF_V_VAR], name: ANF_V_VAR):
        self.params: [ANF_V_VAR] = params
        self.name: ANF_V_VAR = name

    def print(self, lvl):
        return get_indentation(lvl) + f"{self.name.print(lvl)} {' '.join([var.print(lvl) for var in self.params])}"


class ANF_E_LET(ANF_E):
    def __init__(self, var: ANF_V_VAR, term1: ANF_E, term2: ANF_E):
        self.var: ANF_V_VAR = var
        self.term1: ANF_E = term1
        self.term2: ANF_E = term2

    def print(self, lvl):
        return get_indentation(lvl) + f"let {self.var.print(lvl + 1)} = {self.term1.print(0)} in \n{self.term2.print(lvl + 1)}"


class ANF_E_LETREC(ANF_E):
    def __init__(self, var: ANF_V_FUNC, term1: ANF_E, term2: ANF_E):
        self.var: ANF_V_FUNC = var
        self.term1: ANF_E = term1
        self.term2: ANF_E = term2

    def print(self, lvl):
        # assignments = ('\n' + get_indentation(lvl + 1)).join(v.print(lvl + 2) + ' = ' + t.print(lvl+2) for v, t in zip(self.var, self.term1))
        if isinstance(self.term1, ANF_E_LETREC) or isinstance(self.term1, ANF_E_LET):
            return get_indentation(lvl) + 'letrec ' + self.var.print(lvl + 1) + ' = ' + '\n' + self.term1.print(lvl + 1) + '\n' + get_indentation(lvl) + 'in \n' + self.term2.print(lvl + 1)
        else:
            return get_indentation(lvl) + 'letrec ' + self.var.print(lvl + 1) + ' = ' + self.term1.print(lvl+1) + '\n' + get_indentation(lvl) + 'in \n' + self.term2.print(lvl + 1)


class ANF_E_IF(ANF_E):
    def __init__(self, test: ANF_V_VAR, term_if: ANF_E, term_else: ANF_E):
        self.test: ANF_V_VAR = test
        self.term_if: ANF_E = term_if
        self.term_else: ANF_E = term_else

    def print(self, lvl):
        return get_indentation(lvl) + f"if {self.test.print(0)} then \n{self.term_if.print(lvl + 1)} \n{get_indentation(lvl)}else\n{self.term_else.print(lvl + 1)}"


def get_indentation(nesting_lvl):
    return '  ' * nesting_lvl


def parse_ssa_to_anf(ssa: SSA_AST):
    return SA(ssa)

ssa_ast_global = None
buffer_variable_counter = 0
block_identifier = 'L'

def SA(ssa_ast: SSA_AST):
    global ssa_ast_global
    ssa_ast_global = ssa_ast
    return SA_PS(ssa_ast.procs, SA_BS(ssa_ast.blocks, ANF_E_APP([], ANF_V_VAR(get_first_block_in_proc(ssa_ast.blocks).label.label))))


def SA_PS(ps: [SSA_P], inner_term):
    if len(ps) == 0:
        return inner_term

    p: SSA_P = ps[0]
    if len(ps) == 1:
        let_rec = ANF_E_LETREC(SA_V(p.name), SA_BS(p.blocks, ANF_E_APP([], ANF_V_VAR(block_identifier + get_first_block_in_proc(p.blocks).label.label))), inner_term)
    else:
        let_rec = ANF_E_LETREC(SA_V(p.name), SA_BS(p.blocks, ANF_E_APP([], ANF_V_VAR(block_identifier + get_first_block_in_proc(p.blocks).label.label))), SA_PS[1:])

    return let_rec

def SA_BS(bs: [SSA_B], inner_call):
    if len(bs) == 0:
        return inner_call
    b: SSA_B = bs[0]
    block_vars = [SA_V(phi_var)for phi_var in get_phi_vars_in_block(b)]

    # Create self containing functions to build lambda functions in each other. leading to have functions with multiple variables
    if len(block_vars) > 0:
        func = ANF_V_FUNC(block_vars[0], SA_ES(b, b.terms))
        block_vars = block_vars[1:]

        while len(block_vars) > 0:
            func = ANF_V_FUNC(block_vars[0], func)
            block_vars = block_vars[1:]
    else:
        func = ANF_V_FUNC(None, SA_ES(b, b.terms))

    if len(bs) == 1:
        let_rec = ANF_E_LETREC(ANF_V_CONST(block_identifier + b.label.label), func,
                               inner_call)
    else:
        let_rec = ANF_E_LETREC(ANF_V_CONST(block_identifier + b.label.label), func,
                           SA_BS(bs[1:], inner_call))

    #for b in bs[1:]:
    #    block_vars = [SA_V(phi_var) for phi_var in get_phi_vars_in_block(b)]
    #    let_rec.add_entry(SA_V(b.label), ANF_V_FUNC(block_vars, SA_ES(b, b.terms)))
    return let_rec


def SA_ES(b: SSA_B, terms: [SSA_E]):

    if len(terms) == 0: return ANF_V_UNIT()
    term = terms[0]
    if term is None: return ANF_V_UNIT()

    if isinstance(term, SSA_E_ASS):
        unwrap_inner_applications_naming(term.value)
        return unwrap_inner_applications_let_structure(term.value, ANF_E_LET(SA_V(term.var), SA_V(term.value), SA_ES(b, terms[1:])))
    if isinstance(term, SSA_E_GOTO):
        return ANF_E_APP(get_phi_vars_for_jump(b, get_block_by_id(ssa_ast_global, term.label.label)), ANF_V_CONST(block_identifier + term.label.label))
    if isinstance(term, SSA_E_ASS_PHI):
        return SA_ES(b, terms[1:])
    if isinstance(term, SSA_E_RET):
        unwrap_inner_applications_naming(term.value)
        return unwrap_inner_applications_let_structure(term.value, SA_V(term.value))
    if isinstance(term, SSA_E_IF_ELSE):
        unwrap_inner_applications_naming(term.test, True)
        return unwrap_inner_applications_let_structure(term.test, ANF_E_IF(SA_V(term.test, True), SA_ES(b, [term.term_if]), SA_ES(b, [term.term_else])), True)
    #if isinstance(term, SSA_V_FUNC_CALL):
    #    unwrap_inner_applications_naming(term.test)
    #    return unwrap_inner_applications_let_structure(ANF_E_LET(ANF_V_VAR('_'), SA_V(term), SA_ES(b, terms[1:])))
    if issubclass(type(term), SSA_V):
        return SA_V(term)
    print("not impl", term)
    return ANF_E_APP([], SA_V('terms'))


def unwrap_inner_applications_let_structure(var: SSA_V, inner, unwrap_var: bool = False):
    if isinstance(var, SSA_V_FUNC_CALL):
        if unwrap_var:
            name = buffer_assignments[var]
            inner = unwrap_inner_applications_let_structure(var, ANF_E_LET(ANF_V_VAR(name), SA_V(var), inner))
        for arg in var.args:
            if isinstance(arg, SSA_V_FUNC_CALL):
                name = buffer_assignments[arg]
                inner = unwrap_inner_applications_let_structure(arg, ANF_E_LET(ANF_V_VAR(name), SA_V(arg), inner))
    return inner


def unwrap_inner_applications_naming(var: SSA_V, unwrap_var: bool = False):
    if isinstance(var, SSA_V_FUNC_CALL):
        if unwrap_var:
            name = get_buffer_variable()
            buffer_assignments[var] = name
        for arg in var.args:
            if isinstance(arg, SSA_V_FUNC_CALL):
                name = get_buffer_variable()
                buffer_assignments[arg] = name
                unwrap_inner_applications_naming(arg)


def SA_V(var: SSA_V, can_be_buffered: bool = False):
    if isinstance(var, SSA_V_VAR):
        return ANF_V_VAR(var.name)
    if isinstance(var, SSA_V_CONST):
        return ANF_V_CONST(var.value)
    if isinstance(var, SSA_L):
        return ANF_V_CONST(var.label)
    if isinstance(var, SSA_V_FUNC_CALL):
        if can_be_buffered and var in buffer_assignments:
            return ANF_V_VAR(buffer_assignments[var])
        else:
            return ANF_E_APP([(ANF_V_VAR(buffer_assignments[par]) if par in buffer_assignments else SA_V(par)) for par in var.args], SA_V(var.name))

    return ANF_V_CONST('Not impl')


def get_buffer_variable():
    global buffer_variable_counter
    buffer_variable_counter += 1
    return '_buffer_' + str(buffer_variable_counter - 1)


buffer_assignments = {}


