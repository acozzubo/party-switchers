# -*- coding: utf-8 -*-
'''
  __________________________________________
 |                                          |
 | Database Configuration of Scrapped data  |
 | Team: Party Switchers                    |
 | Authors: Andrei Batra                    |
 | Responsable: Andrei Batra                |
 | Date: February, 2020                     |
 |__________________________________________|

 =============================================================================
Configuring a database file with scrapped data
 =============================================================================
'''

#  ________________________________________
# |                                        |
# |              1: Libraries              |
# |________________________________________|

#Basic Stuff
import os, sys
import io

#SQL
import sqlite3

#Pandas
import pandas as pd
import xlrd
#Numpy
import numpy as np

#  ________________________________________
# |                                        |
# |           2: Local Modules             |
# |________________________________________|
import party_switching as ps


#  ________________________________________
# |                                        |
# |               3: Settings              |
# |________________________________________|

#Current path
#wd = '/home/student/capp30122-win-20-acozzubo-andreibartra-mtrichardson-reid7/Project'
os.chdir(ps.wd)
sys.path.append(os.chdir(ps.wd))

#Globals
data_fields = r'data/input/hdv_fields.xlsx'
csv_path = r'data/csv/'
db_file = 'data/db/db.db'
#  ________________________________________
# |                                        |
# |           4: Data Download             |
# |________________________________________|


def data_loading(data_fields, csv_path):
    '''
    Creates a dictionary of tables with information stored in the CSV files
    Input:
        data_fields: Excel file with raw meta data
        csv_path: Directory Path where all the CSV files are
    Output:
        tables: Dictionary with dataframes
        fields: Dataframe with raw metada data
        table_list: A list with all the table names
    '''

    fields = pd.read_excel(data_fields)
    table_list = list(fields.raw_table.unique())

    tables = {}
    for t in table_list:
        tables[t] = pd.read_csv(csv_path + t + '.csv').drop('Unnamed: 0', \
                                                            axis=1)
    return tables, fields, table_list

#  ________________________________________
# |                                        |
# |           5: Data Cleaning             |
# |________________________________________|


def raw_data_cleaning(tables, fields, table_list):
    '''
    Performs the data cleaning process of all the raw data
    Output:
        tables: Dictionary of dataframes with all the fields cleaned
    '''
    #Treatments for all tables
    year_fields = list(fields['campo'][fields.campo. \
                                 str.contains(r'_year|_end|_start$')])
    monetary_fields = ['inc_pub', 'inc_priv', 'rent_pub', 'rent_priv', \
                        'other_inc_pub', 'other_inc_priv', 'oth_val', \
                        'prop_value', 'veh_val']

    pos_con = fields.campo.str.contains(r'^prev_pos')
    pos_fields = list(fields['campo'][pos_con])
    pos_list = [p.split(': ')[1] for p in list(fields['Description'][pos_con])]
    position = dict(zip(pos_fields, pos_list))

    for t in table_list:
        # NaN to empty string
        tables[t] = tables[t].fillna(' ')
        #Cleaning empty rows
        t_fields = list(fields[fields.raw_table == t].campo)
        tables[t] = tables[t][tables[t][t_fields].isin([' ']).sum(1) \
                                     < len(t_fields)]
        for f in t_fields:
            # Converting year fields
            if f in year_fields:
                tables[t][f] = pd.to_numeric(tables[t][f]. \
                                  fillna(' '). \
                                  replace(' ','0'). \
                                  replace('HASTA LA ACTUALIDAD', '2020')). \
                                  astype(int).replace(0,np.NaN)
            #Converting monetary fields
            if f in monetary_fields:
                tables[t][f] = pd.to_numeric(tables[t][f].replace(0, np.NaN), \
                                  errors='coerce')
            # Yes/No columns
            if set(tables[t][f].unique()) == {' ', 'NO', 'SÍ'}:
                tables[t][f] = tables[t][f].astype('category').cat.codes - 1
                tables[t][f] = tables[t][f].replace(-1, np.NaN)

            # Previous position fields
            if f in pos_fields:
                tables[t][f] = tables[t][f]. \
                               replace(' ', np.NaN). \
                               astype('category'). \
                               cat.codes.replace(-1, 0)

    # Candidate
    t = 'candidate'
    tables[t]['dni'] = tables[t]['dni'].astype(str). \
                       str.split('.').str[0]
    tables[t]['dni'] = tables[t]['dni'].apply(lambda x: '0'*(8-len(x)) + x)
    tables[t]['sexo'] = tables[t]['sexo']. \
                        apply(lambda x: 'M' if x == 'MASCULINO' else 'F')

    # Pevious positions
    t = 'position_record'
    tables[t]['prev_position'] = tables[t][pos_fields]. \
                                 dot(tables[t][pos_fields].columns). \
                                 replace(position)
    tables[t] = tables[t].drop(columns = pos_fields)
    tables[t] = tables[t][tables[t]['prev_position'] != '']
    return tables

