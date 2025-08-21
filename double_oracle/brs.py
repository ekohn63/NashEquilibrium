from collections import defaultdict
from behavioural.si_star import path_to_node
from model.dynamics import state_dynamics
from model.induced_tree import Node, get_num_infosets, is_terminal_node
from model.nature import get_outcome_prob
from model.payoff import terminal_utility
from model.state import START_STATE
from behavioural.strategy import terminal_nodes
from sequence_form.sequence import construct_node_sequence, sequence_of

def best_response_pitcher(root: Node, x, battersequences, nature_behave):
    # memo = defaultdict(int)
    value_cache = {}
    policy = {}
    succ_prob = {}
    num_pitcher_infosets = get_num_infosets(root, "Pitcher")

    def V(node: Node):         
        #----Base case--------
        if is_terminal_node(node):
            return 0.0
        
        if node.data != "Pitcher":
            # Not a pitcher decision node: recurse over all children and take expectation
            # w.r.t opponent/nature is NOT needed for value recursion here because
            # your get_successorset(...) handles the coupling under pitcher actions.
            # We just propagate to children to reach pitcher nodes.
            # For strictness we could take a max/exp here if needed, but the BR recursion
            # is defined only at pitcher info sets.
            best_downstream = 0.0
            for child in node.children.values():
                best_downstream = max(best_downstream, V(child))  # harmless; won't affect BR correctness
            return best_downstream

        iset_id = node.info_set
        if node.info_set in value_cache: 
            return value_cache[node.info_set]

        min_val = float("inf")
        best_actions = []
        control = [choice for choice in node.children]
        print(f"iset_id: {iset_id}, control: {control}")

        for action in control:
            immediate_reward = 0.0
            for terminal in compatible_terminal(root, node, action):
                utility = get_term_utility(terminal)
                prob = get_stochastic_prob(node, terminal, x, battersequences, nature_behave)
                #print(f"\033[91m utility: \033[0m {utility} , \033[94m prob: \033[0m {prob}")
                immediate_reward += utility*prob
                #print(immediate_reward)

            succ_val = 0.0
            successors = get_successorset(root, node, action)
            for next_iset in successors:
                prob = get_stochastic_prob(node, next_iset, x, battersequences, nature_behave)
                next_val = V(next_iset)
                print(f"iset: {iset_id}, action: {action}, prob: {prob}, next_val: {next_val}")
                succ_prob[next_iset.info_set] = prob
                succ_val += next_val*prob
            
            value = succ_val + immediate_reward

            # Track argmax with tolerance for numerical ties
            if value < min_val - 1e-12:
                min_val = value
                best_actions = [action]
            elif abs(value - min_val) <= 1e-12:
                best_actions.append(action)

            print(f"iset = {iset_id}, action = {action}, value = {value}")

        policy[iset_id] = best_actions[0]

        value_cache[iset_id] = min_val
        print(f"value_cache[iset_id]: {value_cache[iset_id]}, value_chache: {value_cache}")

        return min_val

    best_value = V(root)

    print(f"value_cache: {value_cache}, prob: {succ_prob}")

    return best_value, policy

def get_stochastic_prob(node, next_iset, x, battersequences, nature_behave):
    batter = sequence_of(next_iset, "Batter")
    nature = sequence_of(next_iset, "Nature")

    batter_old = sequence_of(node, "Batter")
    nature_old = sequence_of(node, "Nature")

    if x[battersequences.index(batter_old)] != 0:
        batter_prob = x[battersequences.index(batter)]/x[battersequences.index(batter_old)]
    else: 
        batter_prob = 0

    nature_iset = nature[-1][0]
    nature_prob = nature_behave[nature_iset][nature[-1][-1]]

    #print(f"\033[91m prob: {batter_prob}, {type(batter_prob)} \033[0m , nature = {nature_prob}, {type(nature_prob)}")
    prob = batter_prob * float(nature_prob)

    return (prob)

def compatible_terminal(root, node, action):
    terminalnodes = terminal_nodes(root)
    compat_terminal = []
    sequence = sequence_of(node, "Pitcher")
    if node.parent == None:
        new_sequence = ((node.info_set, action),)
    else:
        new_sequence = sequence + ((node.info_set, action),)
    for terminal in terminalnodes: 
        term_sequence = sequence_of(terminal, "Pitcher")
        if term_sequence == new_sequence: 
            compat_terminal.append(terminal)
    return compat_terminal

def get_term_utility(terminal: Node):
    nature_outcome = next(choice for choice in terminal.parent.children if terminal.parent.children[choice] is terminal)
    #print(nature_outcome)
    new_state, runs = state_dynamics(START_STATE, nature_outcome)
    utility = terminal_utility(START_STATE, new_state, runs)
    return utility


def get_successorset(root, node, action): 
    terminalnodes = terminal_nodes(root)
    reachable = []

    batter_node = node.children[action]
    for nature in batter_node.children.values(): 
        for pitcher_node in nature.children.values(): 
            if pitcher_node not in terminalnodes: 
                reachable.append(pitcher_node)

    return reachable