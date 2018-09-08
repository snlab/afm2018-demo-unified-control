#!/usr/bin/env python2

import sys
import math
import networkx as nx
import matplotlib.pyplot as plt
import argparse
import yaml

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Topology viewer")
    parser.add_argument("config", type=str, help="Topology configuration file")
    parser.add_argument("--output","-o", type=str, default=None, help="Output png file")
    args = parser.parse_args()
    outputfile = args.output
    with open(args.config) as fp:
        config = yaml.safe_load(fp)


    topo = nx.Graph()

    switches = config["switches"]
    hosts = config["hosts"].keys()
    topo.add_nodes_from(switches)
    topo.add_nodes_from(hosts)

    links = [(link["endpoint1"]["node"],link["endpoint2"]["node"]) for link in config["links"]]

    topo.add_edges_from(links)

    labels = {}
    for n in topo.adj:
        labels[n] = n
    # pos = nx.spring_layout(topo)
    pos = nx.fruchterman_reingold_layout(topo, center=(0, 0))

    # nx.draw(topo, pos=pos)
    ax = plt.gca()
    ax.set_axis_off()

    nx.draw_networkx_nodes(topo, nodelist=hosts, pos=pos,node_color='g',node_shape="^",node_size=100)
    nx.draw_networkx_nodes(topo, nodelist=switches, pos=pos, node_color='r', node_shape=".")
    sw_sw = []
    sw_host = []
    for link in links:
        if link[0] in hosts or link[1] in hosts:
            sw_host.append(link)
        else:
            sw_sw.append(link)
    nx.draw_networkx_edges(topo, edgelist=sw_sw, pos=pos, edge_color='k',style='-')
    nx.draw_networkx_edges(topo, edgelist=sw_host, pos=pos, edge_color='b', style='--')
    nx.draw_networkx_labels(topo, pos, labels=labels)
    if outputfile:
        plt.savefig(outputfile)
    plt.show()
