from __future__ import annotations
from src.scalpel.SSA.ssa_syntax import *

import re

font = {'lambda_sign': 'λ'}
debug_mode = False

function_mapping = {
    '_And': '%s and %s',
    '_Or': '%s or %s',
    '_Add': '%s + %s',
    '_Sub': '%s - %s',
    '_Mult': '%s * %s',
    '_MatMult ': 'unknown',
    '_Div': '%s / %s',
    '_Mod ': '%s % %s',
    '_Pow': '%s ** %s',
    '_LShift': '%s << %s',
    '_RShift': '%s >> %s',
    '_BitOr': '%s | %s',
    '_BitXor': '%s ^ %s',
    '_BitAnd': '%s & %s',
    '_FloorDiv': '%s // %s',
    '_Invert': '~%s',
    '_Not': 'not %s',
    '_UAdd': '+%s',
    '_USub': '-%s',
    '_Eq': '%s == %s',
    '_NotEq': '%s != %s',
    '_Lt': '%s < %s',
    '_LtE': '%s <= %s',
    '_Gt': '%s > %s',
    '_GtE': '%s >= %s',
    '_Is': '%s is %s',
    '_IsNot': '%s is not %s',
    '_In': '%s in %s',
    '_NotIn': '%s not in %s'
}

class ANFNode:
    def __init__(self):
        pass

    def print(self, lvl = 0):
        return 'not implemented'

    def enable_print_ascii(self):
        global font
        font = {'lambda_sign': 'lambda '}

    def enable_print_code(self):
        global font
        font = {'lambda_sign': 'λ'}

    def get_prov_info(self, prov_info):
        return ''

    def parse_anf_to_python(self, assignments, lvl=0):
        return None


class ANF_EV(ANFNode):
    def __init__(self):
        super().__init__()

    def print(self, lvl = 0):
        return ''

    def get_prov_info(self, prov_info):
        return ''

    def parse_anf_to_python(self, assignments, lvl=0):
        return None


class ANF_E(ANF_EV):
    def __init__(self):
        super().__init__()

    def print(self, lvl = 0):
        return ''

    def get_prov_info(self, prov_info):
        return ''

    def parse_anf_to_python(self, assignments, lvl=0):
        return None

class ANF_E_APP(ANF_E):
    def __init__(self, params: [ANF_V], name: ANF_V):
        super().__init__()
        self.params: [ANF_V] = params
        self.name: ANF_V = name

    def print(self, lvl = 0, prov_info: str = ''):
        return get_indentation(lvl) + f"{self.name.print(lvl)} {' '.join([var.print(lvl) for var in self.params])}"

    def get_prov_info(self, prov_info):
        return 'f' + self.name.get_prov_info(None) + (';' if len(self.params) > 0 else '') + ';'.join([var.get_prov_info(None) for var in self.params])

    def parse_anf_to_python(self, assignments, lvl=0):
        if isinstance(self.name, ANF_V_CONST):
            if re.match('L([0-9]|_)*', self.name.value):
                if self.name.value in assignments:
                    return assignments[self.name.value].parse_anf_to_python(assignments, lvl)
        if isinstance(self.name, ANF_V_VAR):
            if self.name.name in function_mapping:
                return get_indentation(lvl) + (function_mapping[self.name.name] % tuple([p.parse_anf_to_python(assignments, 0) for p in self.params]))
        return get_indentation(lvl) + self.name.parse_anf_to_python(assignments) + '(' + ','.join([p.parse_anf_to_python(assignments, 0) for p in self.params]) + ')'

