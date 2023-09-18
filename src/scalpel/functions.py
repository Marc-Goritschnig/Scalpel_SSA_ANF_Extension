import re

def trim_double_spaces(text):
    lines = text.split('\n')
    trimmed_lines = []

    for line in lines:
        leading_spaces = re.match(r'^\s*', line).group()
        trailing_spaces = re.search(r'\s*$', line).group()

        content = re.sub(r'(?<=\S) {2,}(?=\S)', ' ', line.strip())
        trimmed_line = leading_spaces + content + trailing_spaces
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


#def custom_ast_parse(ast, source):
#    ast_tree = ast.parse(source)
#    fix_comment_positioning(ast, ast_tree)
#    return ast_tree
