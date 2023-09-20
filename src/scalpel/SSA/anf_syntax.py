from __future__ import annotations
from scalpel.SSA.ssa_syntax import *

import re

font = {'lambda_sign': 'λ'}
debug_mode = False
comment_separator = '$'

block_call_pattern = re.compile(r'^L([0-9])+(.)*')
function_mapping_ext = {
    re.compile(r'^_new_list_([0-9])+$'): '[%s]',
    re.compile(r'^_Delete_([0-9])+$'): 'del %s',
    re.compile(r'^_new_tuple_([0-9])+$'): '(%s)',
    re.compile(r'^_new_set_([0-9])+$'): 'set(%s)'
}
 #_Raise_ _Assert _Pass _Break _Continue _new_tuple_ _new_dict_ _new_set_ _new_list_ _List_Slice(LUS) _LSD_Get _str_format3 _ADD
function_mapping = {
    '_And': '(%s and %s)',
    '_Or': '(%s or %s)',
    '_Add': '(%s + %s)',
    '_Sub': '(%s - %s)',
    '_Mult': '(%s * %s)',
    '_MatMult ': 'unknown',
    '_Div': '(%s / %s)',
    '_Mod ': '(%s % %s)',
    '_Pow': '(%s ** %s)',
    '_LShift': '(%s << %s)',
    '_RShift': '(%s >> %s)',
    '_BitOr': '(%s | %s)',
    '_BitXor': '(%s ^ %s)',
    '_BitAnd': '(%s & %s)',
    '_FloorDiv': '(%s // %s)',
    '_Invert': '(~%s)',
    '_Not': '(not %s)',
    '_UAdd': '(+%s)',
    '_USub': '(-%s)',
    '_Eq': '(%s == %s)',
    '_NotEq': '(%s != %s)',
    '_Lt': '(%s < %s)',
    '_LtE': '(%s <= %s)',
    '_Gt': '(%s > %s)',
    '_GtE': '(%s >= %s)',
    '_Is': '(%s is %s)',
    '_IsNot': '(%s is not %s)',
    '_In': '(%s in %s)',
    '_NotIn': '(%s not in %s)',
    '_LSD_Get': '%s[%s]',
    '_Raise_1': 'raise %s',
    '_Raise_2': 'raise %s from %s',
    '_Assert': 'assert (%s)',
    '_Pass': 'pass',
    '_Break': 'break',
    '_Continue': 'continue',
    '_List_Slice_L': '%s[%s:]',
    '_List_Slice_U': '%s[:%s]',
    '_List_Slice_US': '%s[:%s:%s]',
    '_List_Slice_LS': '%s[%s::%s]',
    '_List_Slice_LU': '%s[%s:%s]',
    '_List_Slice_LUS': '%s[%s:%s:%s]',
    'tuple_get': '%s[%s]'
}

# Global reference of the SSA AST to be transformed
ssa_ast_global: SSA_AST = None

# Prefix of block labels from SSA
block_identifier = 'L'

# Buffer variables mapped to ANF nodes to replace more complex code due to only values being allowed to be used in function calls
buffer_assignments = {}
buffer_variable_counter = 0

# Keywords to be ignored when parsing ANF code due to special handling
keywords = ['let', 'letrec', 'lambda', 'unit', 'if', 'then', 'else', 'in']


block_label_regex = r'^L([0-9]|_)*$'
block_phi_assignment_vars = {}
buffer_assignments_anf_ssa = {}


def reset():
    global ssa_ast_global,block_identifier,buffer_variable_counter,keywords,block_label_regex,buffer_assignments_anf_ssa,buffer_assignments,block_phi_assignment_vars
    ssa_ast_global = None
    buffer_assignments = {}
    buffer_variable_counter = 0
    block_phi_assignment_vars = {}
    buffer_assignments_anf_ssa = {}


class ANFNode:
    def __init__(self):
        self.prov_info = ''

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

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        return None

    def print_prov_ext(self):
        prov = ''
        if self.prov_info != '':
            prov = '|' + self.prov_info
        return prov

class ANF_EV(ANFNode):
    def __init__(self):
        super().__init__()

    def print(self, lvl = 0):
        return ''

    def get_prov_info(self, prov_info):
        return ''

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        return None


class ANF_E(ANF_EV):
    def __init__(self):
        super().__init__()

    def print(self, lvl = 0):
        return ''

    def get_prov_info(self, prov_info):
        return ''

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        return None

