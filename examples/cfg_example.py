def IsEasyChairQuery(input: str) -> bool:
    # (1) check that input contains "/" followed by anything not
    # containing "/" and containing "EasyChair"
    lastSlash = input.rindex('/')
    if lastSlash < 0:
        return False
    rest = input[lastSlash + 1:]
    if "EasyChair" not in rest:
        return False
    # (2) Check that input starts with "http://"
    if not input.startswith("http://"):
        return False
    # (3) Take the string between "http://" and the last "/".
    # if it starts with "www." strip the "www." off
    t = input[len("http://"): lastSlash]
    if t.startswith("www."):
        t = t[len("www.")]
    # (4) Check that after stripping we have either "live.com"
    # or "google.com"
    if t != "live.com" and t != "google.com":
        return False
    # s survived all checks
    return True
IsEasyChairQuery('test')

a = 1
print(a)
print(a)