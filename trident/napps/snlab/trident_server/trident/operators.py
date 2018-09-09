
from napps.snlab.trident_server.trident.objects import Table

def coalesce(x, y):
    """
    coalesce: coalesces two wildcard values x and y into a single wildcard
    value where possible. Returns None if the two wildcard values conflict.
    """

    if len(x) != len(y):
        return None

    output = ""
    for i, j in zip(x, y):
        if i == j:
            output += i
        elif i == 'x':
            output += j
        elif j == 'x':
            output += i
        else:
            return None

    return output

def rule_union(ax, ay, rx, ry, ajoin):

    """
    rule_union: Computes the union of two rules, coalescing any shared attributes.
    ax: Rule 1's attributes
    ay: Rule 2's attributes
    rx: Rule 1's values
    ry: Rule 2's values
    ajoin: The union of Rule 1 and Rule 2's attributes

    returns rjoin: The union of Rule 1 and Rule 2's values, coalescing shared attributes
    """
    
    PRI_IND = 0    #Priority is always the first value in a rule
    FIRST_ATTR_IND = 1 #Attributes start from index 1
    
    rjoin = np.zeros(len(ajoin), dtype=object)  #rjoin: The rule union
    rjoin[PRI_IND] = str(int(rx[PRI_IND]) + int(ry[PRI_IND]))
    
    for i in range(1, len(ajoin)): #Don't join priority
        rx_ind = np.where(ax == ajoin[i])[0]
        ry_ind = np.where(ay == ajoin[i])[0]
        #print "Attr:{}, rx_ind:{}, ry_ind:{}".format(ajoin[i], rx_ind, ry_ind)
        
        if len(rx_ind) > 0 and len(ry_ind) > 0:
            rjoin[i] = coalesce(rx[rx_ind[0]], ry[ry_ind[0]])
            #print "coalesce:{} and {} -> {}".format(rx[rx_ind[0]], ry[ry_ind[0]], rjoin[i])
            if rjoin[i] == None:
                return None
        elif len(rx_ind) > 0:
            rjoin[i] = rx[rx_ind[0]]
        else: 
            rjoin[i] = ry[ry_ind[0]]

    return rjoin

def is_value_blocked(hi_v, lo_v):
    """
    Checks if value hi_v blocks rule low_r.
    """
    for hi_vi, lo_vi in zip(hi_v, lo_v):
        if (lo_vi == 'x' and (hi_vi == '0' or hi_vi == '1')) \
                or (lo_vi == '0' and hi_vi == '1') \
                or (lo_vi == '1' and hi_vi == '0'):
            return False
    return True

def is_rule_single_rule_blocked(hi_rs, lo_r, key_attr_no):
    """
    is_rule_single_rule_blocked: checks to see if any rules in hi_rs block
    rule lo_r. ASSUMES THAT THE FIRST key_attr_no ATTRIBUTES ARE THE KEY
    ATTRIBUTES. ASSUMES THAT THE FIRST VALUE IN EACH RULE IS PRIORITY.
    """

    if key_attr_no == 0:
        return False

    for hi_r in hi_rs:
        if int(hi_r[0]) >= int(lo_r[0]): #If hi_r has higher priority than lo_r
            is_blocked = True
            for i in range(1, key_attr_no+1):
                is_blocked = is_blocked and is_value_blocked(hi_r[i], lo_r[i])
            if is_blocked:
                return True
    return False

def never_prune(rules, rxy, key_attr_no):
    return False
    