class ANF_E_LET(ANF_E):
    def __init__(self, var: ANF_V, term1: ANF_E, term2: ANF_E):
        super().__init__()
        self.var: ANF_V = var
        self.term1: ANF_E = term1
        self.term2: ANF_E = term2

    def print(self, lvl = 0, prov_info: str = ''):
        return get_indentation(lvl) + f"let {self.var.print(lvl + 1)} = {self.term1.print(0)} in \n{self.term2.print(lvl + 1)}"

    def get_prov_info(self, prov_info):
        return 'let;' + self.var.get_prov_info(None) + ';=;' + self.term1.get_prov_info(None) + ';in\n' + self.term2.get_prov_info(None)

    def parse_anf_to_python(self, assignments, lvl=0):
        name = self.var.name
        if name == '_':
            return get_indentation(lvl) + self.term1.parse_anf_to_python(assignments) + '\n' + self.term2.parse_anf_to_python(assignments, lvl)
        elif name.startswith('_buffer_'):
            assignments[name] = self.term1
            return self.term2.parse_anf_to_python(assignments, lvl)
        return get_indentation(lvl) + self.var.parse_anf_to_python(assignments) + ' = ' + self.term1.parse_anf_to_python(assignments) + '\n' + self.term2.parse_anf_to_python(assignments, lvl)

class ANF_E_LETREC(ANF_E):
    def __init__(self, var: ANF_V, term1: ANF_EV, term2: ANF_E):
        super().__init__()
        self.var: ANF_V = var
        self.term1: ANF_EV = term1
        self.term2: ANF_E = term2

    def print(self, lvl=0, prov_info: str = ''):
        # assignments = ('\n' + get_indentation(lvl + 1)).join(v.print(lvl + 2) + ' = ' + t.print(lvl+2) for v, t in zip(self.var, self.term1))
        if isinstance(self.term1, ANF_E_LETREC) or isinstance(self.term1, ANF_E_LET):
            return get_indentation(lvl) + 'letrec ' + self.var.print(lvl + 1) + ' = ' + '\n' + self.term1.print(lvl + 1) + '\n' + get_indentation(lvl) + 'in\n' + self.term2.print(lvl + 1)
        else:
            return get_indentation(lvl) + 'letrec ' + self.var.print(lvl + 1) + ' = ' + self.term1.print(lvl + 1) + '\n' + get_indentation(lvl) + 'in\n' + self.term2.print(lvl + 1)

    def get_prov_info(self, prov_info):
        if isinstance(self.term1, ANF_E_LETREC) or isinstance(self.term1, ANF_E_LET):
            return 'letrec;' + self.var.get_prov_info(None) + ';=\n' + self.term1.get_prov_info(None) + '\nin\n' + self.term2.get_prov_info(None)
        else:
            return 'letrec;' + self.var.get_prov_info(None) + ';=;' + self.term1.get_prov_info(None) + '\nin\n' + self.term2.get_prov_info(None)

    def parse_anf_to_python(self, assignments, lvl=0):

        ## Check if was For loop
        #if self.var.name == 'L1': #  re.match('L[0-9]*]', self.var.name):
        #    ass_iter = self.term1
        #    iter = ass_iter.term1.parse_anf_to_python(assignments, 0)
        #    ass_i = self.term2
        #    i_var = ass_i.var.parse_anf_to_python(assignments, 0)
        #    return 'for ' + i_var + ' in ' + iter

        if re.match(r'L([0-9]|_)*', self.var.name):
            assignments[self.var.name] = self.term1.term
            return self.term2.parse_anf_to_python(assignments, lvl)

        if isinstance(self.var, ANF_V_VAR):
            if self.var.name.startswith(block_identifier) and isinstance(self.term2, ANF_E_APP):
                if self.term2.name.name == self.var.name:
                    # L1 = XXX in L1
                    # Return just XXX and store XXX if still L1 is called somewhere else
                    assignments[self.var.name] = self.term2
                    return self.term1.parse_anf_to_python(assignments, lvl, False)
        elif isinstance(self.term2, ANF_V_FUNC):
            return get_indentation(lvl) + 'def ' + self.var.print(0, None) + self.term1.parse_anf_to_python(assignments, lvl + 1) + '\n' + self.term2.parse_anf_to_python(assignments, lvl)

        vars = get_function_parameter_recursive(self.term1)
        next_term = get_next_non_function_term(self.term1)
        return get_indentation(lvl) + 'def ' + self.var.print(0, None) + '(' + ','.join(vars) + '):\n' + next_term.parse_anf_to_python(assignments, lvl + 1) + '\n' + self.term2.parse_anf_to_python(assignments, lvl)