#  ________________________________________
# |                                        |
# |            6: Raw Edges table          |
# |________________________________________|



def append_edges(edges, table, edge_type, rename_dic):
    '''
    Generates a dataframe with information requiered to track the political
    movements of the candidates:
        Current Political Party
        Previous elected positions
        Previous Party Memberships
        Previous Party Resignations
    Output: Dataframe with the political movements consolidated
    '''
    fields = ['id_hdv'] + [k for k in rename_dic]
    temp =  table[fields].copy().rename(columns = rename_dic)
    temp['type'] = edge_type
    edges = edges.append(temp, ignore_index=True, sort=True)
    return edges


def raw_edges(tables):
    edges= tables['candidate'][['id_hdv','org_pol']].copy()
    edges['begin'] = np.NaN
    edges['end'] = 2020
    edges['type'] = 'current'

    edges = append_edges(edges, tables['party_record'], 'party', \
                         {'party_memb': 'org_pol', \
                          'party_start': 'begin', \
                          'party_end': 'end'})

    edges = append_edges(edges, tables['position_record'], 'position', \
                         {'prev_org_pol': 'org_pol', \
                          'prev_start': 'begin', \
                          'prev_end': 'end'})

    edges = append_edges(edges, tables['resign_record']. \
                         assign(begin=tables['resign_record']['resign_year']), \
                         'resignation', \
                         {'resign': 'org_pol', \
                          'begin': 'begin', \
                          'resign_year': 'end'})

    edges['edge_rec'] = edges.groupby('id_hdv').cumcount()+1

    return edges

#  ________________________________________
# |                                        |
# |          7: Node Standarization        |
# |________________________________________|


