

#[(2, {'sip': '10.0.0.2', 'dip': '10.0.0.1', 'sport': 4, 'dport': 80, 'proto': 22}, [('00:00:00:00:00:00:00:01', 1), ('00:00:00:00:00:00:00:02', 4)]), (2, {'sip': '10.0.0.1', 'dip': '10.0.0.2', 'sport': 80, 'dport': 4, 'proto': 22}, [('00:00:00:00:00:00:00:02', 1), ('00:00:00:00:00:00:00:01', 4)])]

def convert_format(table):
    rules = table.rules
    # print(table)
    field = ['sip','dip','sport','dport','proto']
    ret = []
    for item in rules:
        priority = int(item[0])
        match = {}
        for i in range(5):
            if item[i+1]!='*':
                match[field[i]] = item[i+1]
        path = []
        for ff in item[6]:
            if len(ff[0])==23:
                outputs = ff[2]
                for output in outputs:
                    path.append((ff[0],int(output)))
        ret.append((priority, match, path))
    return ret
