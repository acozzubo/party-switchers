# -*- coding: utf-8 -*-
'''
  __________________________________________
 |                                          |
 | Updating Database with foreign data      |
 | Team: Party Switchers                    |
 | Authors: Angelo Cozzubo - Andrei Bartra  |
 | Responsable: Angelo Cozzubo              |
 | Date: February, 2020                     |
 |__________________________________________|

 =============================================================================
Uploads external data into the database
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
# |            2: Local Modules            |
# |________________________________________|

import party_switching as ps 

#  ________________________________________
# |                                        |
# |               3: Settings              |
# |________________________________________|

#Current path
os.chdir(ps.wd)
sys.path.append(os.chdir(ps.wd))

#Globals
db_file = 'data//db//db.db'
foreign_path = r'data//foreign//'
foreign_tables = r'data//input//foreign_tables.xlsx'
foreign_meta = r'data//foreign//data_dictionary.xlsx'

#  ________________________________________
# |                                        |
# |           4: Data Download             |
# |________________________________________|


def foreign_to_pandas(foreign_tables, foreign_path):
    '''
    Imports the raw foreign data into dataframes.
    Input:
        foreign_tables: Excel file with the list of foreign tables
        foreign_path: Directory where the csv files are
    Output:
        tables: dictionary with dataframes
        metadata: pandas dataframe with the foreign metadata.
    '''
    table_list = pd.read_excel(foreign_tables)

    metadata = pd.read_excel(foreign_meta)

    tables = {}
    for t in list(table_list['table'].unique()):
        tables[t] = pd.read_csv(foreign_path + t + '.csv')

    return tables, metadata


#  ________________________________________
# |                                        |
# |              5: Metadata               |
# |________________________________________|

def prepare_meta(metadata, tables):
    '''
    Fill some metadata fields of the new columns in the dataframe.
    '''
    md = metadata
    md['col_type'] = 'foreign'
    tab_list = list(md['table'].unique())

    for t in tab_list:
        md.loc[md['table'] == t,'non_null'] = tables[t]. \
                                              describe(include = 'all'). \
                                              loc['count']. \
                                              values
    return md


def update_meta(metadata, db_file):
    '''
    Updates the metadata table in the SQL database with the information
    of the new fields.
    '''
    conn = sqlite3.connect(db_file)
    template = pd.read_sql('SELECT * FROM meta_db LIMIT 1;', conn)
    template = template.drop(0).append(metadata, ignore_index=True, sort=True)
    template.to_sql('meta_db', conn, if_exists = 'append', index = False)
    conn.commit()
    conn.close()


#  ________________________________________
# |                                        |
# |              6: DB Update              |
# |________________________________________|

def update_db(tables, metadata, db_file):
    '''
    updates the database with all the new information.
    '''
    conn = sqlite3.connect(db_file)
    tab_list = list(metadata['table'].unique())
    for t in tab_list:
        tables[t].to_sql(t, conn, if_exists = 'append', index = False)
    conn.commit()
    conn.close()

#  ________________________________________
# |                                        |
# |               7: Wrapper               |
# |________________________________________|


def foreign_data(foreign_tables, foreign_path, db_file):
    '''
    Inserts the foreign data into the SQL database.
    '''
    ft, md = foreign_to_pandas(foreign_tables, foreign_path)
    md = prepare_meta(md, ft)
    update_meta(md, db_file)
    update_db(ft, md, db_file)