def party_standarization(tables):
    '''
    Clean the party names to make them standard across the varios registers
    Input:
        tables: The tables dictionary
    Output:
        edges dataframe with standard party names.
    '''
    edges = tables['edges']
    replace = {'ALIANZA ELECTORAL ': '', \
               'MOVIMIENTO REGIONAL O DEPARTAMENTAL MOVIMIENTO INDEPENDIENTE '
               'REGIONAL': 'MR/D', \
               'MOVIMIENTO REGIONAL O DEPARTAMENTAL MOVIMIENTO INDEPENDIENTE': \
               'MR/D', \
               'MOVIMIENTO REGIONAL O DEPARTAMENTAL MOVIMIENTO REGIONAL': \
               'MR/D',\
               'MOVIMIENTO REGIONAL O DEPARTAMENTAL MOVIMIENTO': 'MR/D', \
               'MOVIMIENTO REGIONAL O DEPARTAMENTAL': 'MR/D', \
               'MOVIMIENTO REGIONAL': 'MR/D', \
               'ORGANIZACION POLITICA LOCAL DISTRITAL': 'OPLD', \
               'ORGANIZACION POLITICA LOCAL PROVINCIAL': 'OPLP', \
               'PARTIDO POLITICO NACIONAL ': '', \
               'PARTIDO POLITICO ': '', \
               'POLPULAR': 'POPULAR', \
               'IZQUIERA': 'IZQUIERDA'  }

    rep_dic = {'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', \
               '-': ' ', ',': ' ', '.': ' ', '"': ' ', '+':' '}

    excepts = [('AMPLIO', 'FRENTE AMPLIO'), \
               ('ANDE MAR', 'MR/D ANDEMAR'), \
               ('CAMBIO 90', 'CAMBIO 90'), \
               ('FUERZA POPULAR', 'FUERZA POPULAR'), \
               ('GRAN CAMBIO', 'PERUANOS POR EL KAMBIO'), \
               ('KAMBIO', 'PERUANOS POR EL KAMBIO'), \
               ('INTEGRACION AMAZONICA', 'INTEGRACION AMAZONICO'), \
               ('INTEGRACION LORETANA', 'INTEGRACION LORETANA MIL'), \
               ('SOCIALISTA', 'PARTIDO SOCIALISTA DEL PERU'), \
               ('SOLIDARIDAD NACIONAL', 'SOLIDARIDAD NACIONAL'), \
               ('APRA', 'APRISTA PERUANO'), \
               ('APRISTA', 'APRISTA PERUANO'), \
               ('PPC', 'POPULAR CRISTIANO' ), \
               (' FIA ', 'FREPAP'), \
               ('PARA PROGRESO', 'ALIANZA POR EL PROGRESO'), \
               ('PARA EL PROGRESO', 'ALIANZA POR EL PROGRESO'), \
               ('NACIONALISTA', 'NACIONALISTA'), \
               ('FREDEMO', 'FREDEMO'), \
               ('SOMOS PERU', 'SOMOS PERU'), \
               ('DE AFIRMACION', 'MOVIMIENTO AFIRMACION SOCIAL'), \
               ('AYLLU', 'MR\\D AYLLU'), \
               ('ETNOCACERISTA', 'ETNOCACERISTA'), \
               ('FUERZA SOCIAL', 'MR\\D FUERZA SOCIAL'), \
               ('PODEMOS POR EL', 'PODEMOS PERU'), \
               ('POPULAR CRISTIANO', 'PARTIDO POPULAR CRISTIANO')]

    reple = lambda x: ''.join([rep_dic.get(c, c) for c in x])
    clean = lambda x: ' '.join([w for w in x.split()])

    #Names
    edges['p_name'] = edges['org_pol'].apply(reple)
    edges['p_name'] = edges['p_name'].apply(clean)

    for old, new in replace.items():
        edges['p_name'] = edges['p_name'].str.replace(old, new)

    #Exceptions
    for exc in excepts:
        edges.loc[edges['p_name'].str.contains(exc[0]), 'p_name'] = exc[1]


    return edges


#  ________________________________________
# |                                        |
# |           8: Network Creation          |
# |________________________________________|

def node_table(tables):
    '''
    Creates a table with all the nodes (parties) and some basic attributes and
    a unique id for each party.
    Input:
        Tables: the tables dictionary
    Output:
        nodes: A Dataframe with party information.

    '''
    edges = tables['edges']
    nodes = edges.loc[:,['p_name','type']]
    nodes['current'] = nodes['type'].apply(lambda x: 1 if x == 'current' else 0)
    nodes = nodes.groupby('p_name').agg({'current': 'max'})
    nodes = nodes.reset_index()
    nodes['reg_movement'] =  0
    nodes.loc[nodes['p_name'].str.contains('MR/D'), 'reg_movement'] = 1
    nodes.loc[nodes['p_name'].str.contains('OPLD'), 'reg_movement'] = 1
    nodes.loc[nodes['p_name'].str.contains('OPLP'), 'reg_movement'] = 1

    nodes = nodes.reset_index()
    nodes = nodes.rename(columns={'index': 'node'})

    return nodes