def get_function_parameter_recursive(next):
    if isinstance(next, ANF_V_FUNC):
        if next.input_var is not None:
            return [next.input_var.print(0, None)] + get_function_parameter_recursive(next.term)
    return []


def get_next_non_function_term(next):
    if isinstance(next, ANF_V_FUNC):
        return get_next_non_function_term(next.term)
    else:
        return next


class ANF_E_IF(ANF_E):
    def __init__(self, test: ANF_V_VAR, term_if: ANF_E, term_else: ANF_E):
        super().__init__()
        self.test: ANF_V_VAR = test
        self.term_if: ANF_E = term_if
        self.term_else: ANF_E = term_else

    def print(self, lvl = 0, prov_info: str = ''):
        return get_indentation(lvl) + f"if {self.test.print(0)} then \n{self.term_if.print(lvl + 1)} \n{get_indentation(lvl)}else\n{self.term_else.print(lvl + 1)}"

    def get_prov_info(self, prov_info):
        return 'if;' + self.test.get_prov_info(None) + ';then\n' + self.term_if.get_prov_info(None) + '\nelse\n' + self.term_else.get_prov_info(None)

    def parse_anf_to_python(self, assignments, lvl=0):
        return get_indentation(lvl) + 'if ' + self.test.parse_anf_to_python(assignments, lvl) + ':\n' + self.term_if.parse_anf_to_python(assignments, lvl + 1) + '\nelse:\n' + self.term_if.parse_anf_to_python(assignments, lvl + 1) + '\n'

class ANF_V(ANF_EV):
    def __init__(self):
        super().__init__()

    def print(self, lvl = 0, prov_info: str = ''):
        return f""

    def get_prov_info(self, prov_info):
        return ''

    def parse_anf_to_python(self, assignments, lvl=0):
        return get_indentation(lvl) + 'ANF_V'

class ANF_V_CONST(ANF_V):
    def __init__(self, value: str):
        super().__init__()
        self.value: str = value

    def print(self, lvl = 0, prov_info: str = ''):
        return f"{self.value}"

    def get_prov_info(self, prov_info):
        return 'c'

    def parse_anf_to_python(self, assignments, lvl=0):
        return get_indentation(lvl) + self.value

class ANF_V_VAR(ANF_V):
    def __init__(self, name: str):
        super().__init__()
        self.name: str = name

    def print(self, lvl = 0, prov_info: str = ''):
        return f"{self.name}"

    def get_prov_info(self, prov_info):
        return 'v'

    def parse_anf_to_python(self, assignments, lvl=0):
        if self.name in assignments:
            return get_indentation(lvl) + assignments[self.name].parse_anf_to_python(assignments, lvl)
        idx = self.name.rfind('_')
        if idx == -1:
            idx = len(self.name)
        name = self.name[0:idx]
        return get_indentation(lvl) + name

class ANF_V_UNIT(ANF_V):
    def __init__(self):
        super().__init__()

    def print(self, lvl = 0, prov_info: str = ''):
        return get_indentation(lvl) + "unit"

    def get_prov_info(self, prov_info):
        return 'u'

    def parse_anf_to_python(self, assignments, lvl=0):
        return ''