class ANF_E_APP(ANF_E):
    def __init__(self, params: [ANF_V], name: ANF_V):
        super().__init__()
        self.params: [ANF_V] = params
        self.name: ANF_V = name

    def print(self, lvl = 0, prov_info: str = ''):
        return get_indentation(lvl) + f"{self.name.print(lvl)} {' '.join([var.print(lvl) for var in self.params])}"

    def get_prov_info(self, prov_info):
        return 'f' + self.name.get_prov_info(None) + self.print_prov_ext() + (';' if len(self.params) > 0 else '') + ';'.join([var.get_prov_info(None) for var in self.params])

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        out = None
        if isinstance(self.name, ANF_V_CONST):
            if re.match('L([0-9]|_)*', self.name.value):
                if self.name.value in assignments and self.name.value not in parsed_blocks:
                    parsed_blocks.append(self.name.value)
                    out = assignments[self.name.value].parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl)
                    return postprocessing_ANF_V_to_python(self, out)
        elif isinstance(self.name, ANF_V_VAR):
            if self.name.name in function_mapping:
                out = (function_mapping[self.name.name] % tuple([p.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, 0) for p in self.params]))
            for (pattern, value) in function_mapping_ext.items():
                if pattern.match(self.name.name):
                    out = (value % ', '.join([p.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, 0) for p in self.params]))
            if re.match('L([0-9]|_)*', self.name.name):
                out = self.name.parse_anf_to_python(assignments, parsed_blocks, loop_block_names)
        if out is None:
            # Default output if nothing applies
            out = self.name.parse_anf_to_python(assignments, parsed_blocks, loop_block_names) + '(' + ','.join([p.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, 0) for p in self.params]) + ')'
        return get_indentation(lvl) + postprocessing_ANF_V_to_python(self, out)

class ANF_E_COMM(ANF_E):
    def __init__(self, text: str, term: ANF_E):
        super().__init__()
        self.text: str = text
        self.term: ANF_E = term

    def print(self, lvl = 0, prov_info: str = ''):
        return f"{self.term.print(lvl)}"

    def get_prov_info(self, prov_info):
        return self.text + ';' + self.term.get_prov_info(None)

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        out = self.term.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl)
        #if self.text.startswith('#-SSA-'):
        #    out = out.split('\n')
        #    out = [out[0] + self.text] + out[1:]
        #    out = '\n'.join(out)
        #else:
        out = get_indentation(lvl) + self.text + '\n' + out
        return post_processing_anf_to_python(out)


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

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        name = self.var.name
        if name == '_':
            return get_indentation(lvl) + self.term1.parse_anf_to_python(assignments, parsed_blocks, loop_block_names) + '\n' + self.term2.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl)
        elif name.startswith('_buffer_'):
            assignments[name] = self.term1
            return self.term2.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl)
        newline = '' if isinstance(self.term2, ANF_V_UNIT) else '\n'
        out = get_indentation(lvl) + self.var.parse_anf_to_python(assignments, parsed_blocks, loop_block_names) + ' = ' + self.term1.parse_anf_to_python(assignments, parsed_blocks, loop_block_names) + newline + self.term2.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl)
        out = "\n".join([s for s in out.split("\n") if s])
        out = post_processing_anf_to_python(out)
        return out

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

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):

        ## Check if was For loop
        #if self.var.name == 'L1': #  re.match('L[0-9]*]', self.var.name):
        #    ass_iter = self.term1
        #    iter = ass_iter.term1.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, 0)
        #    ass_i = self.term2
        #    i_var = ass_i.var.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, 0)
        #    return 'for ' + i_var + ' in ' + iter

        if re.match(block_label_regex, self.var.name):
            assignments[self.var.name] = self.term1.term
            return self.term2.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl)

        if isinstance(self.var, ANF_V_VAR):
            if self.var.name.startswith(block_identifier) and isinstance(self.term2, ANF_E_APP):
                if self.term2.name.name == self.var.name:
                    # L1 = XXX in L1
                    # Return just XXX and store XXX if still L1 is called somewhere else
                    assignments[self.var.name] = self.term2
                    return self.term1.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl, False)
        elif isinstance(self.term2, ANF_V_FUNC):
            return get_indentation(lvl) + 'def ' + self.var.print(0, None) + self.term1.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl + 1) + '\n' + '\n' + self.term2.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl)

        vars = get_function_parameter_recursive(self.term1)
        next_term = get_next_non_function_term(self.term1)
        newline = '' if isinstance(self.term2, ANF_V_UNIT) else '\n'
        return get_indentation(lvl) + 'def ' + self.var.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl) + '(' + ','.join(vars) + '):\n' + next_term.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl + 1) + newline + newline + self.term2.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl)


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

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        parsed_blocks_buffer = parsed_blocks.copy()

        # First time parsing will generate the parse also the blocks within
        if_out = (self.term_if.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl + 1))
        else_out = (self.term_else.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl + 1))

        # Second time parsing will only print the block label as function call
        if_block_label = (self.term_if.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, 0))
        else_block_label = (self.term_else.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, 0))

        # Get the block label numbers
        parsed_blocks = parsed_blocks_buffer
        goto1 = if_block_label.split('\n')[-1].strip().split('(')[0][1:]
        goto2 = else_block_label.split('\n')[-1].strip().split('(')[0][1:]

        # If the labels of gotos are i and i+1 it shows as the pattern which is generated when parsing a while loop
        # Otherwise it would be i and i+2 because the block i+1 would be after the if-else block
        if (goto2 == '' or int(goto1) + 1 == int(goto2)) and ('L' + str(int(goto1) - 1) + '(' in if_out):
            if_out = '\n'.join(if_out.split('\n')[0:-1])
            return (get_indentation(lvl) + 'while ' + self.test.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl) + ':\n'
                    + if_out + '\n' + remove_indentation(else_out, 1) + '\n')

        # Prevent that the block after if-else gets printed into then if part - then print it separately after both parts
        # Add the block label from the one after the if-else block to the parse blocks - therefore it will not be parsed into the output
        parsed_blocks.append('L' + str(int(goto1) + 1))
        if_out = (self.term_if.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl + 1))
        else_out = (self.term_else.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl + 1))

        # Remove the block label function calls which are at the end of the parsed codes if the program does not stop there
        # If so there would be no label and there should not be the last line removed
        if_lines = if_out.split('\n')
        while if_lines[-1] == '':
            if_lines = if_lines[0:-1]
        else_lines = else_out.split('\n')
        while else_lines[-1] == '':
            else_lines = else_lines[0:-1]
            # If there is no else branch we will end up with nothing and need to handle this
            if len(else_lines) == 0:
                else_lines = ['']
                break
        if block_call_pattern.match(if_lines[-1].strip()):
            if_out = '\n'.join(if_lines[0:-1])
        if block_call_pattern.match(else_lines[-1].strip()):
            else_out = '\n'.join(else_lines[0:-1])
        post_if_else = assignments['L' + str(int(goto1) + 1)].parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl) if 'L' + str(int(goto1) + 1) in assignments else ''

        # If there is no content left in the else branch do not print any else content
        else_out = '\n' if else_out == '' else ('\n' + get_indentation(lvl) + 'else:\n' + else_out + '\n' )
        out = get_indentation(lvl) + 'if ' + self.test.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, 0) + ':\n' + if_out + else_out + post_if_else
        return out

