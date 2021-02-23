# -*- coding: utf-8 -*-
'''
  __________________________________________
 |                                          |
 | Network Coordinates update               |
 | Team: Party Switchers                    |
 | Authors: Andrei Bartra                   |
 | Responsable: Andrei Bartra               |
 | Date: February, 2020                     |
 |__________________________________________|

 =============================================================================
Fixing the nodes coordinates for the full graph by inserting them in the
database
The coordinates are made using a 'Hierarchical' spring layout:
    -First a community level graph is made
    -The coordinates within each communities are added
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
# |            4: Helper Functions         |
# |________________________________________|

def create_coordinates():
    '''
    Computes the coordinates for the full network graph
    Procedure:
        -Spring layout considring a weighted network using the
        communities as nodes
        -For each community a spring layout is computed and added to the
        community coordinates.
    Output:
        df_n: Node dataframe with coordinates columns.
    '''
    coms, _, df_nc = ns.simple_graph(db.db_file, \
                                     q.com_nodes, \
                                     q.com_network, \
                                     nx.Graph)
    com_pos = nx.spring_layout(coms, k=4,iterations=50, weight = 'weight')

    DG, _, df_n = ns.network_structure(db.db_file, q.all_network, \
                                       q.all_nodes, graph = nx.DiGraph)

    df_n['clu_x'] = df_n['clusters'].apply(lambda x: com_pos[x][0])
    df_n['clu_y'] = df_n['clusters'].apply(lambda x: com_pos[x][1])
    df_n['ini_x'] = 0
    df_n['ini_y'] = 0

    for c in com_pos.keys():

        com = list(df_n.loc[df_n.clusters == c].index)

        subgraph = DG.subgraph(com)
        sub_pos = nx.spring_layout(subgraph, iterations=40, scale=0.50)
        
        sub_pos_x = pd.Series({k: v[0] for k, v in sub_pos.items()})
        sub_pos_y = pd.Series({k: v[1] for k, v in sub_pos.items()})

        df_n.loc[df_n.clusters == c, 'ini_x'] = df_n['clu_x'] + sub_pos_x
        df_n.loc[df_n.clusters == c, 'ini_y'] = df_n['clu_y'] + sub_pos_y

    return df_n


def update_db(df_n):
    '''
    updates the SQL database with new coordinates for commnunities and paties
    '''
    conn = sqlite3.connect(db.db_file)
    df_n.to_sql('nodes', conn, if_exists = 'replace', index = True)


def update_candidate_menu():
    '''
    Uploads a table in the database with indexes to be used in user interface
    menu
    '''
    conn = sqlite3.connect(db.db_file)
    c = conn.cursor()
    n_cursor = c.execute(q.candidates)
    header = ns.get_header(c)

    df = pd.DataFrame(n_cursor.fetchall(), columns=header)

    df['name'] = df['nombres'] + ' ' + df['ape_pat'] + ' ' + df['ape_mat']

    df['dist_id'] = df['elec_dist'].rank(method='dense').astype(int) -1

    df = df.loc[df.dist_id > 0]

    df['party_id'] = df['p_name'].rank(method='dense').astype(int) 

    df['groups'] = df['dist_id'].astype(str) + '_' + df['party_id'].astype(str)

    df['cand_id'] = (df.groupby(['groups']).cumcount()+1).astype(int)
    df.to_sql('candidate_menu', conn, if_exists = 'replace', index = True)
    conn.close()

#  ________________________________________
# |                                        |
# |             5: Wrapper Function        |
# |________________________________________|

def nodes_coordinates():
    '''
    Updates the dabase with coordinates for the communities and parties.
    '''
    df_n = create_coordinates()
    update_db(df_n)
    update_candidate_menu()
