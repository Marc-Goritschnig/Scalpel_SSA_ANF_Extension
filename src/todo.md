## AST Nodes
- Starred and double Starred operator
- Classes
- Async Nodes
- GeneratorExp
- Subscript on left side of assignments

## Others
- Function placement after backtransformation
- Keeping line splits (for code lines spanning over multiple lines/ comments over multiple lines)
- kwargs and Starred when used as argument after named parameters 
- starred function parameters (* is lost)
- default parameters not working if they are complex e.g attributes def a(x=a.b):...
- double backslashes in strings (a = "C:\\test.py", a = "C:\\")