class ANF_V(ANF_EV):
    def __init__(self):
        super().__init__()

    def print(self, lvl = 0, prov_info: str = ''):
        return f""

    def get_prov_info(self, prov_info):
        return ''

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        return get_indentation(lvl) + 'ANF_V'

class ANF_V_CONST(ANF_V):
    def __init__(self, value: str):
        super().__init__()
        self.value: str = value

    def print(self, lvl = 0, prov_info: str = ''):
        return f"{self.value}"

    def get_prov_info(self, prov_info):
        return 'c' + self.print_prov_ext()

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        #value = normalize_name(self.value)
        return get_indentation(lvl) + postprocessing_ANF_V_to_python(self, self.value)

def postprocessing_ANF_V_to_python(n: ANFNode, out: str):
    if n.prov_info == 'RET':
        return 'return ' + out
    return out

class ANF_V_VAR(ANF_V):
    def __init__(self, name: str):
        super().__init__()
        self.name: str = name

    def print(self, lvl = 0, prov_info: str = ''):
        return f"{self.name}"

    def get_prov_info(self, prov_info):
        return 'v' + self.print_prov_ext()

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        if self.name in assignments:
            return get_indentation(lvl) + postprocessing_ANF_V_to_python(self, assignments[self.name].parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl))
        name = normalize_name(self.name)
        return get_indentation(lvl) + postprocessing_ANF_V_to_python(self, name)


def normalize_name(name: str):
    idx = name.rfind('_')
    if idx == -1:
        idx = len(name)
    return name[0:idx]


class ANF_V_UNIT(ANF_V):
    def __init__(self):
        super().__init__()

    def print(self, lvl = 0, prov_info: str = ''):
        return get_indentation(lvl) + "unit"

    def get_prov_info(self, prov_info):
        return 'u'

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
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

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0, print_variables=True):
        if not print_variables:
            return self.term.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl)
        vars = get_function_parameter_recursive(self.term)
        next_term = get_next_non_function_term(self.term)
        if self.input_var is None:
            return '(' + ','.join(vars) + '):\n' + next_term.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl)
        vars += [self.input_var.parse_anf_to_python(assignments, parsed_blocks, loop_block_names)]
        return '(' + ','.join(vars) + '):\n' + next_term.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl)


