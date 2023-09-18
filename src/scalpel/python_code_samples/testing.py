#-SSA-IfExp
if 1 == 1:
   _ssa_0 = print('0000')
else:
   #-SSA-IfExp
   if a == 1:
      _ssa_1 = print('1111')
   else:
      #-SSA-IfExp
      if a == 1:
         _ssa_2 = print('2222')
      else:
         _ssa_2 = print('33333')
      _ssa_1 = _ssa_2
   _ssa_0 = _ssa_1
_ssa_0