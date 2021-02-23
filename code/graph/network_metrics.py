# -*- coding: utf-8 -*-
'''
  __________________________________________
 |                                          |
 | Network Metrics                          |
 | Team: Party Switchers                    |
 | Authors: Mark Richarson                  |
 | Responsable: Mark Richarson              |
 | Date: March, 2020                        |
 |__________________________________________|

 =============================================================================
Computes various network metrics
 =============================================================================
'''
#  ________________________________________
# |                                        |
# |              1: Libraries              |
# |________________________________________|

import sys, os
import networkx as nx
from operator import itemgetter
import pandas as pd

#  ________________________________________
# |                                        |
# |           2: Local Modules             |
# |________________________________________|

import party_switching as ps
import network_structure as ns
import queries as q
import db_config as db

#  ________________________________________
# |                                        |
# |           2: Settings                  |
# |________________________________________|

os.chdir(ps.wd)
sys.path.append(os.chdir(ps.wd))


#  ________________________________________
# |                                        |
# |           2: Helper Funcions           |
# |________________________________________|


def display_info(G):
    '''Display the basic information about the network'''

    print(nx.info(G))


def display_density(G):
    '''Display the density of the network'''

    print("Network Density: ", nx.density(G))


def display_transitivity(G):
    '''Display the transitivity of the network'''

    print("Network Transitivity: ", nx.transitivity(G))

def set_out_degree(G):
    '''Calculate the out degree for each node and add it as a node attribute'''

    out_degree_dict = dict(G.out_degree(G.nodes))
    nx.set_node_attributes(G, out_degree_dict, "out_degree")

    return out_degree_dict


def set_in_degree(G):
    '''Calculate the in degree for each node and add it as a node attribute'''

    in_degree_dict = dict(G.in_degree(G.nodes))
    nx.set_node_attributes(G, in_degree_dict, "in_degree")

    return in_degree_dict


def set_betweeness_centrality(G):
    '''
    Calculate the betweeness centrality for each node and add it as a node
    attribute
    '''

    betweeness_dict = nx.betweenness_centrality(G)
    nx.set_node_attributes(G, betweeness_dict, 'betweeness_centrality')

    return betweeness_dict


def set_eigenvector_centrality(G):
    '''
    Calculate the eigenvector centrality for each node and add it as a node
    attribute
    '''

    eigenvector_dict = nx.eigenvector_centrality(G)
    nx.set_node_attributes(G, eigenvector_dict, "eigenvector_centrality")

    return eigenvector_dict

#  ________________________________________
# |                                        |
# |           3: Compare Centrality        |
# |________________________________________|

def compare_centrality(G, order_by="in_degree"):
    '''Compare the centrality measures of each node'''

    in_degree = "in_degree"
    out_degree = "out_degree"
    betweeness = "betweeness"
    eigenvector = "eigenvector"
    party = "party_name"
    column_names = [party, in_degree, out_degree, betweeness, eigenvector]

    assert order_by in column_names

    in_degree_dict = set_in_degree(G)
    out_degree_dict = set_out_degree(G)
    betweeness_dict = set_betweeness_centrality(G)
    eigenvector_dict = set_eigenvector_centrality(G)

    if order_by == in_degree:
        top_nodes = sorted(in_degree_dict.items(), key=itemgetter(1),
                           reverse=True)[:10]
    elif order_by == out_degree:
        top_nodes = sorted(out_degree_dict.items(), key=itemgetter(1),
                           reverse=True)[:10]
    elif order_by == betweeness:
        top_nodes = sorted(betweeness_dict.items(), key=itemgetter(1),
                           reverse=True)[:10]
    else:
        top_nodes = sorted(eigenvector_dict.items(), key=itemgetter(1),
                           reverse=True)[:10]

    tuples = []

    for node, _ in top_nodes:
        party = G.nodes[node]['p_name']
        in_deg = in_degree_dict[node]
        out_deg = out_degree_dict[node]
        between = betweeness_dict[node]
        eigvec = eigenvector_dict[node]
        tuples.append((party, in_deg, out_deg, between, eigvec))

    df = pd.DataFrame(tuples, columns=column_names)

    return df

#  ________________________________________
# |                                        |
# |            4: Wrapper Function         |
# |________________________________________|

def display_network_metrics(in_degree):
    '''
    Display network metrics on the user interface
    '''

    rv = ns.network_structure(db.db_file, q.all_network, q.all_nodes,
                                   graph=nx.DiGraph)
    G = rv[0]

    G.name = "Party-Switching"
    print("########## NETWORK METRICS ##########")
    print()
    display_info(G)
    print()
    print("-------------------------------------")
    print("########## Connectivity ##########")
    print()
    display_density(G)
    display_transitivity(G)
    print()
    print("########## Centrality Comparison ##########")
    print()
    print("Nodes ordered by", in_degree)
    print("-------------------------------------")
    print()
    df = compare_centrality(G, order_by=in_degree)
    print(df)
