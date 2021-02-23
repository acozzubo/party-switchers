# -*- coding: utf-8 -*-
'''
  __________________________________________
 |                                          |
 | Community Analysis on Cadidate Party     |
 | Swtching Network                         |
 | Team: Party Switchers                    |
 | Authors: Angelo Cozzubo - Raymond Eid    |
 | Responsable: Raymond Eid                 |
 | Date: February, 2020                     |
 |__________________________________________|

 =============================================================================
Creates Sankey Graphs for single party analysis
 =============================================================================
'''

#  ________________________________________
# |                                        |
# |              1: Libraries              |
# |________________________________________|

import pandas as pd
from plotly.offline import plot
import plotly.graph_objs as go
import sys
import os
import random
import sqlite3
import numpy as np

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
DB_FILE = db.db_file


#  ________________________________________
# |                                        |
# |               2: Globals               |
# |________________________________________|

WD = os.getcwd()
vis = '/code/vis'
GRAPH = '/code/graph'
VAR_LABELS = {'univ_rec': 'University Degree', \
'total_ing': "Candidate Income (by Quartile)", 'D_gini': "District Gini Index", \
'D_pobreza': "District Poverty Level (by Quartile)",
'lengua_originaria': "Share of Indigenous Population (by Quartile)",\
'sin_nivel_educ': "District Share Pop no Schooling (by Quartile)",
"crim_rec": 'Criminal Record', None: "No Attribute Selected"}

#  ________________________________________
# |                                        |
# |               3: Settings              |
# |________________________________________|

sys.path.append(WD + vis)
os.chdir(WD)
sys.path.append(os.chdir(WD))
sys.path.append( WD + GRAPH)

#  ________________________________________
# |                                        |
# |            4: Local Modules            |
# |________________________________________|

import network_structure as ns

#  ________________________________________
# |                                        |
# |             5: Sankey Class            |
# |________________________________________|

