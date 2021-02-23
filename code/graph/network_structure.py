# -*- coding: utf-8 -*-
'''
  __________________________________________
 |                                          |
 | Query to Network Function                |
 | Team: Party Switchers                    |
 | Authors: Marc Richardson                 |
 | Responsable: Marc Richardson             |
 | Date: February, 2020                     |
 |__________________________________________|

 =============================================================================
Function that creates a network object from a valid query of the database.
The query must be at a candidate-link level. It must have the candidate unique
id, the origin and destiny party and should allow for additional attributes. It
must output the intermediate pandas dataframe and the networkx object at demand.
 =============================================================================
'''
#  ________________________________________
# |                                        |
# |              1: Libraries              |
# |________________________________________|

import os, sys
import networkx as nx
import pandas as pd
import sqlite3


#  ________________________________________
# |                                        |
# |            2: Local Modules            |
# |________________________________________|

import party_switching as ps
import db_config as db

#  ________________________________________
# |                                        |
# |               3: Settings              |
# |________________________________________|

#Current path
os.chdir(ps.wd)
sys.path.append(os.chdir(ps.wd))
db_dile = db.db_file

#  ________________________________________
# |                                        |
# |           4: Helper Functions          |
# |________________________________________|

def get_header(cursor):
    """
    Given a cursor object, returns the columns header of the last query
    """

    header = []

    for i in cursor.description:
        s = i[0]
        if "." in s:
            s = s[s.find(".")+1:]
        header.append(s)

    return header


#  ________________________________________
# |                                        |
# |        5: Query Validation Helper      |
# |________________________________________|

def is_header_valid(header, edge=True):
    """
    Validate the SQL query by determining whether it includes the appropriate
    columns and is at the candidate-link level

    :param header: (list of strings) column names
    :param edge: (bool) If True, validation check is for edge query. If False,
                 validation check is for node query

    :return: (bool) True if header includes priority columns. False if otherwise
    """
    if edge:
        priority_cols = ['id_hdv', 'source', 'target', 'year']
    else:
        priority_cols = ['node']

    return all(map(lambda x: x in header, priority_cols))


def is_unique(df, edge=True):
    """
    Check that all records in executed edge or node query are unique.

    :param df: (pd.DataFrame) contains node or edge data
    :param edge: (bool) If True, count unique rows for edges query. If False,
                 count unique rows for nodes query

    :return: (bool) True if rows are unique. False if otherwise
    """

    num_records = len(df)

    if edge:
        grouped_df = df.groupby(by=['id_hdv', 'source', 'target', 'year'])
        grouped_df = grouped_df.size().to_frame().reset_index()
    else:
        grouped_df = df.groupby(by=['node'])
        grouped_df = grouped_df.size().to_frame().reset_index()

    return len(grouped_df) == num_records


def has_erroneous_values(df, c, edge=True):
    """
    Check whether the executed query has erroneous values in the priority
    columns.

    :param df: (pd.DataFrame)
    :param c: (cursor object)
    :param edge: (bool) If True, check values for edges query. If False, check
                 values for nodes query

    :return: (bool) True if there are erroneous values. False if otherwise
    """

    num_records = len(df)

    if edge:
        query = ''' SELECT * FROM network '''
        r = c.execute(query)
        header = get_header(c)
        full_df = pd.DataFrame(r.fetchall(), columns=header)
        merged_df = pd.merge(df, full_df, how='inner',
                             on=['id_hdv', 'source', 'target', 'year'])
    else:
        query = ''' SELECT * FROM nodes '''
        r = c.execute(query)
        header = get_header(c)
        full_df = pd.DataFrame(r.fetchall(), columns=header)
        merged_df = pd.merge(df, full_df, how='inner', on='node')

    return len(merged_df) != num_records


#  ________________________________________
# |                                        |
# |            6: Query Validation         |
# |________________________________________|


def validate_edge_query(header, records, c):
    """
    Check that the edge query is producing valid results.

    :param header: (list of strings) column headers to create DataFrame
    :param records: (list of tuples) values to use to fill DataFrame
    :param c: (cursor object)

    :return: (pd.DataFrame) Edge data with unique rows, no erroneous values, and
             necessary columns. Allows for additional attribute columns.
             If edge query is invalid, returns None.
    """

    # Validate header (executed query includes necessary columns)
    if is_header_valid(header):
        df = pd.DataFrame(records, columns=header)
    else:
        print("Query error: Query must include 'id_hdv', 'origin', 'destiny',"
              "and 'year' attributes")
        return None
    # Validate unique rows in executed query
    if not is_unique(df):
        print("Query error: Query contains duplicate rows")
        return None
    # Validate entries in records (no erroneous values)
    if has_erroneous_values(df, c):
        print("Query error: Query produces erroneous values not in database")
        return None

    return df


