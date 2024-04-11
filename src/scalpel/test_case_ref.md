test1.py...https://github.com/areski/python-nvd3/blob/develop/examples/lineChart.py  
- No (positional argument follows keyword argument)

test2.py...https://github.com/tilezen/vector-datasource/blob/master/scripts/all_the_kinds.py  
- Yes (Only new lines, spaces changed)

test3.py...https://github.com/lhartikk/AstroBuild/blob/master/astro_build.py  
- Yes - (new lines removed E instead of e .000 removed, fun position, parenthesis, ' statt ")

test4.py...https://github.com/gregmuellegger/django-autofixture/blob/master/runtests.py  
- Yes - (Starred function parameter is lost and function is positioned differently, new lines)

test5.py...https://github.com/emanuele/kaggle_pbr/blob/master/blend.py  
- No - (Subscript on left side of assignment)

test6.py...https://github.com/Kong/unirest-python/blob/master/unirest/utils.py  
- Yes - (parenthesis, fun position)

test7.py...https://github.com/Asabeneh/30-Days-Of-Python/blob/master/03_Day_Operators/day-3.py
- Yes - (spaces, new lines, inlined comments in new line)

test8.py...https://github.com/yangxue0827/FPN_Tensorflow/blob/master/help_utils/help_utils.py
- Yes - (fun position, comment indentation, new lines, ' statt """, parenthesis, ' statt ")

test9.py...https://github.com/Far0n/kaggletils/blob/master/kaggletils/math.py
- Yes - Default value of parameter uses attribute call and is not parsed correctly - (Order of functions different, 1. instead of 1.0, 1E-15 instead of 1e-15, ' statt """)

test10.py...https://github.com/TheAlgorithms/Python/blob/c6ca1942e14a6e88c7ea1b96ef3a6d17ca843f52/maths/abs.py#L5
- Yes - (typehints are removed, ' statt ", ' statt """, inlined comments in nachstehender Zeile, fun position)

test11.py...https://github.com/sourabhvora/HyperFace-with-SqueezeNet/blob/master/hyperface.py
- Yes - fun position, (new lines, ' statt ", spaces)

test12.py...https://github.com/openwall/john/blob/f55f42067431c0e8f67e600768cd8a3ad8439818/run/dns/tsigkeyring.py#L25
- Yes - fun position, 'text' instead of """text"""

test13.py...https://github.com/Asabeneh/30-Days-Of-Python/blob/master/04_Day_Strings/day_4.py
-  Yes - (inline comments moved into new line, new lines, spaces)

test14.py...https://github.com/Tautulli/Tautulli/blob/d019efcf911b4806618761c2da48bab7d04031ec/lib/dns/grange.py#L24
- Yes - Function order, ' statt ", parenthesis changed, typehints lost, ' statt """, new lines

test15.py...https://github.com/RMerl/asuswrt-merlin.ng/blob/bc3c8c32858492818c2be50e2ea95522bd342f5e/release/src/router/samba-3.6.x_opwrt/source/lib/dnspython/dns/opcode.py#L45
- Yes - (parenthesis, new lines, ' """, function order, int statt hex)

test16.py...https://github.com/hemathulsidhos/Download-and-Extract-Structural-Metadata-from-Islandora/blob/main/download_rels_ext_2.0.py
- Yes (default value for functino parameters lost, fun position, ' statt ")

test17.py...https://github.com/amitay/samba/blob/68ef3c48fc6df2396381af622140fbc2023bd81c/lib/dnspython/dns/rdtypes/IN/IPSECKEY.py#L76
- No - (Starred after named parameter)

test18.py...https://github.com/RMerl/asuswrt-merlin.ng/blob/bc3c8c32858492818c2be50e2ea95522bd342f5e/release/src/router/samba-3.6.x_opwrt/source/lib/dnspython/dns/rdtypes/ANY/SSHFP.py#L49
- No - (Starred after named parameter)

test19.py...https://github.com/RMerl/asuswrt-merlin.ng/blob/bc3c8c32858492818c2be50e2ea95522bd342f5e/release/src/router/samba-3.6.x_opwrt/source/lib/dnspython/dns/rcode.py#L61
- Yes - (new lines, int instead of hex, ' statt """, function order, parenthesis)

test20.py...https://github.com/RMerl/asuswrt-merlin.ng/blob/bc3c8c32858492818c2be50e2ea95522bd342f5e/release/src/router/samba-3.6.x_opwrt/source/lib/dnspython/dns/flags.py#L82
- Yes - (function position, parenthesis, new lines, integers made from hex, ' instead of """)