class Sankey:
    '''
    Sankey will create the inputs for and plot the diagram given the data
    parameter centered around the party_of_interest, with party switchers
    characterized by the attribute.
    '''

    def __init__(self, data, attribute, party_of_interest):
        '''
        Constructs the Sankey object which will construct the necessary inputs
        and plots the visualization.

        Input:
            data: (Pandas Dataframe) contains the data upon which the diagram
                will be constructed
            attribute: (string) the attribute upon which the sankey will divide
                the node flows
            party_of_interest: (integer) the number of the party around which \
                the Sankey diagram will be centered
        '''
        self.data = data
        self.poi = party_of_interest
        self.attribute = attribute
        if attribute:
            self.attribute_range = sorted(self.data[attribute].unique())
        else:
            self.attribute_range = []
        if  self.attribute_range == [0, 1]:
            self.binary = True
        else:
            self.binary = False
        if self.binary:
            if self.attribute == 'crim_rec':
                self.attr_of_interest = 1
            else:
                self.attr_of_interest = 0
        self.labels = [self.poi]
        self.values, self.sources, self.targets = [], [], []
        self.node_colors = self.gen_color_palette(len(self.data))
        self.flow_colors = []
        self.title = "{} flows by {}".format(self.poi, VAR_LABELS[self.attribute])
        
        self.gen_inputs_from_data()

    def gen_color_palette(self, num_nodes):
        '''
        Creates a distinct color for each node in the Sankey Diagram in a random
        fashion, with the party of interest designated as green in all instances.
        Inputs:
            num_nodes: (integer) the number of parties present in the data
        Returns:
            color_palette: (list) a collection of colors
        '''

        color_palette = []
        color_palette.append("green") #poi node color will always be green
        flow_count = num_nodes + len(self.attribute_range) * 2

        for _ in range(flow_count):
            r = random.randint(0, 255)
            b = random.randint(0, 255)
            g = random.randint(0, 255)
            transparency = random.randint(2, 4) / 10
            rgba = 'rgba' + str((r, b, g, transparency))
            color_palette.append(rgba)

        return color_palette

    def gen_inputs_from_data(self, incoming=True):
        '''
        For each individual party node, groups flows by attribute for party
        switchers flowing into and out of the party of interest. Loops through
        the dataframe to update the source, target, labels, and values list
        attributes in place. Finally, creates the flow of politicians between 
        the attribute groups and the party of interest.
        Inputs:
            incoming: (boolean) specifies if politician switching into or out from
                      the party of interest
        Returns:
            None
        '''
        if incoming:
            row, col = 'source', 'target'

        else:
            row, col = 'target', 'source'
        drop_idx = self.data[self.data[row] == self.poi].index
        iterator = self.data.drop(index=drop_idx, columns=[col])
        
        for _, party, attr, count in iterator.itertuples():
            #Creates party node flows to and from grouping nodes 
            if incoming:
                source, target = self.target_source_labels(incoming, party, attr)
            else:
                target, source = self.target_source_labels(incoming, party, attr)
            self.sources.append(self.labels.index(source))
            self.targets.append(self.labels.index(target))
            self.values.append(count)
            if not self.attribute:
                self.flow_colors = None
            #Creates flows for grouping nodes to and from party of interest node
            else:
                self.values.append(count)
                group_label = self.grouping_label(attr, incoming)
                group_index = self.labels.index(group_label)
                self.node_colors[group_index] = "gray"
                if incoming:
                    self.sources.append(group_index)
                    self.targets.append(0)
                else:
                    self.sources.append(0)
                    self.targets.append(group_index)
                if self.binary:
                    if attr != self.attr_of_interest:
                        self.flow_colors.append('rgba(235, 235, 235, .5)') #gray
                    else:
                        self.flow_colors.append('rgba(214, 30, 30, .8)') #red
                else:
                    self.flow_colors = None
        if incoming:
            self.gen_inputs_from_data(incoming=False)

    def target_source_labels(self, incoming, party, attr):
        '''
        Constructs labels for source and target nodes
        Inputs:
            incoming: (boolean) specifies if politician switching into or out from
                      the party of interest
            party: (string) the name of the party from or into which the politician
                    is switching
            attr: (integer) the value of attribute of interest
        Returns:
            party: (string) party name which may be slight modified
            target_source: (string) party name which will be used either as a
                            source or target node
        '''
        if not incoming: #allows identical party nodes to be separated by in and out flows
            party += " "
        self.labels.append(party)
        if not self.attribute:
            target_source = self.poi
        else:
            target_source = self.grouping_label(attr, incoming)
            if target_source not in self.labels:
                self.labels.append(target_source)
            if self.binary:
                if attr != self.attr_of_interest:
                    self.flow_colors.append('rgba(235, 235, 235, .5)') #gray
                else:
                    self.flow_colors.append('rgba(214, 30, 30, .8)') #red
                    
        return party, target_source
                    
    def grouping_label(self, attr, incoming):
        '''
        Creates the label for the grouping nodes
        Inputs:
            attr: (integer) the value of the attribute of interest
            incoming: (boolean) specifies if politician switching into or out from
                      the party of interest 
        '''
        if incoming:
            direction = "In:"
        else:
            direction = "Out:"
        if self.binary:
            if attr == 0:
                status = "No " + VAR_LABELS[self.attribute]
            else:
                status = VAR_LABELS[self.attribute]
            group_label = "{} {}".format(direction, status) 
        else:
            group_label = "{} {} {}".format(direction, VAR_LABELS[self.attribute], attr)
            
        return group_label

    def plot_diagram(self):
        '''
        Given complete attribute lists for labels, colors, sources, targets,
        values, and flow colors, plots the Sankey diagram in an offline window.

        Returns:
            None
        '''

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=100,
                thickness=50,
                line=dict(color="black", width=1),
                label=self.labels,
                color=self.node_colors),

            link=dict(
                source=self.sources,
                target=self.targets,
                value=self.values,
                color=self.flow_colors))])

        fig.update_layout(title_text=self.title, font_size=15,
                          font=dict(color="black"),
                          plot_bgcolor='black',
                          paper_bgcolor='rgb(128, 128, 128, 0.3)')

        fig.show()