class ANF_V_FUNC(ANF_V):
    def __init__(self, input_var: ANF_V, term: ANF_EV):
        super().__init__()
        self.input_var: ANF_V = input_var
        self.term: ANF_EV = term

    def print(self, lvl = 0, prov_info: str = ''):
        if self.input_var is None:
            if issubclass(type(self.term), ANF_V):
                return f"{font['lambda_sign']} . {self.term.print(lvl)}"
            return f"{font['lambda_sign']} . \n{self.term.print(lvl)}"
        if issubclass(type(self.term), ANF_V):
            return f"{font['lambda_sign']}{self.input_var.print(0)} . {self.term.print(lvl)}"
        return f"{font['lambda_sign']}{self.input_var.print(0)} . \n{self.term.print(lvl)}"

    def get_prov_info(self, prov_info):
        if self.input_var is None:
            if issubclass(type(self.term), ANF_V):
                return 'lambda;.;' + self.term.get_prov_info(None)
            return 'lambda;.\n' + self.term.get_prov_info(None)
        if issubclass(type(self.term), ANF_V):
            return 'lambda;' + self.input_var.get_prov_info(None) + ';.;' + self.term.get_prov_info(None)
        return 'lambda;' + self.input_var.get_prov_info(None) + ';.\n' + self.term.get_prov_info(None)

    def parse_anf_to_python(self, assignments, lvl=0, print_variables=True):
        if not print_variables:
            return self.term.parse_anf_to_python(assignments, lvl)
        vars = get_function_parameter_recursive(self.term)
        next_term = get_next_non_function_term(self.term)
        if self.input_var is None:
            return '(' + ','.join(vars) + '):\n' + next_term.parse_anf_to_python(assignments, lvl)
        vars += [self.input_var.parse_anf_to_python(assignments)]
        return '(' + ','.join(vars) + '):\n' + next_term.parse_anf_to_python(assignments, lvl)


def get_indentation(nesting_lvl):
    return '    ' * nesting_lvl


def parse_ssa_to_anf(ssa: SSA_AST, debug: bool):
    global debug_mode
    debug_mode = debug
    return SA(ssa)


# Global reference of the SSA AST to be transformed
ssa_ast_global: SSA_AST = None

# Prefix of block labels from SSA
block_identifier = 'L'

# Buffer variables mapped to ANF nodes to replace more complex code due to only values being allowed to be used in function calls
buffer_assignments = {}
buffer_variable_counter = 0

# Keywords to be ignored when parsing ANF code due to special handling
keywords = ['let', 'letrec', 'lambda', 'unit', 'if', 'then', 'else', 'in']


# Transform SSA AST into ANF AST
def SA(ssa_ast: SSA_AST):
    global ssa_ast_global
    ssa_ast_global = ssa_ast

    # Transform all procedures of the SSA AST and put the call of the first block as inner most term
    return SA_PS(ssa_ast.procs, SA_BS(ssa_ast.blocks, ANF_E_APP([], ANF_V_VAR(block_identifier + str(get_first_block_in_proc(ssa_ast.blocks).label.label)))))


# Transforms a list of procedures putting the inner_term inside the innermost let/rec
def SA_PS(ps: [SSA_P], inner_term):
    # When there is no procedure we return the inner term
    if len(ps) == 0:
        return inner_term

    # If we have the last procedure we return a letrec of this proc using the inner term
    p: SSA_P = ps[0]

    if len(ps) == 1:
        first_term = SA_BS(p.blocks, ANF_E_APP([], ANF_V_VAR(block_identifier + get_first_block_in_proc(p.blocks).label.label)))

        args = p.args[::-1]
        while len(args) > 0:
            first_term = ANF_V_FUNC(SA_V(args[0]), first_term)
            args = args[1:]

        let_rec = ANF_E_LETREC(SA_V(p.name), first_term, inner_term)
    # If we have still more than one procedure we return a letrec of this proc using a recursive call to build the other procs as inner term
    else:
        first_term = SA_BS(p.blocks, ANF_E_APP([], ANF_V_VAR(block_identifier + get_first_block_in_proc(p.blocks).label.label)))

        args = p.args
        while len(args) > 0:
            first_term = ANF_V_FUNC(SA_V(args[0]), first_term)
            args = args[1:]

        let_rec = ANF_E_LETREC(SA_V(p.name), first_term, SA_PS(ps[1:], inner_term))

    return let_rec


