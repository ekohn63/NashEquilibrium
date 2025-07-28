

#constructing pitcher constraint matrix F, and batter constraint matrix E

# pitcher matrix F
def pitcher_constraint_matrix(root, set_sequences: list):

    return


# batter matrix E
def batter_constraint_matrix(root, sequencelist:list): 
    num_infosets = get_num_infosets()
    E = np.zeros((num_infosets, len(sequencelist)), dtype = np.float64)
    E[0, 0] = 1
    return