#  ________________________________________
# |                                        |
# |           6: Helper Functions          |
# |________________________________________|

def gen_party_indexer(DB_FILE):
    '''
    Creates a dictionary that maps all parties' indices to thier respective 
    names
    Inputs:
        DB_FILE: the path to the database to query
    Outputs:
        indexer: the dictionary mapping party indices to party names
    '''
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql('SELECT * FROM nodes;', conn)
    indexer = dict(zip(df.node, df.p_name))
    del df
    conn.close()

    return indexer

def build_query(poi, attribute):
    '''
    Constructs a SQL query that will include id_hdv, source party, target party,
    year of switch, and the specified attribute.

    Input:
        poi: (integer) the index of the party upon which the Sankey will focus
        attribute: (string) the attribute on which party switching will be
            characterized

    Output:
        query: (string) a SQL query
    '''
    if not attribute:
        attribute_string = ' '
    else:
        attribute_string = ", sv.{} ".format(attribute)

    query = ('SELECT c.id_hdv, n.source, n.target, n.year' + attribute_string +\
             'FROM network as n JOIN candidate as c on n.id_hdv = c.id_hdv '
             'JOIN sankey_vars as sv on sv.id_hdv = c.id_hdv '
             'WHERE n.source = {} OR n.target = {}'.format(poi, poi))

    return query

def clean_df(df, poi, indexer):
    '''
    Takes a raw data frame and outputs it in the correct format for the Sankey
    inputs.

    Input:
        df: (Pandas data frame) raw data frame
        poi: (integer) the index of the party on which the Sankey is focused

    Output:
        cleaned_df: (Pandas data frame) the dataframe in a suitable format for
            the Sankey diagram
    '''
    if len(df.columns) == 4:
        df['dummy'] = ''
    attr = df.columns[4] #empty string if no attr, else gets the attr
    df = df.groupby(['source', 'target', attr]).size().reset_index()
    df.rename(columns={df.columns[3]: "Count"}, inplace=True)
    df = df[(df.source != poi) | (df.target != poi)]
    # gets rid of non-party switchers from poi

    if attr in ['crim_rec', 'univ_rec']:
        df[attr] = df[attr].astype(float).astype(int)
    elif attr not in ['D_gini', 'dummy']:
        df[attr] = df[attr].astype(float).astype(int) + 1
    elif attr == 'D_gini':
        df[attr] = round(df[attr], 1)
    df['source'] = df['source'].map(indexer)
    df['target'] = df['target'].map(indexer)
    df['source'] = np.where(df['source'].str.startswith("MR/D"), \
      "REGIONAL PARTY", df["source"]) 
    df['target'] = np.where(df['target'].str.startswith("MR/D"), \
      "REGIONAL PARTY", df["target"])
    #Groups all regional parties into one group

    return df

#  ________________________________________
# |                                        |
# |           7: Wrapper Function          |
# |________________________________________|

def sankey_wrapper(party_of_interest, attribute):
    '''
    Given inputs from the shell, creates a query for the Sankey Attribute table,
    converts the output into a Pandas Dataframe, creates a Sankey object with
    the Dataframe, which in turns builds and plots the Sankey diagram.

    Inputs:
        party_of_interest: (integer) the number of the party around which the
            Sankey diagram will be centered
        attribute: (string) the attribute upon which the sankey will divide
            the node flows
    Output:
        None, function will plot diagram in an offline internet window
    '''

    query = build_query(party_of_interest, attribute)
    df = ns.network_structure(DB_FILE, query, '', None, edge_only=True)
    indexer = gen_party_indexer(DB_FILE)
    sankey_df = clean_df(df, party_of_interest, indexer)

    poi = indexer[party_of_interest]

    sankey = Sankey(sankey_df, attribute, poi)
    sankey.plot_diagram()