# Transform a list of SSA blocks
def SA_BS(bs: [SSA_B], inner_call):
    if len(bs) == 0:
        return inner_call
    b: SSA_B = bs[0]
    block_vars = [SA_V(phi_var) for phi_var in get_phi_vars_in_block(b)]

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
        let_rec = ANF_E_LETREC(ANF_V_CONST(block_identifier + b.label.label), func, inner_call)
    else:
        let_rec = ANF_E_LETREC(ANF_V_CONST(block_identifier + b.label.label), func, SA_BS(bs[1:], inner_call))

    return let_rec


def SA_ES(b: SSA_B, terms: [SSA_E]):
    if len(terms) == 0:
        return ANF_V_UNIT()

    term = terms[0]
    if term is None:
        return ANF_V_UNIT()

    if isinstance(term, SSA_E_ASS):
        unwrap_inner_applications_naming(term.value)
        return unwrap_inner_applications_let_structure(term.value, ANF_E_LET(SA_V(term.var), SA_V(term.value), SA_ES(b, terms[1:])))
    if isinstance(term, SSA_E_GOTO):
        return ANF_E_APP([SA_V(arg) for arg in get_phi_vars_for_jump(b, get_block_by_id(ssa_ast_global, term.label.label))], ANF_V_CONST(block_identifier + term.label.label))
    if isinstance(term, SSA_E_ASS_PHI):
        return SA_ES(b, terms[1:])
    if isinstance(term, SSA_E_RET):
        if term.value is None:
            return ANF_V_UNIT()
        unwrap_inner_applications_naming(term.value)
        return unwrap_inner_applications_let_structure(term.value, SA_V(term.value))
    if isinstance(term, SSA_E_IF_ELSE):
        unwrap_inner_applications_naming(term.test, True)
        return unwrap_inner_applications_let_structure(term.test, ANF_E_IF(SA_V(term.test, True), SA_ES(b, [term.term_if]), SA_ES(b, [term.term_else])), True)
    if issubclass(type(term), SSA_V):
        unwrap_inner_applications_naming(term)
        return unwrap_inner_applications_let_structure(term, ANF_E_LET(ANF_V_CONST('_'), SA_V(term), SA_ES(b, terms[1:])))

    return ANF_E_APP([], ANF_V_CONST('Not-Impl'))


def unwrap_inner_applications_let_structure(var: SSA_V, inner, unwrap_var: bool = False):
    if isinstance(var, SSA_V_FUNC_CALL):
        if unwrap_var:
            name = buffer_assignments[var]
            inner = unwrap_inner_applications_let_structure(var, ANF_E_LET(ANF_V_VAR(name), SA_V(var), inner))
        else:
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


# Transform values from SSA to ANF
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


# Get a new unique buffer variable
def get_buffer_variable():
    global buffer_variable_counter
    buffer_variable_counter += 1
    return '_buffer_' + str(buffer_variable_counter - 1)


# Print the ANF tree including the provenance information right aligned to the code per line
def print_anf_with_prov_info(anf_parent: ANFNode):
    out = anf_parent.print()
    prov = anf_parent.get_prov_info(None)
    max_chars = max([len(line) + line.count('\t') * 3 for line in out.split('\n')]) + 2
    return '\n'.join([line + (max_chars - len(line) - line.count('\t') * 3) * ' ' + '#' + info for line, info in zip(out.split('\n'), prov.split('\n'))])


# Read anf code and parse it into internal ANF AST representation
def parse_anf_from_text(code: str):
    code = code.strip()
    lines = code.split('\n')
    code_lines, info_lines = zip(*[tuple(line.split('#')) for line in lines])
    code_lines = [re.sub(' +', ' ', line) for line in code_lines]
    return parse_anf_e_from_code([word for line in code_lines for word in line.strip().split(' ')], [info_word for line in info_lines for info_word in line.strip().split(';')])


