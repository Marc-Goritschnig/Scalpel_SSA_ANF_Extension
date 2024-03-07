import re


def replaceSpaces(text, comm_char):
    lines = text.split('\n')
    trimmed_lines = []
    for line in lines:
        if re.match(r'^\s*' + comm_char, line):
            trimmed_lines.append(line)
            continue
        pattern = r"'[^']*'| "  # Matches content within single quotes or spaces
        replacer = lambda match: match.group(0) if match.group(0).startswith("'") else ""

        leading_spaces = re.match(r'^\s*', line).group()
        trailing_spaces = re.search(r'\s*$', line).group()

        trimmed_line = leading_spaces + re.sub(pattern, replacer, line) + trailing_spaces
        trimmed_lines.append(trimmed_line)

    return '\n'.join(trimmed_lines)


def trim_double_spaces(text, comm_char):
    lines = text.split('\n')
    trimmed_lines = []

    withinString = False
    for line in lines:
        outLine = ''
        if re.match(r'^\s*' + comm_char, line):
            trimmed_lines.append(line)
            continue
        for i, c in enumerate(line):
            if c == '\'' and (i == 0 or line[i - 1] != '\\'):
                withinString = not withinString

            if not withinString and c == ' ' and (i + 1 < len(line) and line[i + 1] == ' '):
                outLine += ''
                continue
            outLine += c

        leading_spaces = re.match(r'^\s*', line).group()
        trailing_spaces = re.search(r'\s*$', line).group()

        trimmed_line = leading_spaces + outLine + trailing_spaces
        trimmed_lines.append(trimmed_line)

    return '\n'.join(trimmed_lines)


def fix_comment_positioning(ast, ast_tree):
    comments = []
    body = []
    for node in ast_tree.body:
        if isinstance(node, ast.Comment):
            comments.append(node)
        else:
            body.append(node)

    for c in comments:
        insert_comment_rec(c, body)

    ast_tree.body = body


def insert_comment_rec(c, stmts):
    idx = 0
    for node in stmts:
        if not hasattr(node, 'lineno'):
            continue

        if c.end_lineno < node.lineno:
            stmts.insert(idx, c)
            return True
        elif c.end_lineno < node.end_lineno:
            last_list = stmts
            # Iterate over the object's attributes and check if they are of list type
            for key, value in vars(node).items():
                if isinstance(value, list):
                    if c.end_lineno < value[0].lineno:
                        last_list.append(c)
                        return True
                    if insert_comment_rec(c, value):
                        return True
                    last_list = value
            last_list.append(c)
        else:
            pass  # Next node should be checked
        idx += 1
    return False



# Get the variables global unique name, considers parent variables to be used
def get_global_unique_name(var_name, parent_vars, used_var_names):
    return var_name


def get_global_unique_name_with_update(var_name, used_var_names):
    if var_name not in used_var_names:
        used_var_names[var_name] = 0
        return var_name + '_' + str(used_var_names[var_name])
    used_var_names[var_name] = used_var_names[var_name] + 1
    return var_name + '_' + str(used_var_names[var_name])

def get_global_unique_name_with_idx(var_name, used_var_names):
    if var_name not in used_var_names:
        used_var_names[var_name] = 0
        return var_name + '_' + str(used_var_names[var_name])
    return var_name + '_' + str(used_var_names[var_name])


#def custom_ast_parse(ast, source):
#    ast_tree = ast.parse(source)
#    fix_comment_positioning(ast, ast_tree)
#    return ast_tree
