import ast
import os

def count_nodes(node):
    node_type = type(node).__name__
    if node_type == 'Starred':
        print()
    if node_type not in node_distribution:
        node_distribution[node_type] = 1
    else:
        node_distribution[node_type] += 1

    # Recursively visit child nodes
    for child_node in ast.iter_child_nodes(node):
        count_nodes(child_node)


node_distribution = {}
directory = './github_test_samples'
for filename in os.listdir(directory):
    if not filename.startswith('__init__') and filename.endswith('.py'):
        with open(os.path.join(directory, filename), "r") as file:
            tree = ast.parse(file.read())
            count_nodes(tree)

# Sort the distribution map by counter value
sorted_distribution = sorted(node_distribution.items(), key=lambda x: x[1], reverse=True)

# Print the sorted distribution map
for node_type, count in sorted_distribution:
    print(f"{node_type}: {count}")

# Print the sorted distribution map in pgfplots-compatible format
print("\\begin{tikzpicture}")
print("\\begin{axis}[xbar, y=-0.7cm, bar width=0.4cm, xlabel=Count, ytick=data, symbolic y coords={", end="")
for node_type, _ in sorted_distribution[:-1]:
    if node_type[0].isupper():
        print(f"{node_type},", end="")
print(f"{sorted_distribution[-1][0]}" + "} y dir=reverse]")
print("\\addplot coordinates {")
for node_type, count in sorted_distribution:
    if node_type[0].isupper():
        print(f"({count},{node_type})", end='')
print("};")
print("\\end{axis}")
print("\\end{tikzpicture}")

print(len(sorted_distribution))