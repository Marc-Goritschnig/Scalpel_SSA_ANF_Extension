import ast_comments as ast

# Your Python code with comments as a string
code = """
#print('sdf') if 1 == 1 else print('1111') if a == 1 else print('sdfsdfsdf')
#-SSA-IfExp
if 1 == 1:
    _ssa_0 = print('sdf')
    # sfsdfsdf
else:
    #-SSA-IfExp
    if a == 1:
       _ssa_1 = print('1111')
    else:
       _ssa_1 = print('sdfsdfsdf')
    _ssa_0 = _ssa_1
_ssa_0
"""

c2 = """
if 1 == 1:
   # Test1
   print('a')
else:
   # Start of else
   print('b')
   #End of else
#Before print
print('b')
#After print
"""
# Parse the code with comments
parsed_ast = ast.parse(code)

print('a')
