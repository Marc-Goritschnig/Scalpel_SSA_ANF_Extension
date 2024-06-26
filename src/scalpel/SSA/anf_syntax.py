from __future__ import annotations

import ast

from scalpel.SSA.ssa_syntax import *

import re

from scalpel.functions import trim_double_spaces
from scalpel.config import PROV_INFO_EXT_CHAR, PROV_INFO_SPLIT_CHAR, PROV_INFO_MARKER, ANF_BUFFER_VAR_NAME

font = {'lambda_sign': 'λ'}
debug_mode = False
no_pos_tracking = False

# Prefix of block labels from SSA
block_identifier = 'L'

VAR_NAME_REGEX = '[a-zA-Z0-9_]*'
block_call_pattern = re.compile(r'^L([0-9])+(.)*')
function_mapping_ext = {
    re.compile(r'^_new_list_([0-9])+$'): '[%s]',
    re.compile(r'^_Delete_([0-9])+$'): 'del %s',
    re.compile(r'^_new_tuple_([0-9])+$'): '(%s)',
    re.compile(r'^_new_set_([0-9])+$'): '{%s}',
    re.compile(r'^_new_dict_([0-9])+$'): lambda params: '{' + ','.join(
        [str(p) if i % 2 == 0 else (': ' + str(p)) for i, p in enumerate(params)]).replace(',:', ':') + '}'
}
# _Raise_ _Assert _Pass _Break _Continue _new_tuple_ _new_dict_ _new_set_ _new_list_ _List_Slice(LUS) _LSD_Get _str_format3 _ADD
function_mapping = {
    '_And': '(%s and %s)',
    '_Or': '(%s or %s)',
    '_Add': '(%s + %s)',
    '_Sub': '(%s - %s)',
    '_Mult': '(%s * %s)',
    '_MatMult ': 'unknown',
    '_Div': '(%s / %s)',
    '_Mod': '(%s %% %s)',
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
    '_Raise': 'raise %s',
    '_Raise_2': 'raise %s from %s',
    '_Assert': 'assert (%s)',
    '_Assert_2': 'assert (%s, %s)',
    '_Pass': 'pass',
    '_Break': 'break',
    '_Continue': 'continue',
    '_List_Slice': '%s[:]',
    '_List_Slice_L': '%s[%s:]',
    '_List_Slice_U': '%s[:%s]',
    '_List_Slice_US': '%s[:%s:%s]',
    '_List_Slice_LS': '%s[%s::%s]',
    '_List_Slice_LU': '%s[%s:%s]',
    '_List_Slice_LUS': '%s[%s:%s:%s]',
    '_List_Slice_S': '%s[::%s]',
    '_Tuple_Get': '%s[%s]',
    '_Starred': '*%s',
    '_Starred2': '**%s'
}

# Global reference of the SSA AST to be transformed
ssa_ast_global: SSA_AST = None

# Buffer variables mapped to ANF nodes to replace more complex code due to only values being allowed to be used in function calls
buffer_assignments = {}
buffer_variable_counter = 0

# Keywords to be ignored when parsing ANF code due to special handling
keywords = ['let', 'letrec', 'lambda', 'λ', 'unit', 'if', 'then', 'else', 'in']

block_label_regex = r'^L([0-9]|_)*$'
block_phi_assignment_vars = {}
buffer_assignments_anf_ssa = {}


def reset():
    global ssa_ast_global, block_identifier, buffer_variable_counter, keywords, block_label_regex, buffer_assignments_anf_ssa, buffer_assignments, block_phi_assignment_vars
    ssa_ast_global = None
    buffer_assignments = {}
    buffer_variable_counter = 0
    block_phi_assignment_vars = {}
    buffer_assignments_anf_ssa = {}


class ANFNode:
    def __init__(self, ssa_node: SSANode = None):
        self.init(ssa_node)

    def init(self, ssa_node: SSANode = None):
        self.prov_info = ''
        self.pos_info = None
        if ssa_node is not None:
            if ssa_node.pos_info is not None:
                self.pos_info = ssa_node.pos_info
            else:
                positions = find_child_positions(ssa_node)
                if len(positions) > 0:
                    pos = Position(None)
                    for p in positions:
                        pos.lineno = min(pos.lineno, p.lineno)
                        pos.end_lineno = max(pos.end_lineno, p.end_lineno)
                        pos.col_offset = min(pos.col_offset, p.col_offset)
                        pos.end_col_offset = max(pos.end_col_offset, p.end_col_offset)
                    self.pos_info = pos

    def print(self, lvl=0):
        return 'not implemented'

    def enable_print_ascii(self):
        global font
        font = {'lambda_sign': 'lambda'}

    def enable_print_code(self):
        global font
        font = {'lambda_sign': 'λ'}

    def get_prov_info(self, prov_info):
        return ''

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        return None

    def print_prov_ext(self):
        prov = ''
        if no_pos_tracking:
            pass
        elif not no_pos_tracking and self.pos_info is not None:
            prov += PROV_INFO_EXT_CHAR + str(self.pos_info)
        else:
            prov += PROV_INFO_EXT_CHAR
        if self.prov_info != '':
            prov += PROV_INFO_EXT_CHAR + self.prov_info
        return prov


class ANF_EV(ANFNode):
    def __init__(self, ssa_node: SSANode = None):
        super().__init__(ssa_node=ssa_node)

    def print(self, lvl=0):
        return ''

    def get_prov_info(self, prov_info):
        return ''

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        return None


class ANF_E(ANF_EV):
    def __init__(self, ssa_node: SSANode = None):
        super().__init__(ssa_node=ssa_node)

    def print(self, lvl=0):
        return ''

    def get_prov_info(self, prov_info):
        return ''

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        return None