# Convert an ANF code expression to ANF AST
def parse_anf_e_from_code(code_words, info_words):
    next_word = code_words[0]
    if next_word == 'let':
        variable = ANF_V_VAR(code_words[1])
        right = parse_anf_e_from_code(code_words[3:], info_words[3:])
        _in = get_other_section_part(code_words[1:], info_words[1:], ['let', 'letrec'], ['in'])
        return ANF_E_LET(variable, right, _in)
    if next_word == 'letrec':
        variable = ANF_V_VAR(code_words[1])
        right = parse_anf_e_from_code(code_words[3:], info_words[3:])
        _in = get_other_section_part(code_words[1:], info_words[1:], ['let', 'letrec'], ['in'])
        return ANF_E_LETREC(variable, right, _in)
    if next_word == 'unit':
        return ANF_V_UNIT()
    if next_word == 'lambda':
        variable = ANF_V_VAR(code_words[1])
        rest = code_words[3:]
        rest_info = info_words[3:]
        if code_words[1] == '.':
            variable = None
            rest = code_words[2:]
            rest_info = info_words[2:]
        return ANF_V_FUNC(variable, parse_anf_e_from_code(rest, rest_info))
    if next_word == 'if':
        then_part = get_other_section_part(code_words[1:], info_words[1:], ['if'], ['then'])
        else_part = get_other_section_part(code_words[1:], info_words[1:], ['if'], ['else'])
        return ANF_E_IF(parse_anf_e_from_code(code_words[1:], info_words[1:]), then_part, else_part)

    count = 0
    while count + 1 < len(code_words) and next_word not in keywords:
        count += 1
        next_word = code_words[count]

    if count > 1:
        return ANF_E_APP([parse_anf_v_from_code(code_words[i], info_words[i]) for i in range(1, count)], parse_anf_v_from_code(code_words[0], info_words[0][1:]))
    else:
        return parse_anf_v_from_code(code_words[0], info_words[0])


# Convert an ANF code value to ANF AST
def parse_anf_v_from_code(code_word: str, info_word: str):
    if info_word == 'c':
        return ANF_V_CONST(code_word)
    if info_word == 'v':
        return ANF_V_VAR(code_word)
    if info_word.startswith('f'):
        return ANF_E_APP([], parse_anf_v_from_code(code_word, info_word[1:]))


# Get the position of the next part belonging to the given one
# Ex. We start at a "letrec" and want to find its "in"
# (letrec) xxx let xxx let xxx in xxx in xxx (in) xxx
def get_other_section_part(code_words: [str], info_words: [str], open_keys: [str], close_keys: [str]):
    indentation = 1
    idx = 0
    for i, w in enumerate(code_words):
        if w in open_keys:
            indentation += 1
        elif w in close_keys:
            indentation -= 1
        if indentation == 0:
            idx = i
            break
    return parse_anf_e_from_code(code_words[idx + 1:], info_words[idx + 1:])


def parse_anf_to_ssa(anf_ast):
    stmts, blocks, procs = parse_anf_to_ssa2(anf_ast)
    return SSA_AST(procs, blocks)


