from sys import stdout
from model.induced_tree import Node


def recursion_test(a: str): 
    print("do something")
    for child in None: 
        recursion_test(a)

def test2(node: Node):
    if True == True: 
        print(node.data)
        print(node.children)
    for child in node.children.values():
        test2(child)

# answer - need a conditional to check if reached the bottom of the recursion otherwise it will break!

def build_tree()->Node:
    root = Node(None, "Pitcher")
    c1 = Node(None, "Batter")
    c2 = Node(None, "Batter")
    root.add_child(1,c1)
    root.add_child(2,c2)
    return root

root = build_tree()
root.print_tree(stdout)`