class ANF_E_APP(ANF_E):
    def __init__(self, params: [ANF_V], name: ANF_V, ssa_node: SSANode = None, params_named: [str] = None):
        super().__init__(ssa_node=ssa_node)
        self.params: [ANF_V] = params
        self.name: ANF_V = name
        self.params_named = params_named
        if ssa_node is not None:
            if hasattr(ssa_node, 'params_named'):
                self.params_named: [str] = ssa_node.params_named

    def print(self, lvl=0, prov_info: str = ''):
        return get_indentation(lvl) + f"{self.name.print(lvl)} {' '.join([var.print(lvl) for var in self.params])}"

    def get_prov_info(self, prov_info):
        name_info = ''
        if self.params_named is not None:
            name_info = PROV_INFO_EXT_CHAR + 'names=' + ','.join(self.params_named)
        prov = 'f' + self.name.get_prov_info(None) + name_info + self.print_prov_ext() + (
            PROV_INFO_SPLIT_CHAR if len(self.params) > 0 else '') + PROV_INFO_SPLIT_CHAR.join(
            [var.get_prov_info(None) for var in self.params])
        return prov.replace('ff', 'f')

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        out = None
        if isinstance(self.name, ANF_V_CONST):
            if self.name.is_block_id:
                if self.name.value in assignments and self.name.value not in parsed_blocks:
                    parsed_blocks.append(self.name.value)
                    out = assignments[self.name.value].parse_anf_to_python(assignments, parsed_blocks, loop_block_names,
                                                                           lvl)
                    return postprocessing_ANF_V_to_python(self, out)
        elif isinstance(self.name, ANF_V_VAR):
            if self.name.name in function_mapping:
                out = (function_mapping[self.name.name] % tuple(
                    [p.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, 0) for p in self.params]))
            for (pattern, value) in function_mapping_ext.items():
                if pattern.match(self.name.name):
                    if callable(value):
                        out = value([p.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, 0) for p in
                                     self.params])
                    else:
                        out = (value % ', '.join(
                            [p.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, 0) for p in
                             self.params]))
        if out is None:
            # Default output if nothing applies
            out = self.name.parse_anf_to_python(assignments, parsed_blocks, loop_block_names) + '(' + ','.join([(
                                                                                                                    self.params_named[
                                                                                                                        idx - (
                                                                                                                                    len(self.params) - len(
                                                                                                                                self.params_named))] + '=' if self.params_named is not None and len(
                                                                                                                        self.params) - idx <= len(
                                                                                                                        self.params_named) else '') + p.parse_anf_to_python(
                assignments, parsed_blocks, loop_block_names, 0) for idx, p in enumerate(self.params)]) + ')'
        lines = postprocessing_ANF_V_to_python(self, out).split('\n')
        lines = [get_indentation(lvl) + s for s in lines]
        return '\n'.join(lines)


class ANF_E_COMM(ANF_E):
    def __init__(self, text: str, term: ANF_E, ssa_node: SSANode = None):
        super().__init__(ssa_node=ssa_node)
        self.text: str = text
        self.term: ANF_E = term

    def print(self, lvl=0, prov_info: str = ''):
        # print('comm')
        # print(self.text)
        # print(get_indentation(lvl) + f"{self.text}\n{self.term.print(lvl)}")

        return get_indentation(lvl) + f"{self.text}\n{self.term.print(lvl)}"

    def get_prov_info(self, prov_info):
        return self.print_prov_ext() + '\n' + self.term.get_prov_info(None)

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        out = self.term.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl)
        # if self.text.startswith('# SSA-'):
        #    out = out.split('\n')
        #    out = [out[0] + self.text] + out[1:]
        #    out = '\n'.join(out)
        # else:
        out = get_indentation(lvl) + self.text + '\n' + out
        out = out.replace(NEW_COMMENT_MARKER, ORIGINAL_COMMENT_MARKER, 1)
        return post_processing_anf_to_python(out)


class ANF_E_LET(ANF_E):
    def __init__(self, var: ANF_V, term1: ANF_E, term2: ANF_E, ssa_node: SSANode = None):
        super().__init__(ssa_node=ssa_node)
        self.var: ANF_V = var
        self.term1: ANF_E = term1
        self.term2: ANF_E = term2

    def print(self, lvl=0, prov_info: str = ''):
        next_lvl = lvl
        # next_lvl = lvl + 1
        # if isinstance(self.term2, ANF_E_LET) or isinstance(self.term2, ANF_E_IF) or isinstance(self.term2, ANF_E_COMM):
        #    next_lvl = lvl
        return get_indentation(
            lvl) + f"let {self.var.print(next_lvl)} = {self.term1.print(0)} in \n{self.term2.print(next_lvl)}"

    def get_prov_info(self, prov_info):
        return self.print_prov_ext() + PROV_INFO_SPLIT_CHAR + self.var.get_prov_info(
            None) + PROV_INFO_SPLIT_CHAR + self.print_prov_ext() + PROV_INFO_SPLIT_CHAR + self.term1.get_prov_info(
            None) + PROV_INFO_SPLIT_CHAR + self.print_prov_ext() + '\n' + self.term2.get_prov_info(None)

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        name = self.var.name
        if name == '_':
            lines = self.term1.parse_anf_to_python(assignments, parsed_blocks, loop_block_names).split('\n')
            lines = [get_indentation(lvl) + s for s in lines]
            return '\n'.join(lines) + '\n' + self.term2.parse_anf_to_python(assignments, parsed_blocks,
                                                                            loop_block_names, lvl)
        elif self.var.is_buffer_var:
            assignments[name] = self.term1
            return self.term2.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl)
        newline = '' if isinstance(self.term2, ANF_V_UNIT) else '\n'
        out = get_indentation(lvl) + self.var.parse_anf_to_python(assignments, parsed_blocks,
                                                                  loop_block_names) + ' = ' + self.term1.parse_anf_to_python(
            assignments, parsed_blocks, loop_block_names) + newline + self.term2.parse_anf_to_python(assignments,
                                                                                                     parsed_blocks,
                                                                                                     loop_block_names,
                                                                                                     lvl)
        out = "\n".join([s for s in out.split("\n") if s])
        out = post_processing_anf_to_python(out)
        return out


class ANF_E_LETREC(ANF_E):
    def __init__(self, terms: [ANF_EV], term2: ANF_E, ssa_node: SSANode = None):
        super().__init__(ssa_node=ssa_node)
        self.terms: [ANF_EV] = terms
        self.term2: ANF_EV = term2

    def print(self, lvl=0, prov_info: str = ''):
        add_newline = '' if len(self.terms) == 0 else '\n'
        return get_indentation(lvl) + 'letrec \n' + ('').join(letrec.print(lvl + 1) for letrec in self.terms) + (
                    get_indentation(lvl) + 'in\n' + (self.term2.print(lvl + 1))) if self.term2 is not None else ''

    def get_prov_info(self, prov_info):
        add_newline = '' if len(self.terms) == 0 else '\n'
        return '\n' + ''.join([term.get_prov_info(None) for term in self.terms]) + '\n' + self.term2.get_prov_info(None)

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        out = '\n'.join(t for t in
                        [term.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl) for term in
                         self.terms] if len(t) > 0)
        if self.term2 is not None:
            if isinstance(self.term2, ANF_E_FUNC):
                out += get_next_non_function_term(self.term2).parse_anf_to_python(assignments, parsed_blocks,
                                                                                  loop_block_names, lvl)
            else:
                out += self.term2.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl)
        return post_processing_anf_to_python(out)