def network_table(tables):
    '''
    Creates a dataframe with network vertices. It is unique by:
        source: source party node,
        target: target party node,
        year: year of the movement,
        id_hdv: candidate unique id
    Input:
        tables: The tables dictionary
    Output:
        ntwk: The network dataframe
    '''
    ntwk = tables['edges']

    #Updating edges
    ntwk = ntwk.merge(tables['nodes']. \
                        loc[:,['p_name','node']], \
                        on = 'p_name')

    ntwk = ntwk.sort_values(['id_hdv','begin','end'])

    #Update edges
    tables['edges'] = ntwk

    #Identifying when indivuals stay in the samee party
    ntwk['same_party'] = ntwk.groupby('id_hdv')['p_name'].shift(-1) == \
                         ntwk['p_name']

    #Treating time so it is ordered and without gaps
    ntwk['year'] = ntwk.groupby('id_hdv')['end'].shift(1)
    ntwk['year'] = ntwk.loc[:,['begin','year']]. \
                        apply(lambda x: x[0] if np.isnan(x[1]) else x[1], \
                               axis =1)
    #Replacing the begin year if the candidate didn't move
    ntwk.loc[ntwk.groupby('id_hdv')['same_party'].shift(1, fill_value=False), \
             'year'] = ntwk.groupby('id_hdv')['year'].shift(1)
    ntwk.groupby('id_hdv')['year'].shift(1, fill_value=False)

    # NA correspond to the latest year
    ntwk.loc[:, 'year'] = ntwk.loc[:, 'year'].fillna(2020)

    # Filtering invalid movements
    ntwk = ntwk.loc[~ntwk['same_party']].copy()


    ntwk['source'] = ntwk.groupby('id_hdv')['node'].shift(1)
    ntwk['source'] = ntwk['source'].fillna(ntwk['node'])

    #Remove first row per individual

    ntwk['_N'] = ntwk.groupby('id_hdv')['year'].transform('count')
    ntwk['_n'] = ntwk.groupby('id_hdv').cumcount()+1

    #Identifying non movers
    ntwk['edge'] = ntwk['source'] != ntwk['node']

    # Keeping relevant columns
    ntwk = ntwk.loc[(ntwk['_n'] > 1) | (ntwk['_N'] == 1), \
                    ['id_hdv', 'source', 'node', 'year', 'edge']].copy()

    ntwk = ntwk.rename(columns = {'node': 'target'})

    return ntwk
#  ________________________________________
# |                                        |
# |               9: Metadata              |
# |________________________________________|