block_phi_assignment_vars = {}
buffer_assignments_anf_ssa = {}
def parse_anf_to_ssa2(term):
    global block_phi_assignment_vars
    if isinstance(term, ANF_E_LETREC):
        if isinstance(term.var, ANF_V_VAR):
            name = term.var.name
            if re.match(r'L([0-9]|_)*', name):
                stmts1, blocks1, procs1 = parse_anf_to_ssa2(term.term1.term)
                stmts2, blocks2, procs2 = parse_anf_to_ssa2(term.term2)
                # The first innermost letrec got a simple function call in its "in" term which is artificially added from SSA to ANF to call the first Block and therefore not needed
                if isinstance(term.term2, ANF_E_APP):
                    if re.match(r'L([0-9]|_)*', term.term2.name.name):
                        stmts2, blocks2, procs2 = [], [], []
                phi_ass = []
                if name in block_phi_assignment_vars:
                    for var in block_phi_assignment_vars[name]:
                        max_idx = 0
                        for arg in block_phi_assignment_vars[name][var]:
                            idx = int(arg[arg.rfind('_')+1:])
                            max_idx = max(max_idx, idx)
                        phi_ass += [SSA_E_ASS_PHI(SSA_V_VAR(var + '_' + str(max_idx+1)), [SSA_V_VAR(arg) for arg in block_phi_assignment_vars[name][var]])]
                return [], [SSA_B(SSA_L(term.var.name[1:]), phi_ass + stmts1 + stmts2, False)] + blocks1 + blocks2, procs1 + procs2

        # Get all functions with 1 parameter at the start of the letrec describing the procs input variables
        vars = get_function_parameter_recursive(term.term1)
        next_non_func_term = get_next_non_function_term(term.term1)
        stmts1, blocks1, procs1 = parse_anf_to_ssa2(next_non_func_term)
        stmts2, blocks2, procs2 = parse_anf_to_ssa2(term.term2)
        return [], blocks2, [SSA_P(SSA_L(term.var.print(0, None)), [SSA_V_VAR(var) for var in vars], blocks1)] + procs1 + procs2
    elif isinstance(term, ANF_E_LET):
        name = term.var.print()
        # Parse the right assignment side first and check if the left side is a buffer variable
        stmts1, _      , _      = parse_anf_to_ssa2(term.term1)
        ass = [SSA_E_ASS(SSA_V_VAR(name), stmts1[0])]
        # if we have a buffer variable we keep track of it and do not include the assignment in the returned statements
        if name.startswith('_buffer_'):
            buffer_assignments_anf_ssa[name] = stmts1[0]
            ass = []
        # Parse the following statements
        stmts2, blocks2, procs2 = parse_anf_to_ssa2(term.term2)
        if name == '_':
            return stmts1 + stmts2, blocks2, procs2
        return ass + stmts2, blocks2, procs2
    elif isinstance(term, ANF_E_APP):
        name = term.name.print()
        if re.match(r'L([0-9]|_)*', name):
            if name not in block_phi_assignment_vars:
                block_phi_assignment_vars[name] = {}
            for arg in term.params:
                arg_name = get_name_from_buffer(arg.print())
                base = arg_name[0:arg_name.rfind('_')]
                if base not in block_phi_assignment_vars[name]:
                    block_phi_assignment_vars[name][base] = []
                block_phi_assignment_vars[name][base].append(arg_name)
            return [SSA_E_GOTO(SSA_L(name[1:]))], [], []
        return [SSA_V_FUNC_CALL(SSA_V_VAR(name), [SSA_V_VAR(get_name_from_buffer(arg.print())) for arg in term.params])], [], []
    elif isinstance(term, ANF_E_IF):
        stmts1, _, _ = parse_anf_to_ssa2(term.term_if)
        stmts2, _, _ = parse_anf_to_ssa2(term.term_else)
        return [SSA_E_IF_ELSE(parse_anf_to_ssa2(term.test)[0][0], stmts1[0], stmts2[0])], [], []
    elif isinstance(term, ANF_V_VAR):
        if term.name in buffer_assignments_anf_ssa:
            return [buffer_assignments_anf_ssa[term.name]], [], []
        return [SSA_V_VAR(term.name)], [], []
    elif isinstance(term, ANF_V_FUNC):
        return [], [], []
    elif isinstance(term, ANF_V_CONST):
        return [SSA_V_CONST(term.value)], [], []
    elif isinstance(term, ANF_V_UNIT):
        return [], [], []


def get_name_from_buffer(name):
    if name in buffer_assignments_anf_ssa:
        return buffer_assignments_anf_ssa[name].print(0)
    return name