class ANF_E_LETREC_ASS(ANF_E):
    def __init__(self, var: ANF_V, term1: ANF_EV, ssa_node: SSANode = None):
        super().__init__(ssa_node=ssa_node)
        self.var: ANF_V = var
        self.term1: ANF_EV = term1

    def print(self, lvl=0, prov_info: str = ''):
        line_sep = '\n'
        return get_indentation(lvl) + self.var.print(lvl + 1) + ' = ' + line_sep + self.term1.print(lvl + 1) + line_sep

    def get_prov_info(self, prov_info):
        add_new_line = isinstance(self.term1, ANF_E_LETREC_ASS) or isinstance(self.term1, ANF_E_LET) or isinstance(
            self.term1, ANF_E_COMM)
        line_sep2 = '\n'
        return self.var.get_prov_info(
            None) + PROV_INFO_SPLIT_CHAR + self.print_prov_ext() + '\n' + self.term1.get_prov_info(None) + line_sep2

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        if self.var.is_block_id:
            t1 = get_next_non_function_term(self.term1)
            assignments[self.var.name] = t1
            return ''

        vars = get_function_parameter_recursive(self.term1)
        next_term = get_next_non_function_term(self.term1)
        out = get_indentation(lvl) + 'def ' + self.var.parse_anf_to_python(assignments, parsed_blocks, loop_block_names,
                                                                           lvl) + '(' + ','.join(
            vars) + '):\n' + next_term.parse_anf_to_python(assignments, parsed_blocks, loop_block_names, lvl + 1)
        return post_processing_anf_to_python(out)


def get_function_parameter_recursive(next):
    if isinstance(next, ANF_E_FUNC):
        if next.input_var is not None:
            return get_function_parameter_recursive(next.term) + [next.input_var.parse_anf_to_python({}, [], [])]
    return []


def get_next_non_function_term(next):
    if isinstance(next, ANF_E_FUNC):
        return get_next_non_function_term(next.term)
    else:
        return next


