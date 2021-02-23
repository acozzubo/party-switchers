# -*- coding: utf-8 -*-
'''
  __________________________________________
 |                                          |
 | Community Analysis on Cadidate Party     |
 | Swtching Network                         |
 | Team: Party Switchers                    |
 | Authors: Angelo Cozzubo - Andrei Bartra  |
 | Responsable: Angelo Cozzubo              |
 | Date: February, 2020                     |
 |__________________________________________|

 =============================================================================
Performs the party community (cluster) analysis and updates the nodes table with 
the community (clusters) id's
 =============================================================================
'''

#  ________________________________________
# |                                        |
# |              1: Libraries              |
# |________________________________________|


import pandas as pd
import networkx as nx
from networkx.algorithms import community as cm
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
# |          4: Cluster Analysis           |
# |________________________________________|

def cluster_analysis():
    '''
    Identifies communities in the network using 
    Clauset-Newman-Moore greedy modularity maximization.
    The biggest community was pationed using the Kernighan–Lin algorithm
    Output:
        df_n: nodes dataframe with cluster id's and cluster lables
        DG: Fiuill Directed NEtwork
    '''
    DG, _, df_n = ns.network_structure(db.db_file, q.all_network, \
                                          q.all_nodes, graph = nx.DiGraph)
    P = DG.to_undirected()

    # Clauset-Newman-Moore greedy modularity maximization
    gmc = cm.greedy_modularity_communities(P, weight=None)

    c_i = 0
    df_n['cluster_gmc'] = 0
    for c in gmc:
        df_n.loc[list(c), 'cluster_gmc'] = c_i
        c_i +=1
    #Kernighan–Lin algorithm on the biggest community
    klb = cm.kernighan_lin_bisection(P.subgraph(list(gmc[0])), seed=1234)
    c_i = 0
    for c in klb:
        df_n.loc[list(c), 'cluster_klb'] = c_i
        c_i +=1 

    df_n['cluster_klb'] = df_n['cluster_klb'].fillna(2).astype(int)
    df_n['clusters'] = pd.factorize(df_n.cluster_gmc*100 + \
                                    df_n.cluster_klb, sort=True)[0] 

    #Merging the smaller commnunities
    df_n.loc[df_n.clusters >= 12, 'clusters' ] = 12

    # Labelling the communities according to the underlying characteristic
    df_n.loc[df_n.clusters == 0, 'cluster_labs'] = 'Strong Regional Left' 
    df_n.loc[df_n.clusters == 1, 'cluster_labs'] = 'Socialist Progresive + AP' 
    df_n.loc[df_n.clusters == 2, 'cluster_labs'] = 'APRA influence'
    df_n.loc[df_n.clusters == 3, 'cluster_labs'] = 'Fujimorism'
    df_n.loc[df_n.clusters == 4, 'cluster_labs'] = 'High Income Liberal Progresive'
    df_n.loc[df_n.clusters == 5, 'cluster_labs'] = 'Podemos Peru Influence'
    df_n.loc[df_n.clusters == 6, 'cluster_labs'] = 'APP Influence'
    df_n.loc[df_n.clusters == 7, 'cluster_labs'] = 'Etnocacerism'
    df_n.loc[df_n.clusters == 8, 'cluster_labs'] = 'P.N.'
    df_n.loc[df_n.clusters == 9, 'cluster_labs'] = 'FONAVI'
    df_n.loc[df_n.clusters == 10, 'cluster_labs'] = 'RUNA'
    df_n.loc[df_n.clusters == 11, 'cluster_labs'] = 'PPS'
    df_n.loc[df_n.clusters == 12, 'cluster_labs'] = 'Other Local Movements'
    return df_n, DG

#  ________________________________________
# |                                        |
# |            5: Degree Measures          |
# |________________________________________|

def neighbor_degree(DG, df_n):
    '''
    Exploting the situation to calculate degree metrics.
    '''
    df_n['neighbor_dg'] = pd.Series(nx.average_neighbor_degree(DG))
    df_n['degree'] = pd.Series(dict(DG.degree))  
    return df_n

#  ________________________________________
# |                                        |
# |              6: DB Update              |
# |________________________________________|

def update_db(df_n):
    '''
    Updating the database with node table with the communities (clusters)
    '''
    conn = sqlite3.connect(db.db_file)

    df_n = df_n.drop(['cluster_gmc','cluster_klb'], axis=1)
    df_n.to_sql('nodes', conn, if_exists = 'replace', index = True)


#  ________________________________________
# |                                        |
# |               7: Wrapper               |
# |________________________________________|

def gen_clusters():
    '''
    Commnunity analysis and database update process
    '''
    df_n, DG = cluster_analysis()
    df_n = neighbor_degree(DG, df_n)
    update_db(df_n)