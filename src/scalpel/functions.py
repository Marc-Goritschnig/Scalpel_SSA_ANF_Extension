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