class ANF_E_IF(ANF_E):
    def __init__(self, test: ANF_V_VAR, term_if: ANF_E, term_else: ANF_E, ssa_node: SSANode = None):
        super().__init__(ssa_node=ssa_node)
        self.test: ANF_V_VAR = test
        self.term_if: ANF_E = term_if
        self.term_else: ANF_E = term_else

    def print(self, lvl=0, prov_info: str = ''):
        return get_indentation(
            lvl) + f"if {self.test.print(0)} then \n{self.term_if.print(lvl + 1)} \n{get_indentation(lvl)}else\n{self.term_else.print(lvl + 1)}"

    def get_prov_info(self, prov_info):
        return self.print_prov_ext() + PROV_INFO_SPLIT_CHAR + self.test.get_prov_info(
            None) + PROV_INFO_SPLIT_CHAR + self.print_prov_ext() + '\n' + self.term_if.get_prov_info(
            None) + '\n' + self.print_prov_ext() + '\n' + self.term_else.get_prov_info(None)

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

        # Loop that contains break or continue in main body
        pattern = r'(.|\n)*(continue|break)\n( )*L[0-9]+\(.*\)(\n)*'
        is_if_with_only_continue_in_body = re.match(pattern, if_out) is not None
        # If the labels of gotos are i and i+1 it shows as the pattern which is generated when parsing a while loop
        # Otherwise it would be i and i+2 because the block i+1 would be after the if-else block
        if (goto2 == '' or int(goto1) + 1 == int(goto2)) and (
                'L' + str(int(goto1) - 1) + '(' in if_out) and not is_if_with_only_continue_in_body:
            if_out = '\n'.join(if_out.split('\n')[0:-1])
            return (get_indentation(lvl) + 'while ' + self.test.parse_anf_to_python(assignments, parsed_blocks,
                                                                                    loop_block_names, lvl) + ':\n'
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
        post_if_else = assignments['L' + str(int(goto1) + 1)].parse_anf_to_python(assignments, parsed_blocks,
                                                                                  loop_block_names, lvl) if 'L' + str(
            int(goto1) + 1) in assignments else ''

        # If there is no content left in the else branch do not print any else content
        else_out = '\n' if else_out == '' else ('\n' + get_indentation(lvl) + 'else:\n' + else_out + '\n')
        out = get_indentation(lvl) + 'if ' + self.test.parse_anf_to_python(assignments, parsed_blocks, loop_block_names,
                                                                           0) + ':\n' + if_out + else_out + post_if_else
        return out


class ANF_V(ANF_EV):
    def __init__(self, ssa_node: SSANode = None):
        super().__init__(ssa_node=ssa_node)
        self.is_buffer_var: bool = False
        self.is_block_id: bool = False

    def print(self, lvl=0, prov_info: str = ''):
        return f""

    def get_prov_info(self, prov_info):
        return ''

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        return get_indentation(lvl) + 'ANF_V'


class ANF_V_CONST(ANF_V):
    def __init__(self, value: str, ssa_node: SSANode = None, is_block_id: bool = False):
        super().__init__(ssa_node=ssa_node)
        self.value: str = value
        self.is_block_id = is_block_id

    def print(self, lvl=0, prov_info: str = ''):
        if self.prov_info == 'RET':
            return get_indentation(lvl) + f"{self.value}"
        else:
            return f"{self.value}"

    def get_prov_info(self, prov_info):
        if self.is_block_id:
            return 'lc' + self.print_prov_ext()
        return 'c' + self.print_prov_ext()

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        # value = normalize_name(self.value)
        val = self.value
        # if isinstance(self.value, str):
        #    val = repr(self.value)[1:-1]
        return get_indentation(lvl) + postprocessing_ANF_V_to_python(self, val)


def postprocessing_ANF_V_to_python(n: ANFNode, out: str):
    if n.prov_info == 'RET':
        out = 'return ' + out
        return out.replace('return return', 'return')
    return out


class ANF_V_VAR(ANF_V):
    def __init__(self, name: str, is_buffer_var: bool = False, is_block_id: bool = False, ssa_node: SSANode = None):
        super().__init__(ssa_node=ssa_node)
        self.name: str = name
        self.is_buffer_var: bool = is_buffer_var
        self.is_block_id: bool = is_block_id

    def print(self, lvl=0, prov_info: str = ''):
        return f"{self.name}"

    def get_prov_info(self, prov_info):
        if self.is_block_id:
            return 'lv' + self.print_prov_ext()
        return ('b' if self.is_buffer_var else '') + 'v' + self.print_prov_ext()

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        if self.name in assignments:
            return get_indentation(lvl) + postprocessing_ANF_V_to_python(self,
                                                                         assignments[self.name].parse_anf_to_python(
                                                                             assignments, parsed_blocks,
                                                                             loop_block_names, lvl))
        name = normalize_name(self.name)
        return get_indentation(lvl) + postprocessing_ANF_V_to_python(self, name)


def normalize_name(name: str):
    idx = name.rfind('_')
    if not (re.match(r'.*_([0-9])+', name)) or idx == -1:  # or name.startswith(SSA_BUFFER_VAR_NAME):
        idx = len(name)
    return name[0:idx]


class ANF_V_UNIT(ANF_V):
    def __init__(self, ssa_node: SSANode = None):
        super().__init__(ssa_node)

    def print(self, lvl=0, prov_info: str = ''):
        return get_indentation(lvl) + "unit"

    def get_prov_info(self, prov_info):
        return 'u'

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        return ''


class ANF_E_FUNC(ANF_E):
    def __init__(self, input_var: ANF_V, term: ANF_E, ssa_node: SSANode = None):
        super().__init__(ssa_node=ssa_node)
        self.input_var: ANF_V = input_var
        self.term: ANF_E = term

    def print(self, lvl=0, prov_info: str = ''):
        next_node = get_first_node_diff_than_comment(self.term)
        add_new_line = (not issubclass(type(next_node), ANF_V) or isinstance(next_node, ANF_V_UNIT)) or isinstance(
            self.term, ANF_E_COMM)
        line_sep = '\n' if add_new_line else ''
        if self.input_var is None:
            return get_indentation(lvl) + f"{font['lambda_sign']} . {line_sep}{self.term.print(lvl)}"
        return get_indentation(
            lvl) + f"{font['lambda_sign']} {self.input_var.print(0)} . {line_sep}{self.term.print(lvl)}"

    def get_prov_info(self, prov_info):
        next_node = get_first_node_diff_than_comment(self.term)
        add_new_line = (not issubclass(type(next_node), ANF_V) or isinstance(next_node, ANF_V_UNIT)) or isinstance(
            self.term, ANF_E_COMM)
        line_sep = '\n' if add_new_line else PROV_INFO_SPLIT_CHAR
        if self.input_var is None:
            return self.print_prov_ext() + PROV_INFO_SPLIT_CHAR + line_sep + self.term.get_prov_info(None)
        return self.print_prov_ext() + PROV_INFO_SPLIT_CHAR + self.input_var.get_prov_info(
            None) + PROV_INFO_SPLIT_CHAR + line_sep + self.term.get_prov_info(None)

    def parse_anf_to_python(self, assignments, parsed_blocks, loop_block_names, lvl=0):
        # Not used_var_names
        # letrecs of parsed functions do not call print on this type only read its variables and innermost term
        return ''


def print_anf_code_to_python(anf_tree: ANFNode):
    return post_processing_anf_to_python(anf_tree.parse_anf_to_python({}, [], []))


def get_first_node_diff_than_comment(node):
    if isinstance(node, ANF_E_COMM):
        return get_first_node_diff_than_comment(node.term)
    return node


def get_indentation(nesting_lvl):
    return '    ' * nesting_lvl


def remove_indentation(code, i):
    new_code = ''
    for c in code.split('\n'):
        new_code += c[4:] + '\n'
    return new_code


def parse_ssa_to_anf(ssa: SSA_AST, debug: bool, no_pos: bool):
    global debug_mode, no_pos_tracking
    reset()
    no_pos_tracking = no_pos
    debug_mode = debug
    return SA(ssa)


# Transform SSA AST into ANF AST
def SA(ssa_ast: SSA_AST):
    global ssa_ast_global
    ssa_ast_global = ssa_ast

    # Transform all procedures of the SSA AST and put the call of the first block as inner most term
    first_block = get_first_block_in_proc(ssa_ast.blocks)
    return SA_PS(ssa_ast.procs, SA_BS(ssa_ast.blocks[0], True, first_scope=True))


# Transforms a list of procedures putting the inner_term inside the innermost let/rec
def SA_PS(ps: [SSA_P], inner_term, as_array: bool = False):
    # When there is no procedure we return the inner term
    if len(ps) == 0:
        return inner_term

    # If we have the last procedure we return a letrec of this proc using the inner term

    parsed_procs = []
    while len(ps) > 0:
        p: SSA_P = ps[0]

        first_term = SA_BS(p.blocks[0], True, first_scope=True)
        # args = p.args[::-1] If arguments should be given in backwards order
        # If so the back transformation function get_function_parameter_recursive must also be build in revers
        args = p.args
        while len(args) > 0:
            first_term = ANF_E_FUNC(SA_V(args[0]), first_term, ssa_node=p)
            args = args[1:]

        v = SA_V(p.name)
        v.init(ssa_node=p)
        ps = ps[1:]
        parsed_procs.append(ANF_E_LETREC_ASS(v, first_term, ssa_node=p))

    let_rec = ANF_E_LETREC(parsed_procs, inner_term, ssa_node=p)

    return let_rec


# Transform a list of SSA blocks
def SA_BS(b: SSA_B, is_block_id=True, first_scope=False):
    block_vars = [SA_V(phi_var) for phi_var in get_phi_vars_in_block(b)]

    # Create self containing functions to build lambda functions in each other. leading to have functions with multiple variables
    if len(block_vars) > 0:
        b_terms = ANF_E_FUNC(block_vars[0], SA_ES(b, b.terms), ssa_node=b)
        block_vars = block_vars[1:]

        while len(block_vars) > 0:
            b_terms = ANF_E_FUNC(block_vars[0], b_terms, ssa_node=b)
            block_vars = block_vars[1:]
    else:
        b_terms = SA_ES(b, b.terms)

    let_rec = []
    if b.blocks is not None and len(b.blocks) > 0:
        let_rec = SA_BS2(b.blocks)

    if b.blocks is None or len(b.blocks) == 0:
        return b_terms

    if first_scope:
        return ANF_E_LETREC(let_rec, b_terms)
    return ANF_E_LETREC_ASS(ANF_V_CONST(block_identifier + b.label.label, ssa_node=b, is_block_id=True),
                            ANF_E_LETREC(let_rec, b_terms))


def SA_BS2(bs: [SSA_B], is_block_id=True):
    blocks_out = []

    for b in bs:
        if b.blocks is not None and len(b.blocks) > 0:
            blocks_out.append(SA_BS(b))
        else:
            block_vars = [SA_V(phi_var) for phi_var in get_phi_vars_in_block(b)]

            # Create self containing functions to build lambda functions in each other. leading to have functions with multiple variables
            if len(block_vars) > 0:
                b_terms = ANF_E_FUNC(block_vars[0], SA_ES(b, b.terms), ssa_node=b)
                block_vars = block_vars[1:]

                while len(block_vars) > 0:
                    b_terms = ANF_E_FUNC(block_vars[0], b_terms, ssa_node=b)
                    block_vars = block_vars[1:]
            else:
                b_terms = SA_ES(b, b.terms)

            blocks_out.append(
                ANF_E_LETREC_ASS(ANF_V_CONST(block_identifier + b.label.label, ssa_node=b, is_block_id=True), b_terms,
                                 ssa_node=b))
    return blocks_out


def SA_ES(b: SSA_B, terms: [SSA_E]):
    if len(terms) == 0:
        return ANF_V_UNIT()

    term = terms[0]
    if term is None:
        return ANF_V_UNIT()

    if isinstance(term, SSA_E_ASS):
        unwrap_inner_applications_naming(term.value)
        return unwrap_inner_applications_let_structure(term.value,
                                                       ANF_E_LET(SA_V(term.var), SA_V(term.value), SA_ES(b, terms[1:]),
                                                                 ssa_node=term))
    if isinstance(term, SSA_E_GOTO):
        return ANF_E_APP(
            [SA_V(arg) for arg in get_phi_vars_for_jump(b, get_block_by_id(ssa_ast_global, term.label.label), ssa_ast_global)],
            ANF_V_CONST(block_identifier + term.label.label, ssa_node=term, is_block_id=True), ssa_node=term)
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
        return unwrap_inner_applications_let_structure(term.test,
                                                       ANF_E_IF(SA_V(term.test, True), SA_ES(b, [term.term_if]),
                                                                SA_ES(b, [term.term_else]), ssa_node=term), True)
    if isinstance(term, SSA_E_FUNC_CALL):
        unwrap_inner_applications_naming(term)
        return unwrap_inner_applications_let_structure(term,
                                                       ANF_E_LET(ANF_V_CONST('_'), SA_V(term), SA_ES(b, terms[1:]),
                                                                 ssa_node=term))
    if issubclass(type(term), SSA_E_COMM):
        return ANF_E_COMM(term.text, SA_ES(b, terms[1:]), ssa_node=term)
    if issubclass(type(term), SSA_V):
        # Needed for variables just being there like in an transformed ifexp node
        return ANF_E_LET(ANF_V_CONST('_'), SA_V(term), SA_ES(b, terms[1:]))
    return ANF_E_APP([], ANF_V_CONST('Not-Impl'))


def unwrap_inner_applications_let_structure(var: SSA_V | SSA_E_FUNC_CALL, inner, unwrap_var: bool = False):
    if isinstance(var, SSA_E_FUNC_CALL):
        if unwrap_var:
            name = buffer_assignments[var]
            inner = unwrap_inner_applications_let_structure(var,
                                                            ANF_E_LET(ANF_V_VAR(name, True, ssa_node=var), SA_V(var),
                                                                      inner, ssa_node=var))
        else:
            for arg in var.args:
                if isinstance(arg, SSA_E_FUNC_CALL):
                    name = buffer_assignments[arg]
                    inner = unwrap_inner_applications_let_structure(arg, ANF_E_LET(ANF_V_VAR(name, True, ssa_node=arg),
                                                                                   SA_V(arg), inner, ssa_node=arg))

            if isinstance(var.name, SSA_E_FUNC_CALL):
                name = buffer_assignments[var.name]
                inner = unwrap_inner_applications_let_structure(var.name,
                                                                ANF_E_LET(ANF_V_VAR(name, True, ssa_node=var.name),
                                                                          SA_V(var.name), inner, ssa_node=var.name))
    return inner


def unwrap_inner_applications_naming(var: SSA_V, unwrap_var: bool = False):
    if isinstance(var, SSA_E_FUNC_CALL):
        if unwrap_var:
            name = get_buffer_variable()
            buffer_assignments[var] = name
        for arg in var.args:
            if isinstance(arg, SSA_E_FUNC_CALL):
                name = get_buffer_variable()
                buffer_assignments[arg] = name
                unwrap_inner_applications_naming(arg)
        if isinstance(var.name, SSA_E_FUNC_CALL):
            name = get_buffer_variable()
            buffer_assignments[var.name] = name
            unwrap_inner_applications_naming(var.name)


# Transform values from SSA to ANF
def SA_V(var: SSA_V, can_be_buffered: bool = False):
    if isinstance(var, SSA_V_VAR):
        return ANF_V_VAR(var.name, ssa_node=var)
    if isinstance(var, SSA_V_CONST):
        return ANF_V_CONST(var.value, ssa_node=var)
    if isinstance(var, SSA_L):
        return ANF_V_CONST(var.label, ssa_node=var)
    if isinstance(var, SSA_E_FUNC_CALL):
        if can_be_buffered and var in buffer_assignments:
            return ANF_V_VAR(buffer_assignments[var], ssa_node=var)
        else:
            return ANF_E_APP(
                [(ANF_V_VAR(buffer_assignments[par], ssa_node=par) if par in buffer_assignments else SA_V(par)) for par
                 in var.args],
                ANF_V_VAR(buffer_assignments[var.name], ssa_node=var.name) if var.name in buffer_assignments else SA_V(
                    var.name), ssa_node=var)
            # unwrap_inner_applications_naming(var)
            # return unwrap_inner_applications_let_structure(var, ANF_E_APP([(ANF_V_VAR(buffer_assignments[par], ssa_node=par) if par in buffer_assignments else SA_V(par)) for par in var.args], SA_V(var.name), ssa_node=var))

    return ANF_V_CONST('Not impl')


# Get a new unique buffer variable
def get_buffer_variable():
    global buffer_variable_counter
    buffer_variable_counter += 1
    return ANF_BUFFER_VAR_NAME + str(buffer_variable_counter - 1)


# Print the ANF tree including the provenance information right aligned to the code per line
def print_anf_with_prov_info(anf_parent: ANFNode):
    out = trim_double_spaces(anf_parent.print(), NEW_COMMENT_MARKER)
    prov = anf_parent.get_prov_info(None)
    max_chars = max([len(line) + line.count('\t') * 3 for line in out.split('\n')]) + 2
    return '\n'.join(
        [line + (max_chars - len(line) - line.count('\t') * 3) * ' ' + PROV_INFO_MARKER + info for line, info in
         zip(out.split('\n'), prov.split('\n'))])


# Read anf code and parse it into internal ANF AST representation
def parse_anf_from_text(code: str):
    code = code.strip()
    lines = code.split('\n')
    a = [tuple(line.rsplit(PROV_INFO_MARKER, 1)) for line in lines]
    code_lines, info_lines = zip(*[tuple(line.rsplit(PROV_INFO_MARKER, 1)) for line in lines])
    code_lines = [
        line if re.match(r'^(\s)*' + NEW_COMMENT_MARKER, line) else trim_double_spaces(line, NEW_COMMENT_MARKER) for
        line in code_lines]
    code_words = []

    for line in code_lines:
        # a = repr(line.strip())[1:-1]
        # x = re.split(r"(?<!\\)(?:\\\\)*'", repr(line.strip())[1:-1])
        # for i, part in enumerate([line.strip()] if re.match(r'^(\s)*' + NEW_COMMENT_MARKER, line) else re.split(r"(?<!\\\\)(?:\\\\\\\\)*'", repr(line.strip())[1:-1])):
        for i, part in enumerate(
                [line.strip()] if re.match(r'^(\s)*' + NEW_COMMENT_MARKER, line) else re.split(r"(?<!\\)'",
                                                                                               line.strip())):
            if i % 2 == 1 or part != ' ':
                for j, word in enumerate(
                        [part] if re.match(r'^(\s)*' + NEW_COMMENT_MARKER, part) else part.strip().split(' ')):
                    if i % 2 == 0 and ('\'' not in part or re.match(r'^(\s)*' + NEW_COMMENT_MARKER, part)):
                        code_words.append(word)
                    elif j == 0:
                        code_words.append('\'' + part + '\'')
                        break

    # code_words = list(filter(lambda e: e is not None, code_words))
    aa = parse_anf_e_from_code(code_words, [info_word for line in info_lines for info_word in
                                            line.strip().split(PROV_INFO_SPLIT_CHAR)])
    return aa


# Convert an ANF code expression to ANF AST
def parse_anf_e_from_code(code_words, info_words):
    next_word = code_words[0]
    info0_parts = info_words[0].split(PROV_INFO_EXT_CHAR)
    if len(info_words) > 1:
        info1_parts = info_words[1].split(PROV_INFO_EXT_CHAR)

    # Found a comment within provenance information
    if len(code_words[0]) > 0 and code_words[0].startswith(NEW_COMMENT_MARKER):
        return ANF_E_COMM(code_words[0], parse_anf_e_from_code(code_words[1:], info_words[1:]))
    if next_word == 'let':
        variable = ANF_V_VAR(code_words[1], info1_parts[0] == 'bv')
        right = parse_anf_e_from_code(code_words[3:], info_words[3:])
        _in = get_other_section_part(code_words[1:], info_words[1:], ['let', 'letrec'], ['in'])
        return ANF_E_LET(variable, right, _in)
    if next_word == 'letrec':
        i = 0
        blocks = []
        in_idx = get_other_section_part_idx(code_words[1:], info_words[1:], ['let', 'letrec'], ['in'])
        inside = 0
        while len(code_words) > i + 2 and i < in_idx:
            if code_words[i] == 'let' or (code_words[i] == 'letrec' and i > 0):
                inside += 1
            elif code_words[i] == 'in':
                inside -= 1
            elif inside == 0 and code_words[i] != 'let' and code_words[i + 2] == '=':
                # Find start of next assignment or end at the 'in' area
                i2 = i + 1
                inside2 = 0
                while len(code_words) > i2 + 2 and i2 < in_idx + 1:
                    if code_words[i2] == 'let' or code_words[i2] == 'letrec':
                        inside2 += 1
                    elif code_words[i2] == 'in':
                        inside2 -= 1
                    elif inside2 == 0 and 'let' not in code_words[i2] and code_words[i2 + 2] == '=':
                        i2 += 1
                        break
                    i2 += 1
                block = parse_anf_e_from_code(code_words[i + 1:i2], info_words[i + 1:i2])
                blocks.append(block)
            i += 1
        _in = get_other_section_part(code_words[1:], info_words[1:], ['let', 'letrec'], ['in'])
        return ANF_E_LETREC(blocks, _in)
    if len(code_words) > 1 and code_words[1] == '=':
        # assign within letrec
        variable = ANF_V_VAR(code_words[0], info0_parts[0] == 'bv',
                             is_block_id=info0_parts[0] == 'lc' or info0_parts[0] == 'lv')
        right = parse_anf_e_from_code(code_words[2:], info_words[2:])
        return ANF_E_LETREC_ASS(variable, right)
    if next_word == 'unit':
        return ANF_V_UNIT()
    if next_word == 'lambda' or next_word == 'λ':
        variable = ANF_V_VAR(code_words[1], info1_parts[0] == 'bv')
        rest = code_words[3:]
        rest_info = info_words[3:]
        if code_words[1] == '.':
            variable = None
            rest = code_words[2:]
            rest_info = info_words[2:]
        return ANF_E_FUNC(variable, parse_anf_e_from_code(rest, rest_info))
    if next_word == 'if':
        then_part = get_other_section_part(code_words[1:], info_words[1:], ['if'], ['then'])
        else_part = get_other_section_part(code_words[1:], info_words[1:], ['if'], ['else'])
        return ANF_E_IF(parse_anf_e_from_code(code_words[1:], info_words[1:]), then_part, else_part)

    count = 0
    while count + 1 < len(code_words) and next_word not in keywords:
        count += 1
        next_word = code_words[count]
    if count + 1 == len(code_words) and next_word not in keywords:
        count += 1

    if count > 1:
        # Read param naming prov info
        names = None
        if 'names=' in info_words[0]:
            parts = info_words[0].split(PROV_INFO_EXT_CHAR)
            parts2 = []
            for part in parts:
                if 'names=' in part:
                    names = part.split('names=')[1].split(',')
                else:
                    parts2.append(part)
            info_words[0] = PROV_INFO_EXT_CHAR.join(parts2)

        n = ANF_E_APP([parse_anf_v_from_code(code_words[i], info_words[i]) for i in range(1, count)],
                      parse_anf_v_from_code(code_words[0], info_words[0][1:]), params_named=names)
        info_word_parts = info_words[0][1:].split(PROV_INFO_EXT_CHAR)
        if n is not None and len(info_word_parts) > 1:
            n.prov_info = info_word_parts[len(info_word_parts) - 1]
            # The found info is not prov info but position info
            if ':' in n.prov_info:
                n.prov_info = ''
        return n
    else:
        return parse_anf_v_from_code(code_words[0], info_words[0])


# Convert an ANF code value to ANF AST
def parse_anf_v_from_code(code_word: str, info_word_with_prov: str):
    info_word_parts = info_word_with_prov.split(PROV_INFO_EXT_CHAR)
    info_word = info_word_parts[0]

    n = None
    if info_word == 'c':
        n = ANF_V_CONST(code_word)
    if info_word == 'v':
        n = ANF_V_VAR(code_word)
    if info_word == 'lv':
        n = ANF_V_VAR(code_word, False, is_block_id=True)
    if info_word == 'lc':
        n = ANF_V_CONST(code_word, is_block_id=True)
    if info_word == 'bv':
        n = ANF_V_VAR(code_word, True)
    if info_word.startswith('f'):
        n = ANF_E_APP([], parse_anf_v_from_code(code_word, info_word[1:]))
    if n is not None and len(info_word_parts) > 1:
        n.prov_info = info_word_parts[len(info_word_parts) - 1]
        # The found info is not prov info but position info
        if ':' in n.prov_info:
            n.prov_info = ''
    return n


# Get the position of the next part belonging to the given one
# Ex. We start at a "letrec" and want to find its "in"
# (letrec) xxx let xxx let xxx in xxx in xxx (in) xxx
def get_other_section_part(code_words: [str], info_words: [str], open_keys: [str], close_keys: [str]):
    idx = get_other_section_part_idx(code_words, info_words, open_keys, close_keys)
    return parse_anf_e_from_code(code_words[idx + 1:], info_words[idx + 1:])


def get_other_section_part_idx(code_words: [str], info_words: [str], open_keys: [str], close_keys: [str]):
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

    return idx


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
        if skip > 0:
            skip -= 1
            continue

        line = lines[i]
        line_strip = line.strip()
        if ORIGINAL_COMMENT_MARKER + ' SSA-AugAssign' in line:
            a, b, c, d = re.sub(r'(\w+)\s*=\s*(|.)\1\s*(.{1,2})\s*(.*)', r'\1;\2;\3;\4', lines[i + 1]).split(';')
            output += f'{a} {c.strip()}= {b}{d}\n'
            skip = 1
        elif line_strip.startswith(ORIGINAL_COMMENT_MARKER + ' SSA-ForTuple'):
            lines[i] = ''
            var = lines[i + 1].strip().split(' ')[1]
            j = 2
            vars = []
            while i + j < len(lines):
                if lines[i + j] == '':
                    j += 1
                    continue
                next_var = lines[i + j].split('=')[0].strip()
                if ',' in next_var:
                    next_var = '(' + next_var + ')'
                vars.append(next_var)
                lines[i + j] = ''
                j += 1
                if i + j == len(lines) or var not in lines[i + j]:
                    break
            lines[i + 1] = lines[i + 1].replace(var, '(' + ','.join(vars) + ')')
        elif line_strip.startswith(ORIGINAL_COMMENT_MARKER + ' SSA-WithinFun-'):
            fun_name = lines[i].replace(ORIGINAL_COMMENT_MARKER + ' SSA-WithinFun-', '').strip()
            fun_end_idx = 0
            j = 2
            # Find start of target function
            while not re.match(r'^ *def ' + fun_name + '.*', lines[i + j]):
                j += 1
                if i + j >= len(lines):
                    break
                line_indentation = len(re.findall(r"^ *", lines[i + j])[0])
                # Save end of current function to be moved
                if line_indentation == 0 and fun_end_idx == 0:
                    fun_end_idx = i + j

            if i + j < len(lines):
                indentation = len(re.findall(r"^ *", lines[i + j])[0])

                j2 = 1
                if re.match(r'^\s*' + ORIGINAL_COMMENT_MARKER + ' SSA-WithinFun', lines[i + j + j2]):
                    j2 += 1

                if i + j + j2 < len(lines):
                    target_indentation = indentation + 4
                    if fun_end_idx == 0:
                        lines = lines[i + j:i + j + j2] + [(' ' * target_indentation) + line for line in
                                                           [lines[i - 1]] + lines[i + 1:i + j - 1]] + lines[i + j + j2:]
                    else:
                        lines = lines[fun_end_idx:i + j + j2] + [(' ' * target_indentation) + line for line in
                                                                 [lines[i - 1]] + lines[i + 1:fun_end_idx]] + lines[
                                                                                                              i + j + j2:]
                    out = '\n'.join(output.split('\n')[:-2]) + post_processing_anf_to_python('\n'.join(lines))
                    return out
                else:
                    output += line + '\n'
            else:
                output += line + '\n'
        elif ORIGINAL_COMMENT_MARKER + ' SSA-ClassStart' in line:
            j = 1
            while re.match('( )*' + ORIGINAL_COMMENT_MARKER + ' SSA-ClassEnd', lines[i + j]) is None:
                lines[i + j] = lines[i + j][2:]
                j += 1
            lines[i + j] = ''
        elif ORIGINAL_COMMENT_MARKER + ' SSA-Import' in line:
            lines[i + 1] = lines[i + 1].split('# ', 1)[1]
            lines[i] = ''
        elif ORIGINAL_COMMENT_MARKER + ' SSA-SubscriptMultiDim-' in line:
            info = lines[i].split('SSA-SubscriptMultiDim-')[1]
            # var, count = info.split('-')
            # line = lines[i + 1]
            # pattern = re.escape(var) + r'\[[^\]]*\]' * int(count)
            # content = re.search(pattern, line).group(0)
            # line = line.replace(content, content.replace('][', ','))
            line = replaceSpaces(lines[i + 1], ORIGINAL_COMMENT_MARKER)
            line = line.replace(info, info.replace('][', ','))
            lines[i + 1] = line
            lines[i] = ''
        elif '_str_format' in line_strip:
            v3 = None
            if '_str_format2' in line_strip:
                start, content = line_strip.split('_str_format2', 1)
                _, content, end = extract_main_parenthesis(content)
                v1, v2 = re.sub(r'\(*(.*),(.*)\)*', r'\1;\2', content).split(';')
            else:
                start, content = line_strip.split('_str_format3', 1)
                _, content, end = extract_main_parenthesis(content)
                v1, v2, v3 = re.sub(r'\(*(.*),(.*[^\(\)]),(.*[^\(\)])\)*', r'\1;\2;\3', content).split(';')

            gen_node = ast.parse('print(f\'{10:.3}\')')
            n: ast.FormattedValue = gen_node.body[0].value.args[0].values[0]
            n.value = ast.parse(v1)
            n.conversion = int(v2)
            n.format_spec = None

            format = ''
            if v3 is not None:
                format = ':' + v3.strip().replace('\'', '')

            out = start + ast.unparse(n)[1:-2] + format + '}\'' + end + '\n'
            out = out.replace('\'', 'f\'', 1)
            out = out.replace('ff\'', 'f\'', 1)
            out = ast.unparse(ast.parse(out).body[0])
            out = out.replace('\' + \'{', '{', 1)
            out = out.replace('}\' + \'', '}', 1)
            out = out.replace('\' + \'', '', 1)

            lines[i] = out
            return output + post_processing_anf_to_python('\n'.join(lines[i:]))

        elif ORIGINAL_COMMENT_MARKER + ' SSA-FuncSub' in line:
            parts = lines[i + 1].split(' = ')
            var = parts[0].strip()
            val = parts[1].strip()
            lines[i] = ''
            lines[i + 1] = ''
            lines[i + 2] = lines[i + 2].replace(var, val)
        elif ORIGINAL_COMMENT_MARKER + ' SSA-NamedExpr' in line:
            var, val = re.sub(r'^ *(.*) = (.*)', r'\1;\2', lines[i + 1]).split(';')
            start, var_part, end = re.sub(r'(.*)(([^a-zA-z]|^)' + var + '([^a-zA-z]|$))(.*)', r'\1;\2;\5',
                                          lines[i + 2]).split(';')
            lines[i + 2] = start + var_part.replace(var, '(' + var + ' := ' + val + ')') + end
            skip = 1
        elif ORIGINAL_COMMENT_MARKER + ' SSA-Tuple' in line:
            indentation = len(re.findall(r"^ *", lines[i + 1])[0])
            var, value = re.sub(r'^ *(.*)\s=\s(.*)', r'\1;\2', lines[i + 1]).split(';')
            j = 2
            vars = []
            while (var + '[') in lines[i + j]:
                vars.append(lines[i + j].split(' = ')[0].strip())
                j += 1
            # parenthesis = line_strip.split(ORIGINAL_COMMENT_MARKER + ' SSA-Tuple')[1]
            # part1 = '(' + ', '.join(vars) + ')' if parenthesis[0] == '1' else ', '.join(vars)
            # part2 = '(' + value + ')' if parenthesis[1] == '1' else value
            part1 = ', '.join(vars)
            part2 = value
            output += indentation * ' ' + part1 + ' = ' + part2 + '\n'
            skip = len(vars) + 1
        elif ORIGINAL_COMMENT_MARKER + ' SSA-ListComp' in line or ORIGINAL_COMMENT_MARKER + ' SSA-SetComp' in line or ORIGINAL_COMMENT_MARKER + ' SSA-DictComp' in line:
            variable = lines[i + 1].split('=')[0].strip()
            j = 2
            out = ''

            while re.match(r'^ *for.*', lines[i + j]):
                out = out + lines[i + j].split(':')[0].strip() + ' '
                j += 1

            if ORIGINAL_COMMENT_MARKER + ' SSA-DictComp' in line:
                value = re.sub(r'^ *.*\[(.*)\] = (.*)', r'\1;\2', lines[i + j]).strip().split(';')
                value = value[0] + ': ' + value[1]
            else:
                value = re.sub(r'^ *' + variable + '\\.' + VAR_NAME_REGEX + '\((.*)\).*', r'\1', lines[i + j]).strip()

            out = value + ' ' + out
            if ORIGINAL_COMMENT_MARKER + ' SSA-ListComp' in line:
                out = '[' + out + ']'
            else:
                out = '{' + out + '}'

            output += lines[i + j + 1].replace(variable, out) + '\n'
            skip = j + 1
        elif ORIGINAL_COMMENT_MARKER + ' SSA-Lambda' in line and 'def ' in lines[i - 1]:
            if len(lines) > i + 3 or len(lines) > i + 2 and lines[i + 2] != '':
                name, args = re.sub(r'def (.*)\((.*)\).*', r'\1;\2', lines[i - 1]).split(';')
                name = name.strip()
                code = lines[i + 1]
                output = ''.join(output.split('\n')[:-2])
                lines[i - 1] = ''
                lines[i] = ''
                lines[i + 1] = ''
                j = 2
                while i + j < len(lines):
                    lines[i + j] = re.sub(name, 'lambda ' + args + ': ' + code.replace('return', '', 1), lines[i + j])
                    j += 1
                skip = 1
            output += lines[i] + '\n'
        elif line_strip.startswith(ORIGINAL_COMMENT_MARKER + ' SSA-SubscriptSet'):
            indentation, var, subscript, value = re.sub(r'^( *)(.*) = .*\((.*),(.*),(.*)\).*', r'\1;\2;\4;\5',
                                                        lines[i + 1]).split(';')
            output += indentation + var + '[' + subscript + '] = ' + value + '\n'
            skip = 1
        elif line_strip.startswith(ORIGINAL_COMMENT_MARKER + ' SSA-AnnAssign'):
            indentation = len(re.findall(r"^ *", lines[i + 1])[0])
            _, t, simple = line_strip.split('|')
            p1, p2 = lines[i + 1].strip().split(' = ')
            new_line = (indentation * ' ') + p1 + ': ' + t + ' = ' + p2 + '\n'
            if simple == '0':
                new_line = (indentation * ' ') + '(' + p1 + '): ' + t + ' = ' + p2 + '\n'
            output += new_line
            skip = 1
        elif ORIGINAL_COMMENT_MARKER + ' SSA-FOR' in line and len(lines) > i + 5:
            indentation = len(re.findall(r"^ *", lines[i + 1])[0])
            _, arr = re.sub(r'^ *(.*)\s=\s(.*)', r'\1;\2', lines[i + 1]).split(';')
            variable, _ = re.sub(r'^ *(.*)\s=\s(.*)', r'\1;\2', lines[i + 2]).split(';')
            indentation2 = len(re.findall(r"^ *", lines[i + 5])[0])
            j = 5
            while lines[i + j].startswith(indentation2 * ' '):
                j += 1
                if i + j == len(lines):
                    break
            # For loop without brak in main body
            if 'next(_SSA_' in lines[j - 1]:
                loop_body = lines[i + 5:j - 1]
            else:  # For loop with break in main body (no next assignment at end of loop body)
                loop_body = lines[i + 5:j]

            code_after = []
            if i + j < len(lines):
                code_after = lines[i + j:]

            lines = [indentation * ' ' + 'for ' + variable + ' in ' + arr + ':\n'] + loop_body + code_after
            return output + post_processing_anf_to_python('\n'.join(lines))
        elif ORIGINAL_COMMENT_MARKER + ' SSA-IfExp' in line:
            indentation = len(re.findall(r"^ *", lines[i + 2])[0])
            if_term = re.sub(r'^(.*)if (.*):(.)*', r'\2', lines[i + 1])
            ssa_var, if_val = re.sub(r'^ *(.*)\s=\s(.*)', r'\1;\2', lines[i + 2]).split(';')
            j = 3
            while not (lines[i + j].startswith(indentation * ' ' + ssa_var)):
                j += 1
            else_block = [line[4:] for line in lines[i + 6:i + j]]
            else_val = re.sub(r'^ *(.*)\s=\s(.*)', r'\2', lines[i + j])
            j += 1
            while not (lines[i + j].startswith((indentation - 4) * ' ') and ssa_var in lines[i + j]):
                j += 1
                if i + j == len(lines):
                    break
            if_exp = if_val + ' if ' + if_term + ' else ' + else_val
            line = lines[i + j].replace(ssa_var, if_exp)

            code_after = []
            if i + j + 1 < len(lines):
                code_after = lines[i + j + 1:]

            lines = [line] + else_block + code_after
            return output + post_processing_anf_to_python('\n'.join(lines))
        elif line_strip.startswith(ORIGINAL_COMMENT_MARKER + ' SSA-Attribute'):
            indentation, buffer, type, attr, var = re.sub(r'^( *)(.*) = _obj(2|)_(' + VAR_NAME_REGEX + ')\((.*)\)$',
                                                          r'\1;\2;\3;\4;\5', lines[i + 1]).split(';')
            params = ''
            # TODO Search for commans not within parenthesis, meaning there are multiple variables
            parts = split_at_comma(var)
            if len(parts) > 1:
                var, params = parts[0], ','.join(parts[1:])

            j = 2
            while i + j < len(lines) and re.match('.*' + buffer + '(?![A-Za-z0-9_])', lines[i + j]) is None:
                j += 1
            if i + j == len(lines):
                output += lines[i] + '\n'
            else:
                lines[i] = ''
                lines[i + 1] = ''
                if type == '2':
                    lines[i + j] = lines[i + j].replace(buffer, var + '.' + attr + '(' + params + ')')
                else:
                    lines[i + j] = lines[i + j].replace(buffer, var + '.' + attr)

                return output + post_processing_anf_to_python('\n'.join(lines[i + 2:]))
        else:
            output += line + ('' if (i == len(lines) - 1 and line == '') else '\n')
    return output


def split_at_comma(string):
    result = []
    current_part = ''
    braces_count = 0
    ap_count = 0

    for char in string:
        if char == ',' and braces_count == 0 and ap_count == 0:
            result.append(current_part.strip())
            current_part = ''
        else:
            current_part += char
            if char == '(' or char == '[':
                braces_count += 1
            elif char == ')' or char == ']':
                braces_count -= 1
            if char == '\'' and ap_count % 2 == 0:
                ap_count += 1
            elif char == '\'' and ap_count % 2 == 1:
                ap_count -= 1

    if current_part:
        result.append(current_part.strip())

    return result


def extract_main_parenthesis(input):
    indentation = 0
    start = 0
    for i in range(len(input)):
        if input[i] == '(':
            indentation += 1
            if indentation == 1:
                start = i + 1
        if input[i] == ')':
            indentation -= 1
            if indentation == 0:
                if len(input) > i + 1:
                    return input[:start], input[start:i], input[i + 1:]
                return input[:start], input[start:i], ''