def validate_node_query(header, records, c):
    """
    Check that the node query is valid.

    :param header: (list of strings) column headers to create DataFrame
    :param records: (list of tuples) values to use to fill DataFrame
    :param c: (cursor object)

    :return: (pd.DataFrame) Node data with unique rows, no erroneous values, and
             necessary columns. Allows for additional attribute columns.
             If node query is invalid, returns None.
    """

    # Validate header (executed query includes necessary columns)
    if is_header_valid(header, edge=False):
        df = pd.DataFrame(records, columns=header)
    else:
        print("Query error: Query must include 'node' columns")
        return None
    # Validate unique rows in executed query
    if not is_unique(df, edge=False):
        print("Query error: Query contains duplicate rows")
        return None
    # Validate entries in records (no erroneous values)
    if has_erroneous_values(df, c, edge=False):
        print("Query error: Query produces erroneous values not in database")
        return None

    return df

#  ________________________________________
# |                                        |
# |             7: Graph Builder           |
# |________________________________________|

def build_graph(edge_df, node_df, graph_type=nx.Graph):
    """
    Build a graph from edge dataframe and node dataframe

    :param edge_df: (pd.DataFrame) edges records
    :param node_df: (pd.DataFrame) nodes records
    :param graph_type: (networkx graph class) graph class to use to build graph

    :return: networkx graph object
    """

    node_df.set_index('node', inplace=True) # sets index using 'node' column
    G = nx.from_pandas_edgelist(edge_df, edge_attr=True,
                                create_using=graph_type)

    for col in node_df.columns: # all remaining columns are added as node attrs
        nx.set_node_attributes(G, node_df[col], col)

    return G

#  ________________________________________
# |                                        |
# |               8: Wrapper               |
# |________________________________________|



def network_structure(db_file, edge_query, node_query, \
                      graph=nx.Graph, edge_only=False):
    """
    Validate edge and node queries and, if queries are valid, generate a
    networkx object of the class specified by 'graph' keyword. The function
    also allows the edge pd.DataFrame and node pd.DataFrame returned along with
    the graph object

    Required Query formats:
    Edges:
        Columns: 'id_hdv', 'source', 'target', 'year', <attributes>
        Unique: 'id_hdv', 'source', 'target', 'year'
        Other: The combination of 'id_hdv', 'origin', 'destiny', 'year'
               should be a valid register in the network table in the database
    Nodes
        Columns: 'node', <attribute>
        Unique: 'node'
        Other: The node must be a valid register in the node table in the
               database

    The set of unique nodes in the edges table should be the same as the set of
    nodes in the nodes table.


    :param db_file: (str) filename for database to query
    :param edge_query: (str) SQL query to execute for edges
    :param node_query: (str) SQL query to execute for nodes
    :param graph: (networkx graph class) graph class to use to build graph
    :param edge_only: (bool) validate only the edge query and return only the
                      the edge pd.DataFrame. Defaults to False.

    :return: Either the edge pd.DataFrame or the networkx Graph object and both
             the edge and node pd.DataFrame
    """

    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    try:  # Try to execute the edge query, return None if it fails to execute
        edge_r = c.execute(edge_query)
    except:
        print("Query error: SQL cannot execute edge query")
        return None
    edge_header = get_header(c)
    edge_records = edge_r.fetchall()

    if not edge_only:
        try:  # Try to execute the node query, return None if it fails
            node_r = c.execute(node_query)
        except:
            print("Query error: SQL cannot execute node query")
            return None
        node_header = get_header(c)
        node_records = node_r.fetchall()

    edge_df = validate_edge_query(edge_header, edge_records, c)
    if edge_df is None:
        print("Query error: Edge query is invalid")
        return None

    if not edge_only:
        node_df = validate_node_query(node_header, node_records, c)
        if node_df is None:
            print("Query error: Node query is invalid")
            return None

    conn.close()


    if not edge_only:
        # Check that nodes in node_df equal the unique nodes in edge_df
        nodes_in_edge_df = set(edge_df['source']) | set(edge_df['target'])
        nodes_in_node_df = set(node_df['node'])

        if not nodes_in_edge_df == nodes_in_node_df:
            print("Query error: The unique nodes in the edges query must match"
                  "the unique nodes in the nodes query")
            return None

        G = build_graph(edge_df, node_df, graph_type=graph)

    if edge_only:
        return edge_df
    else:
        return G, edge_df, node_df


#  ________________________________________
# |                                        |
# |            9: Simple Graph             |
# |________________________________________|


def simple_graph(db_file, node_query, edge_query,graph_type=nx.Graph ):
    '''
    Simple version for graphs that does not require any verification.
    '''
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    n_cursor = c.execute(node_query)
    header = get_header(c)
    nodes = pd.DataFrame(n_cursor.fetchall(), columns=header)

    e_cursor = c.execute(edge_query)
    header = get_header(c)
    edges = pd.DataFrame(e_cursor.fetchall(), columns=header)

    G = build_graph(edges, nodes, graph_type)
    return G, edges, nodes
