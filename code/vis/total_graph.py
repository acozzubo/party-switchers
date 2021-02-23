# -*- coding: utf-8 -*-
'''
  __________________________________________
 |                                          |
 | Network visualizations                   |
 | Team: Party Switchers                    |
 | Authors: Angelo Cozzubo - Andrei Bartra  |
 | Responsable: Angelo Cozzubo              |
 | Date: February, 2020                     |
 |__________________________________________|

 =============================================================================
Builds the full network graph and the candidate highlight graph
 =============================================================================
'''
import numpy as np
import pandas as pd
import networkx as nx
import pydot
import seaborn as sb
import matplotlib.pyplot as plt
import matplotlib
import os, sys
import sqlite3

#  ________________________________________
# |                                        |
# |             2: Local Modules           |
# |________________________________________|

import queries as q
import db_config as db
import network_structure as ns 
import party_switching as ps 

#  ________________________________________
# |                                        |
# |               3: Settings              |
# |________________________________________|

os.chdir(ps.wd)
sys.path.append(os.chdir(ps.wd))

#  ________________________________________
# |                                        |
# |             3: Helper Functions        |
# |________________________________________|

def fetch_candidate(dist_id, party_id, cand_id):
    '''
    Retrieves the candidate id and the candidate name from the SQL database,
    using the indexes selected by the user.
    '''
    conn = sqlite3.connect(db.db_file)
    c = conn.cursor()
    n_cursor = c.execute("SELECT * FROM candidate_menu")
    header = ns.get_header(c)

    df = pd.DataFrame(n_cursor.fetchall(), columns=header)
    conn.close()

    rv = df.loc[(df.dist_id == dist_id) & \
                (df.party_id == party_id) &\
                (df.cand_id == cand_id), ['id_hdv', 'name'] ].values[0]
    return tuple(rv)


def get_trajectory(id_hdv):
    '''
    Retrieves the candidate party switching trajectory in a string format
    ready for display
    '''
    conn = sqlite3.connect(db.db_file)
    c = conn.cursor()
    query = 'SELECT year, p_name, type FROM edges WHERE id_hdv == "{}"'. \
             format(id_hdv)
    n_cursor = c.execute(query)
    header = ns.get_header(c)
    moves = pd.DataFrame(n_cursor.fetchall(), columns=header)
    moves.loc[moves.type == 'current', 'year'] = 2020
    moves = moves.sort_values('year')
    
    path = '\n'.join(['{}: {} ({})'.format(y,p,t) for y, p, t \
                      in moves.itertuples(index = False, name=None)])
    conn.close()
    return path     


#  ________________________________________
# |                                        |
# |             4: Graph Functions         |
# |________________________________________|

def total_graph(pos_only=False):
    '''
    Creates the full netowrk graph coloring the nodes by community
    '''
    DG, df_e, df_n = ns.network_structure(db.db_file, q.all_network, \
                                          q.all_nodes, graph = nx.DiGraph)

    pos = {n :(df_n.loc[n,'ini_x'], df_n.loc[n,'ini_y']) for n in df_n.index}

    ##Set plt and style
    plt.style.use('seaborn-paper')
    fig, ax = plt.subplots(1, 1, figsize=(12, 7)) 

    ## Position type, nodes, edges and labels

    n = max(df_n['clusters']) +1 
    
    from_list = matplotlib.colors.LinearSegmentedColormap.from_list 
    cm = from_list(None, plt.cm.tab20(range(0,n)), n)

    ec = nx.draw_networkx_edges(DG, pos, alpha=0.05)
    nc = nx.draw_networkx_nodes(DG, pos, nodelist=DG.nodes(),
                                node_color=list(df_n['clusters']), 
                                alpha=0.8, 
                                node_size=list(df_n['degree']*5), 
                                cmap=cm,
                                vmin = -0.5,
                                vmax = n - 0.5)

    ##Groups colorbar
    df_n = df_n.sort_values(by = ['clusters', 'degree', 'node']) 

    cbar = fig.colorbar(nc, spacing='uniform', 
                        ticks=list(df_n['clusters'].unique()))
    #ax.set_yticks(df_n['clusters'].unique() + 0.5, minor=False)


    cbar.ax.set_yticklabels(list(df_n['cluster_labs'].unique()))

    ##Title, annotations and labels
    ax.set_title('Party Switchers Network and Clusters by Greedy Modularity*', \
                  fontsize=15, ha='center')

    plt.annotate('    Note: Composed Spring Layout. \n\
    Network with {} parties (nodes) and {} \
    candidates (edges) \n\
    Node size proportional to its degree (adjacent edges) \n \
    *The biggest cluster was diveded using Kernighan Lin bisection: \n\
    Strong Regional Left and Socialist Progressive + AP'. 
                 format(nx.number_of_nodes(DG), nx.number_of_edges(DG)), \
                 (0,0), (0, -10), xycoords='axes fraction', \
                 textcoords='offset points', va='top')
    ax.yaxis.set_label_position("right")
    ax.set_ylabel('Party Clusters', size=10)
    
    ##Save as image 
    plt.savefig("output/total_graph.png", format="PNG", dpi=500)
    plt.show()


