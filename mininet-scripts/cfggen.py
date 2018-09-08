#!/usr/bin/env python2

import sys
import math
import networkx as nx
import matplotlib.pyplot as plt
import argparse
import yaml

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Topology configuration file generator")
    parser.add_argument("source", type=str, help="GraphML file")
    parser.add_argument("--output","-o", type=str, default=None, help="Output YAML file")
    parser.add_argument("--ratio","-r", type=float, default=0.0,
                        help="Ratio of the radius that compute which nodes not to attach host")
    args = parser.parse_args()
    outputfile = args.output
    topo = nx.read_graphml(args.source).to_undirected()
    labels = {}
    for n in topo.adj:
        labels[n] = n
    # pos = nx.spring_layout(topo)
    pos = nx.fruchterman_reingold_layout(topo, center=(0, 0))

    nx.draw(topo, pos=pos)
    nx.draw_networkx_labels(topo, pos, labels=labels)
    # plt.savefig(topology_name+'-topo.png')
    plt.show()

    switches = [str(n) for n in topo.adj]

    linkmap = dict()
    for link, attr in topo.edges.items():
        id = attr['id']
        if id not in linkmap:
            linkmap[id] = {"endpoint1": {"node": link[0]},
                           "endpoint2": {"node": link[1]}}
    linklist = linkmap.values()

    hostmap = dict()
    tmp = {(n, math.sqrt(p[0] ** 2 + p[1] ** 2)) for n, p in pos.items()}
    tmp = sorted(tmp, key=lambda t: t[1], reverse=True)
    delta = tmp[0][1] * args.ratio
    for i, a in enumerate(tmp, 1):
        node = a[0]
        hostname = "h" + str(node)
        hostmap[hostname] = {"ip": "10.0.0.%d" % i, "type": "default"}
        linklist.append({"endpoint1": {"node": hostname},
                         "endpoint2": {"node": str(node)}})
        if a[1] < delta:
            break

    for l in linklist:
        l['bw'] = 1000

    if outputfile:
        fp = open(outputfile, 'w')
    else:
        fp = sys.stdout

    yaml.dump({"switches": switches,
               "hosts": hostmap,
               "links": linklist}, fp)
