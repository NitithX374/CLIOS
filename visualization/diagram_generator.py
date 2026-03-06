from graphviz import Graph
import os
import platform
import subprocess

def generate_diagram(data):

    dot = Graph(format="png")
    dot.attr(rankdir="LR")

    # Nodes
    for node in data["nodes"]:
        if node == data["detected_by"]:
            dot.node(node, node, color="blue", style="filled")
        else:
            dot.node(node)

    # Edges
    for edge in data["edges"]:
        n1, n2 = edge
        if sorted([n1, n2]) == sorted(data["failed_link"]):
            dot.edge(n1, n2, color="red", style="dashed")
        else:
            dot.edge(n1, n2)

    output_path = dot.render("network_diagram", cleanup=True)

    print("Diagram saved as", output_path)

    # 🔥 Auto-open the image
    open_file(output_path)


def open_file(path):
    system = platform.system()

    if system == "Windows":
        os.startfile(path)
    elif system == "Darwin":  # macOS
        subprocess.run(["open", path])
    else:  # Linux
        subprocess.run(["xdg-open", path])