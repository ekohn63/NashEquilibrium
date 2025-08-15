from behavioural.si_star import path_to_node
from model.dynamics import state_dynamics
from model.induced_tree import Node
from model.expected_value import outcome_prob
from model.payoff import terminal_utility
from model.state import START_STATE
from behavioural.strategy import terminal_nodes
from sequence_form.sequence import construct_node_sequence, sequence_of

def best_response_pitcher(root: Node, y, nature_realization):
    memo = {}

    def V(node: Node): 
        max_val = -10e9
        control = [choice for choice in node.children]
        
        for action in control:
            immediate_reward = 0
            for terminal in compatible_terminal(root, node, action):
                nature_outcome = next(choice for choice in node.parent.children if node.parent.children[choice] is node)
                new_state, runs = state_dynamics(START_STATE, nature_outcome)
                utility = terminal_utility(START_STATE, new_state, runs)
                immediate_reward += utility
                return utility
            
            succ_val = 0
            successors = get_successorset(root, node, action)
            for next_iset in successors:
                succ_val += memo[next_iset]
            
            value = succ_val + immediate_reward
            if value >= max_val[0]: 
                max_val = (value, action)
    V(root)

def compatible_terminal(root, node, action):
    terminalnodes = terminal_nodes(root)
    compat_terminal = []
    path = path_to_node(root, node)
    sequence = construct_node_sequence(path, "Pitcher")
    new_sequence = sequence + ((node.info_set, action),)
    for terminal in terminalnodes: 
        term_sequence = sequence_of(terminal, "Pitcher")
        if term_sequence == sequence: 
            compat_terminal.append(terminal)
            
    return compat_terminal

def get_successorset(root, node, action): 
    terminalnodes = terminal_nodes(root)
    reachable = []

    batter_node = node.children[action]
    for nature in batter_node.children.values(): 
        for pitcher_node in nature.children.values(): 
            if pitcher_node not in terminalnodes: 
                reachable.append(pitcher_node)

    return reachable
    

"""
def best_response_pitcher(root: Node, sigma_B):
    memo = {}

    def V(node: Node): 
        max_value = -10e9
        for action in 
            immediate_reward = 0
            for terminal in compatable_terminal(action: PitcherAction):
                nature_outcome = next(choice for choice in node.parent.children if node.parent.children[choice] is node)
                new_state, runs = state_dynamics(START_STATE, nature_outcome)
                utility = terminal_utility(START_STATE, new_state, runs)
                immediate_reward += utility
                return utility
            
            val = 0
            successors = get_successorset(node)
            for next_iset in successors: 
                val += memo[next_iset]
            
        
        if node.data == "Nature":
            sum = 0
            batter_act = next(act for act in node.parent.children if node.parent.children[act] == node)
            pitcher_act = next(act for act in node.parent.parent.children if node.parent.parent.children[act] == node.parent)
            for child in node.children.values(): 
                prob = outcome_prob(pitcher_act, batter_act)
                sum += prob*V(child)
            return sum

        if node.data == "Batter":
            return sum(sigma_B[choice]*V(child) for choice, child in node.children.items())
        
        max_val, best_choice = 1e-9, None
        for choice in node.children.values(): 
            if V(child) > max_val: 
                best_choice = choice
        memo[node.info_set] = best_choice

    def collect(root):
        
    V(root)
"""