def get_indentation(nesting_lvl):
    return '    ' * nesting_lvl


def remove_indentation(code, i):
    new_code = ''
    for c in code.split('\n'):
        new_code += c[4:] + '\n'
    return new_code


def parse_ssa_to_anf(ssa: SSA_AST, debug: bool):
    global debug_mode
    reset()
    debug_mode = debug
    return SA(ssa)


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
        x = SA_V(term.value)
        x.prov_info = 'RET'
        return unwrap_inner_applications_let_structure(term.value, x)
    if isinstance(term, SSA_E_IF_ELSE):
        unwrap_inner_applications_naming(term.test, True)
        return unwrap_inner_applications_let_structure(term.test, ANF_E_IF(SA_V(term.test, True), SA_ES(b, [term.term_if]), SA_ES(b, [term.term_else])), True)
    if issubclass(type(term), SSA_V):
        unwrap_inner_applications_naming(term)
        return unwrap_inner_applications_let_structure(term, ANF_E_LET(ANF_V_CONST('_'), SA_V(term), SA_ES(b, terms[1:])))
    if issubclass(type(term), SSA_E_COMM):
        return ANF_E_COMM(term.text, SA_ES(b, terms[1:]))
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
    return '\n'.join([line + (max_chars - len(line) - line.count('\t') * 3) * ' ' + comment_separator + info for line, info in zip(out.split('\n'), prov.split('\n'))])


# Read anf code and parse it into internal ANF AST representation
def parse_anf_from_text(code: str):
    code = code.strip()
    lines = code.split('\n')
    code_lines, info_lines = zip(*[tuple(line.split(comment_separator)) for line in lines])
    code_lines = [re.sub(' +', ' ', line) for line in code_lines]
    code_words = [word if i % 2 == 0 else (('\'' + part + '\'') if j == 0 else None) for line in code_lines for i, part in enumerate(line.strip().split('\'')) for j, word in enumerate(part.strip().split(' '))  if part != ' ']
    code_words = list(filter(lambda e: e is not None, code_words))
    aa = parse_anf_e_from_code(code_words, [info_word for line in info_lines for info_word in line.strip().split(';')])
    return aa

# Convert an ANF code expression to ANF AST
def parse_anf_e_from_code(code_words, info_words):
    next_word = code_words[0]

    # Found a comment within provenance information
    if info_words[0][0] == '#':
        return ANF_E_COMM(info_words[0], parse_anf_e_from_code(code_words[0:], info_words[1:]))
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
def parse_anf_v_from_code(code_word: str, info_word_with_prov: str):
    info_word_parts = info_word_with_prov.split('|')
    info_word = info_word_parts[0]

    n = None
    if info_word == 'c':
        n = ANF_V_CONST(code_word)
    if info_word == 'v':
        n = ANF_V_VAR(code_word)
    if info_word.startswith('f'):
        n = ANF_E_APP([], parse_anf_v_from_code(code_word, info_word[1:]))
    if n is not None and len(info_word_parts) > 1:
        n.prov_info = info_word_parts[1]
    return n

# Get the position of the next part belonging to the given one
# Ex. We start at a "letrec" and want to find its "in"
# (letrec) xxx let xxx let xxx in xxx in xxx (in) xxx
def get_other_section_part(code_words: [str], info_words: [str], open_keys: [str], close_keys: [str]):
    indentation = 1
    idx = 0
    comment_offset = 0
    for i, w in enumerate(code_words):
        if len(info_words[i + comment_offset]) > 0:
            if info_words[i + comment_offset][0] == '#':
                comment_offset += 1
        if w in open_keys:
            indentation += 1
        elif w in close_keys:
            indentation -= 1
        if indentation == 0:
            idx = i
            break

    return parse_anf_e_from_code(code_words[idx + 1:], info_words[idx + 1 + comment_offset:])


def parse_anf_to_ssa(anf_ast):
    stmts, blocks, procs = parse_anf_to_ssa2(anf_ast)
    return SSA_AST(procs, blocks)