def flow_join(tx, ty, is_pruned=is_rule_single_rule_blocked):
    
    """
    flow_join: Combines two tables, tx and ty, to generate a table equivalent to executing
    tx folowed by ty. The domain of any shared attributes must be equal, or behavior is 
    undefined. Pruning algorithm specified by is_pruned (defaults to is_rule_single_rule_blocked).
    """

    #Calculate combined key
    key = []

    for attr_i in tx.get_key():
        key.append(attr_i)

    for attr_i in ty.get_key():
        if attr_i not in tx.get_attr():
            key.append(attr_i)

    #print "key:{}".format(key)

    #Calculate combined attr
    attr = ["pri"] + key[:]
    
    for attr_i in tx.get_attr():
        if attr_i not in attr:
            attr.append(attr_i)

    for attr_i in ty.get_attr():
        if attr_i not in attr:
            attr.append(attr_i)

    #print "attr:{}".format(attr)

    #Calculate combined rules
    rules = []
    key_attr_no = len(key) #Number of attributes in txy's key, needed for pruning
    for rx in tx.get_rules():
        for ry in ty.get_rules():
            rxy = rule_union(tx.get_attr(), ty.get_attr(), rx, ry, attr)
            if rxy is not None and not is_pruned(rules, rxy, key_attr_no):
                rules.append(rxy)
     
    #The loop above is not strictly executed in priority order
    rules1 = []
    for r in sorted(rules, cmp=lambda x,y:cmp(-int(x[0]), -int(y[0]))):
        if not is_pruned(rules1, r, key_attr_no):
            rules1.append(r)

    #Construct table
    txy = Table(attr, key)
    txy.add_rules(rules1)
    return txy

def special_join(tx, ty, special_key):
    
    """
    flow_join for special case, where the table tx and ty must share at least one common 
    input, whose rules follow the pattern: exact value + wildcards

    assume the rules are sorted in descending order of priority
    """

    #Calculate combined key
    key = []

    for attr_i in tx.get_key():
        key.append(attr_i)

    for attr_i in ty.get_key():
        if attr_i not in tx.get_attr():
            key.append(attr_i)
    
    #Calculate combined attr
    attr = ["pri"] + key[:]

    for attr_i in tx.get_attr():
        if attr_i not in attr:
            attr.append(attr_i)

    for attr_i in ty.get_attr():
        if attr_i not in attr:
            attr.append(attr_i)

    rules = []
    key_attr_no = len(key)

    special_indx = np.where(tx.get_attr() == special_key)[0][0]
    special_indy = np.where(ty.get_attr() == special_key)[0][0]

    #Build up dictionary for ty
    info = dict()
    ry_ind = 0

    for ry in ty.get_rules():
        v = str(ry[special_indy]).split("x")[0]
        if len(v) == 0:
            continue
        info[v] = ry_ind
        ry_ind += 1

    #Copy and calculate rules from tx
    for rx in tx.get_rules():
        v = str(rx[special_indx]).split("x")[0]
        for i in range(1, len(v) + 1):
            if info.has_key(v[0:i]):
                ry = ty.get_rules()[info.get(v[0:i])]
                rxy = rule_union(tx.get_attr(), ty.get_attr(), rx, ry, attr)
                rules.append(rxy)
        ry = ty.get_rules()[ry_ind]
        rxy = rule_union(tx.get_attr(), ty.get_attr(), rx, ry, attr)
        rules.append(rxy)
    
    #Build up dictionary for tx
    info = dict()
    rx_ind = 0

    for rx in tx.get_rules():
        v = str(rx[special_indx]).split("x")[0]
        if len(v) == 0:
            continue
        info[v] = rx_ind
        rx_ind += 1

    #Copy and calculate rules from ty
    for ry in ty.get_rules():
        v = str(ry[special_indy]).split("x")[0]
        for i in range(1, len(v) + 1):
            if info.has_key(v[0:i]):
                rx = tx.get_rules()[info.get(v[0:i])]
                rxy = rule_union(tx.get_attr(), ty.get_attr(), rx, ry, attr)
                rules.append(rxy)
        rx = tx.get_rules()[rx_ind]
        rxy = rule_union(tx.get_attr(), ty.get_attr(), rx, ry, attr)
        rules.append(rxy)

    #Construct table
    txy = Table(attr, key)

    #Remove duplication
    rules1 = []
    dup = dict()
    special_indxy = np.where(txy.get_attr() == special_key)[0][0]

    for r in sorted(rules, cmp=lambda x,y:cmp(-int(x[0]), -int(y[0]))):
        v = str(r[special_indxy]).split("x")[0]
        if dup.has_key(v):
            continue
        else:
            rules1.append(r)
            dup[v] = True;

    txy.add_rules(rules1)

    return txy