def meta_table(tables, fields, uni_fields=10):
    '''
    Creates a dataframe with all the meta data up to this point.
    input:
        tables: the tables dictionary
        fields: the dataframe with raw meta information
        uni_fields: Number of maximun unique values to register in the
        unique values field.
    Output:
        meta_raw: The dataframe with raw meta information
        meta_db: A dataframe with all metada data of all the fields up to
        this point.
    '''
    meta_raw = fields

    desc = {'begin' : 'Begin year in the party',
            'end': 'End year  the party',
            'type':  'Type of registry',
            'p_name': 'Political Party Name (processed)',
            'node':  'Political Party Code' ,
            'same_party':  'Dummy if the next register is the same party',
            'year':  'Year of the movement',
            'current':  'It is a political party participating on current elections'  ,
            'reg_movement': 'It is a local party',
            'source': 'Source Node',
            'target': 'Target Node' ,
            'edge':  'It is a movement to other party'
            }

    meta_db = pd.DataFrame(columns = ['table', 'column', 'non_null', \
                                      'type', 'unique_vals', 'n_unique', \
                                      'is_key', 'section', 'xpath', \
                                      'col_type', 'description'])

    for k, v in tables.items():
        temp = pd.DataFrame(v.describe(include = 'all').loc['count']. \
                              rename('non_null'))
        temp['type'] = v.dtypes.astype(str)
        temp['type'] = temp['type'].apply(lambda x: 'TEXT' if x =='object' \
                                                   else 'NUMERIC') 
        temp = temp.reset_index().rename(columns={'index': 'column'})
        temp['table'] = k
        temp['n_unique'] = temp['column'].apply(lambda x: len(v[x].unique()))
        u_vals = lambda x: ', '.join([str(s) for s in v[x[0]].unique()]) \
                                              if x[1] < uni_fields else ''
        temp['unique_vals'] = temp.loc[:, ['column', 'n_unique']]. \
                              apply(u_vals, axis = 1)

        col_type = lambda x: 'raw' if x in fields['campo'].values else 'processed'
        temp['col_type'] = temp['column'].apply(col_type) 

        temp['is_key'] = temp['column'].str[-4:].isin(['_rec', '_hdv']) 

        def field(col, field):
            return str(fields.loc[fields.campo==col,field].values).strip("['']") 

        temp['section'] = temp.apply(lambda x: field(x['column'],'seccion'), \
                                     axis=1)
        temp['xpath'] = temp.apply(lambda x: field(x['column'],'xpath'), \
                                    axis=1)
        temp['description'] = temp.apply(lambda x: \
                                         field(x['column'],'Description'), \
                                          axis=1)

        meta_db = meta_db.append(temp, ignore_index=True, sort=True)


    meta_db.loc[meta_db['column'] == 'id_hdv', 'description'] = \
    'Primary Key. Encodes location in web: page-ver_mas-register'

    meta_db.loc[meta_db['column'].str. \
                                  contains('_rec'), 'description'] = \
    'Record ID in the table for the candidate'

    for col, des in desc.items():
        meta_db.loc[meta_db['column'] == col, 'description'] = des

    meta_db.loc[(meta_db['table'] == 'edges') & \
                (meta_db['column']. \
                 isin(['id_hdv', 'edge_rec'])), \
               'is_key'] = True

    meta_db.loc[(meta_db['table'] == 'nodes') & \
                (meta_db['column'] == 'node'), 'is_key'] = True

    meta_db.loc[(meta_db['table'] == 'network') & \
                (meta_db['column']. \
                 isin(['id_hdv', 'source', 'target', 'year'])), \
               'is_key'] = True


    return meta_raw, meta_db

#  ________________________________________
# |                                        |
# |         10: DB Configuration           |
# |________________________________________|



def sql_config(tables, db_file):
    '''
    Configures a SQL database following the structure of the tables
    '''
    try:
        os.remove(db_file)
    except:
        pass
    else:
        conn = sqlite3.connect(db_file)

        c = conn.cursor()

        meta = tables['meta_db']

        for t in list(meta['table'].unique()):

            temp = meta.loc[meta['table'] == t, ['column', 'type', 'is_key']]
            temp['query'] = '[' + temp['column'] + ']' + ' ' \
                           + temp['type'] + ','

            fields = temp['query'].to_string(index=False, header=False)

            key = ', '.join(list(temp.loc[temp['is_key'], 'column']))

            query = \
            """
            CREATE TABLE {}
            (
            {}
            PRIMARY KEY ({})
            )
            """.format(t, fields, key)
            c.execute(query)


        conn.commit()
        conn.close()
#  ________________________________________
# |                                        |
# |            11: Data Upload             |
# |________________________________________|


def sql_upload(tables, db_file):
    '''
    Uploads the dataframes into the SQL database
    '''
    conn = sqlite3.connect(db_file)

    for t, df in tables.items():
        df.to_sql(t, conn, if_exists = 'append', index = False)
    conn.commit()
    conn.close()

#  ________________________________________
# |                                        |
# |               12: Wrapper              |
# |________________________________________|


def db_config(data_fields, csv_path, db_file):
    '''
    All the data cleaning, metada data and SQL database configuration
    '''
    tables, fields, table_list = data_loading(data_fields, csv_path)
    tables = raw_data_cleaning(tables, fields, table_list)
    tables['edges'] = raw_edges(tables)
    tables['edges'] = party_standarization(tables)

    tables['nodes'] = node_table(tables)
    tables['network'] = network_table(tables)
    tables['meta_raw'], tables['meta_db'] = meta_table(tables, fields)

    sql_config(tables, db_file)
    sql_upload(tables, db_file)