def parse_anf_to_ssa2(term):
    global block_phi_assignment_vars
    if isinstance(term, ANF_E_LETREC):
        if isinstance(term.var, ANF_V_VAR):
            name = term.var.name
            if re.match(block_label_regex, name):
                stmts1, blocks1, procs1 = parse_anf_to_ssa2(term.term1.term)
                stmts2, blocks2, procs2 = parse_anf_to_ssa2(term.term2)

                # Replace single constants which are return values with a SSA RET object
                for idx, st in enumerate(stmts1):
                    if isinstance(st, SSA_V_CONST):
                        stmts1[idx] = SSA_E_RET(st)
                for idx, st in enumerate(stmts1):
                    if isinstance(st, SSA_V_CONST):
                        stmts1[idx] = SSA_E_RET(st)

                # The first innermost letrec got a simple function call in its "in" term which is artificially added from SSA to ANF to call the first Block and therefore not needed
                if isinstance(term.term2, ANF_E_APP):
                    if re.match(block_label_regex, term.term2.name.name):
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

        # Replace single constants which are return values with a SSA RET object
        for idx, st in enumerate(stmts1):
            if isinstance(st, SSA_V_CONST):
                stmts1[idx] = SSA_E_RET(st)
        for idx, st in enumerate(stmts1):
            if isinstance(st, SSA_V_CONST):
                stmts1[idx] = SSA_E_RET(st)

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
        if re.match(block_label_regex, name):
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
        stmts1 = stmts1[0] if len(stmts1) > 0 else SSA_E_RET(None)
        stmts2 = stmts2[0] if len(stmts2) > 0 else SSA_E_RET(None)
        return [SSA_E_IF_ELSE(parse_anf_to_ssa2(term.test)[0][0], stmts1, stmts2)], [], []
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


def post_processing_anf_to_python(code):
    output = ''
    lines = code.split('\n')
    skip = 0

    # iterate over ast and check comments for markers like aug assign then the next sasignment should be changed to an aug assign
    for i in range(len(lines)):
        line = lines[i]
        line_strip = line.strip()
        if skip > 0:
            skip -= 1
            continue
        if '#-SSA-AugAssign' in line:
            output += re.sub(r'(\w+)\s*=\s*(|.)\1\s*(.)\s*(.*)', r'\1 \3= \2\4', lines[i + 1]) + '\n'
            skip = 1
        elif line_strip.startswith('#-SSA-AnnAssign'):
            indentation = len(re.findall(r"^ *", lines[i + 1])[0])
            _, t, simple = line_strip.split('|')
            p1, p2 = lines[i + 1].strip().split(' = ')
            new_line = (indentation * ' ') + p1 + ': ' + t + ' = ' + p2 + '\n'
            if simple == '0':
                new_line = (indentation * ' ') + '(' + p1 + '): ' + t + ' = ' + p2 + '\n'
            output += new_line
            skip = 1
        elif '#-SSA-FOR' in line and len(lines) > i + 5:
            indentation = len(re.findall(r"^ *", lines[i + 1])[0])
            _, arr = re.sub(r'^ *(.*)\s=\s(.*)', r'\1;\2', lines[i + 1]).split(';')
            variable, _ = re.sub(r'^ *(.*)\s=\s(.*)', r'\1;\2', lines[i + 2]).split(';')
            indentation2 = len(re.findall(r"^ *", lines[i + 5])[0])
            j = 5
            while lines[i + j].startswith(indentation2 * ' '):
                j += 1
                if i + j == len(lines):
                    break
            loop_body = lines[i + 5:j-1]

            code_after = []
            if i + j < len(lines):
                code_after = lines[i + j:]

            lines = lines[:i] + [indentation * ' ' + 'for ' + variable + ' in ' + arr + ':\n'] + loop_body + code_after
            return post_processing_anf_to_python('\n'.join(lines))
        elif '#-SSA-IfExp' in line:
            indentation = len(re.findall(r"^ *", lines[i + 2])[0])
            if_term = re.sub(r'^(.*)if (.*):(.)*', r'\2',lines[i + 1])
            ssa_var, if_val = re.sub(r'^ *(.*)\s=\s(.*)', r'\1;\2',lines[i + 2]).split(';')
            j = 3
            while not (lines[i + j].startswith(indentation * ' ' + ssa_var)):
                j += 1
            else_block = [line[4:] for line in lines[i+6:i+j]]
            else_val = re.sub(r'^ *(.*)\s=\s(.*)', r'\2', lines[i + j])
            j += 1
            while not (lines[i + j].startswith((indentation - 4) * ' ') and ssa_var in lines[i + j]):
                j += 1
                if i + j == len(lines):
                    break
            if_exp = if_val + ' if ' + if_term + ' else ' + else_val
            line = lines[i + j].replace(ssa_var, if_exp)

            code_after = []
            if i+j+1 < len(lines):
                code_after = lines[i+j+1:]

            lines = lines[:i] + [line] + else_block + code_after
            return post_processing_anf_to_python('\n'.join(lines))
        else:
            output += line + '\n'
    return output