def cluster_graph(k=4, pos_only = False):
    '''
    Creates the community level netowrk graph coloring the nodes by community
    '''
    coms, df_ec, df_nc = ns.simple_graph(db.db_file, \
                                         q.com_nodes_coords, \
                                         q.com_network, \
                                         nx.Graph)

    df_nc['degree'] = pd.Series(dict(coms.degree(weight = 'weight')))


    pos = {n :(df_nc.loc[n,'clu_x'], df_nc.loc[n,'clu_y']) for n in df_nc.index}

    plt.close()
    
    ##Set plt and style
    plt.style.use('seaborn-paper')
    fig, ax = plt.subplots(1, 1, figsize=(12, 7)) 

    ## Position type, nodes, edges and labels
     # alternative: spring_layout 

    widths = [ d['weight'] for (u,v,d) in coms.edges(data=True)]
    n = max(df_nc.index) +1
    from_list = matplotlib.colors.LinearSegmentedColormap.from_list 
    cm = from_list(None, plt.cm.tab20(range(0,n)), n)

    ec = nx.draw_networkx_edges(coms, pos, width = widths, alpha = 0.1 )
    nc = nx.draw_networkx_nodes(coms, pos, nodelist=coms.nodes(),
                                node_color=list(df_nc.index), 
                                alpha=0.6, 
                                node_size=list(df_nc['degree']*30), 
                                cmap=cm,
                                vmin = -0.5,
                                vmax= n-0.5)

    ##Groups colorbar

    cbar = fig.colorbar(nc, spacing='proportional',
                        ticks=list(df_nc.index))

    cbar.ax.set_yticklabels(list(df_nc['cluster_labs'])) 

    ##Title, annotations and labels
    ax.set_title('Party Switchers Clusters by Greedy Modularity*', \
                  fontsize=15, ha='center')

    plt.annotate('    Note: Spring Layout. \n\
    Network with {} Clusters (nodes) and {} \
    candidates movements (weigthed edges) \n\
    Node size proportional to its degree (adjacent edges) \n \
    Edge size proportinal to the number of movements \n\
    *The biggest cluster was diveded using Kernighan Lin bisection: \n\
    Strong Regional Left and Socialist Progressive + AP'. 
                 format(nx.number_of_nodes(coms), nx.number_of_edges(coms)), \
                 (0,0), (0, -12), xycoords='axes fraction', \
                 textcoords='offset points', va='top')
    ax.yaxis.set_label_position("right")
    ax.set_ylabel('Party Clusters', size=10)
    
    ##Save as image 
    plt.savefig("output/cluster_graph.png", format="PNG", dpi=499)
    plt.show()
    return


def candidate_graph(dist_id, party_id, cand_id):
    '''
    Highlights a particular candidate in the full network graph 
    '''
    id_hdv, name = fetch_candidate(dist_id, party_id, cand_id)

    DG, df_e, df_n = ns.network_structure(db.db_file, q.all_network, \
                                          q.all_nodes, graph = nx.DiGraph)

    cand_nodes = set(df_e.loc[df_e.id_hdv == id_hdv, 'source'].unique()) | \
                 set(df_e.loc[df_e.id_hdv == id_hdv, 'target'].unique())

    cand_edges = list(df_e.loc[df_e.id_hdv == id_hdv, \
                               ['source','target']].itertuples(index=False, \
                                                               name=None))    
    path = get_trajectory(id_hdv)

    pos = {n :(df_n.loc[n,'ini_x'], df_n.loc[n,'ini_y']) for n in df_n.index}

    ##Set plt and style
    plt.style.use('seaborn-paper')
    fig, ax = plt.subplots(1, 1, figsize=(12, 7)) 
    plt.subplots_adjust(bottom=0.20)
    ## Position type, nodes, edges and labels

    n = max(df_n['clusters']) +1 
    
    from_list = matplotlib.colors.LinearSegmentedColormap.from_list 
    cm = from_list(None, plt.cm.tab20(range(0,n)), n)

    ec = nx.draw_networkx_edges(DG, pos, alpha=0.05)
    nc = nx.draw_networkx_nodes(DG, pos, nodelist=DG.nodes(),
                                node_color=list(df_n['clusters']), 
                                alpha=0.3, 
                                node_size=list(df_n['degree']*5), 
                                cmap=cm,
                                vmin = -0.5,
                                vmax = n - 0.5)


    nx.draw_networkx_nodes(DG,pos,nodelist=list(cand_nodes),node_color='r', alpha = 0.8, node_size = 20)
    nx.draw_networkx_edges(DG,pos,edgelist=cand_edges,edge_color='r',width=1, alpha = 0.8)

    ##Groups colorbar
    df_n = df_n.sort_values(by = ['clusters', 'degree', 'node']) 

    cbar = fig.colorbar(nc, spacing='uniform', 
                        ticks=list(df_n['clusters'].unique()))
    #ax.set_yticks(df_n['clusters'].unique() + 0.5, minor=False)


    cbar.ax.set_yticklabels(list(df_n['cluster_labs'].unique()))

    ##Title, annotations and labels
    ax.set_title('Political path of candidate {}'.format(name), \
                  fontsize=15, ha='center')

    plt.annotate('Trajectory: \n{}'.format(path), \
                 (0,0), (0, -10), xycoords='axes fraction', \
                 textcoords='offset points', va='top')
    ax.yaxis.set_label_position("right")
    ax.set_ylabel('Party Clusters', size=10)
    
    ##Save as image 
    plt.savefig("output/total_graph.png", format="PNG", dpi=500)
    plt.show()

