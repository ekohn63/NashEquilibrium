from sys import stdout
from model.induced_tree import Node
from model.action_set import BATTER_ACTIONS as bs, PITCHER_ACTIONS as ps

def build_tree() -> Node: 
    root = Node(data = "Pitcher", info_set = 1)
    b1 = Node(data = "Batter", info_set = 1)
    b2 = Node(data = "Batter", info_set = 1)
    root.add_child(ps[0], b1)
    root.add_child(ps[1], b2)

    c3 = Node(data = "Nature", info_set = 1)
    c4 = Node(data = "Nature", info_set = 1)
    c5 = Node(data = "Nature", info_set = 1)
    c6 = Node(data = "Nature", info_set = 1)

    b1.add_child(bs[0], c3)
    b1.add_child(bs[1], c4)
    b2.add_child(bs[0], c5)
    b2.add_child(bs[1], c6)

    c7 = Node(data = "Pitcher", info_set = 2)
    c8 = Node(data = "Pitcher", info_set = 3)
    c9 = Node(data = "Terminal")
    c3.add_child("Strike", c7)
    c3.add_child("Ball", c8)
    c3.add_child("Terminal", c9)

    c10 = Node(data = "Pitcher", info_set = 4)
    c11 = Node(data = "Pitcher", info_set = 5)
    c12 = Node(data = "Terminal")
    c4.add_child("Strike", c10)
    c4.add_child("Ball", c11)
    c4.add_child("Terminal", c12)

    c13 = Node(data = "Pitcher", info_set = 6)
    c14 = Node(data = "Pitcher", info_set = 7)
    c15 = Node(data = "Terminal")
    c5.add_child("Strike", c13)
    c5.add_child("Ball", c14)
    c5.add_child("Terminal",c15)

    c16 = Node(data = "Pitcher", info_set = 8)
    c17 = Node(data = "Pitcher", info_set = 9)
    c18 = Node(data = "Terminal")
    c6.add_child("Strike", c16)
    c6.add_child("Ball", c17)
    c6.add_child("Terminal", c18)

    pitcher_node = [c7, c8, c10, c11, c13, c14, c16, c17]
    for i, node in enumerate(pitcher_node): 
        bi = Node(data = "Batter", info_set = 1 + i)
        bj = Node(data = "Batter", info_set = 1 + i)
        node.add_child(ps[0],bi)
        node.add_child(ps[1], child = bj)

    for pitcher in pitcher_node: 
        for i, node in enumerate(pitcher.children.values()): 
            ni = Node(data = "Nature", info_set = 1 + i)
            nj = Node(data = "Nature", info_set = 1 + i)
            node.add_child(bs[0], ni)
            node.add_child(bs[1], nj)

    for pitcher in pitcher_node: 
        for batter in pitcher.children.values(): 
            for nature in batter.children.values(): 
                ti = Node(data = "Terminal")
                nature.add_child("Terminal", ti)

    # still need to make the nature children, and the childrne of nature
    return root

def build_tree2() -> Node: 
    root = Node(data = "Pitcher", info_set = 1)
    b1 = Node(data = "Batter", info_set = 1)
    b2 = Node(data = "Batter", info_set = 1)
    root.add_child("Fastball", b1)
    root.add_child("Offspeed", b2)

    c3 = Node(data = "Nature", info_set = 1)
    c4 = Node(data = "Nature", info_set = 1)
    c5 = Node(data = "Nature", info_set = 1)
    c6 = Node(data = "Nature", info_set = 1)

    b1.add_child("Swing", c3)
    b1.add_child("Take", c4)
    b2.add_child("Swing", c5)
    b2.add_child("Take", c6)

    c7 = Node(data = "Pitcher", info_set = 2)
    c8 = Node(data = "Pitcher", info_set = 3)
    c9 = Node(data = "Terminal")
    c3.add_child("Strike", c7)
    c3.add_child("Ball", c8)
    c3.add_child("Terminal", c9)

    c10 = Node(data = "Pitcher", info_set = 4)
    c11 = Node(data = "Pitcher", info_set = 5)
    c12 = Node(data = "Terminal")
    c4.add_child("Strike", c10)
    c4.add_child("Ball", c11)
    c4.add_child("Terminal", c12)

    c13 = Node(data = "Pitcher", info_set = 6)
    c14 = Node(data = "Pitcher", info_set = 7)
    c15 = Node(data = "Terminal")
    c5.add_child("Strike", c13)
    c5.add_child("Ball", c14)
    c5.add_child("Terminal",c15)

    c16 = Node(data = "Pitcher", info_set = 8)
    c17 = Node(data = "Pitcher", info_set = 9)
    c18 = Node(data = "Terminal")
    c6.add_child("Strike", c16)
    c6.add_child("Ball", c17)
    c6.add_child("Terminal", c18)

    pitcher_node = [c7, c8, c10, c11, c13, c14, c16, c17]
    for i, node in enumerate(pitcher_node): 
        bi = Node(data = "Batter", info_set = 1 + i)
        bj = Node(data = "Batter", info_set = 1 + i)
        node.add_child("Fastball",bi)
        node.add_child("Offspeed", child = bj)

    for pitcher in pitcher_node: 
        for i, node in enumerate(pitcher.children.values()): 
            ni = Node(data = "Nature", info_set = 1 + i)
            nj = Node(data = "Nature", info_set = 1 + i)
            node.add_child("Swing", ni)
            node.add_child("Take", nj)

    for pitcher in pitcher_node: 
        for batter in pitcher.children.values(): 
            for nature in batter.children.values(): 
                ti = Node(data = "Terminal")
                nature.add_child("Terminal", ti)

    # still need to make the nature children, and the childrne of nature
    return root

if __name__ == "__main__":
    root = build_tree()
    f = open(file = "C:\\Users\\elidk\\PycharmProjects\\NashEquilibirum\\behavioural\\test_tree.txt", mode = "w")
    root.print_tree(f)
    