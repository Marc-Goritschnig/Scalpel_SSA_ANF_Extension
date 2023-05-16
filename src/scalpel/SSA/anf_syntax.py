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
            return f"λ . \n{self.term.print(lvl)}"
        if isinstance(self.term, ANF_V_FUNC):
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
        return get_indentation(lvl) + f"{self.name.print(lvl)}({' '.join([var.print(lvl) for var in self.params])})"


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

def SA(ssa_ast: SSA_AST):
    global ssa_ast_global
    ssa_ast_global = ssa_ast
    return SA_PS(ssa_ast.procs, SA_BS(ssa_ast.blocks, ANF_E_APP([], ANF_V_VAR(ssa_ast.blocks[0].label.label))))


def SA_PS(ps: [SSA_P], inner_term):
    p: SSA_P = ps[0]
    if len(ps) == 0:
        return inner_term
    elif len(ps) == 1:
        let_rec = ANF_E_LETREC(SA_V(p.name), SA_BS(p.blocks, ANF_E_APP([], ANF_V_VAR(p.blocks[0].label.label))), inner_term)
    else:
        let_rec = ANF_E_LETREC(SA_V(p.name), SA_BS(p.blocks, ANF_E_APP([], ANF_V_VAR(p.blocks[0].label.label))), SA_PS[1:])

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
        let_rec = ANF_E_LETREC(SA_V(b.label), func,
                               inner_call)
    else:
        let_rec = ANF_E_LETREC(SA_V(b.label), func,
                           SA_BS(bs[1:], inner_call))

    #for b in bs[1:]:
    #    block_vars = [SA_V(phi_var) for phi_var in get_phi_vars_in_block(b)]
    #    let_rec.add_entry(SA_V(b.label), ANF_V_FUNC(block_vars, SA_ES(b, b.terms)))
    return let_rec


def SA_ES(b: SSA_B, terms: [SSA_E]):
    global buffer_variable_counter

    if len(terms) == 0: return ANF_V_UNIT()
    term = terms[0]
    if term is None: return ANF_V_UNIT()

    if isinstance(term, SSA_E_ASS):
        return ANF_E_LET(SA_V(term.var), SA_V(term.value), SA_ES(b, terms[1:]))
    if isinstance(term, SSA_E_GOTO):
        print(get_block_by_id(ssa_ast_global, term.label).label.print(0))
        return ANF_E_APP(get_phi_vars_for_jump(b, get_block_by_id(ssa_ast_global, term.label)), SA_V(term.label))
    if isinstance(term, SSA_E_ASS_PHI):
        return SA_ES(b, terms[1:])
    if isinstance(term, SSA_E_RET):
        return SA_V(term.func_call)
    if isinstance(term, SSA_E_IF_ELSE):
        return ANF_E_IF(SA_V(term.test), SA_ES(b, [term.term_if]), SA_ES(b, [term.term_else]))
    if isinstance(term, SSA_V_FUNC_CALL):
        node = ANF_E_LET(ANF_V_VAR('_'), SA_V(term), SA_ES(b, terms[1:]))
        return node
    print("not impl", term)
    return ANF_E_APP([], SA_V('terms'))

def SA_V(var: SSA_V):
    if isinstance(var, SSA_V_VAR):
        return ANF_V_VAR(var.name)
    if isinstance(var, SSA_V_CONST):
        return ANF_V_CONST(var.value)
    if isinstance(var, SSA_L):
        return ANF_V_CONST(var.label)
    if isinstance(var, SSA_V_FUNC_CALL):
        return ANF_E_APP([SA_V(par) for par in var.args], SA_V(var.name))
    return ANF_V_CONST('Not impl')
