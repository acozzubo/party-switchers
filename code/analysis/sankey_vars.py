# -*- coding: utf-8 -*-
'''
  __________________________________________
 |                                          |
 | Updating Database with foreign data      |
 | Team: Party Switchers                    |
 | Authors: Angelo Cozzubo                  |
 | Responsable: Angelo Cozzubo              |
 | Date: February, 2020                     |
 |__________________________________________|

 =============================================================================
Creates categorical variables using candidates information and foreing data
to create the sakey graphs for the single party analysis.
 =============================================================================
'''

#  ________________________________________
# |                                        |
# |              1: Libraries              |
# |________________________________________|

import numpy as np
import pandas as pd
import sqlite3
import os
import sys


#  ________________________________________
# |                                        |
# |             2: The Function            |
# |________________________________________|


def gen_sankey_vars(db_loc):
    '''
    CAUTION: THIS FUNCTION GENERATES A NEW TABLE IN DB AND REPLACES PREVIOUS
    DB WITH THE SAME NAME
    Generates attribute table for sankey graphs and update SQL db
    Input: database location
    Output: None
    '''

    conn = sqlite3.connect(db_loc)
    cursor = conn.cursor()

    candidate = pd.read_sql('SELECT * FROM candidate;', conn)
    civil_rec = pd.read_sql('SELECT * FROM civil_record;', conn)
    criminal_rec = pd.read_sql('SELECT * FROM criminal_record;', conn)
    other_assets = pd.read_sql('SELECT * FROM other_assets;', conn)
    properties = pd.read_sql('SELECT * FROM properties;', conn)
    vehicles = pd.read_sql('SELECT * FROM vehicles;', conn)
    univ_record = pd.read_sql('SELECT * FROM univ_record;', conn)
    work_experience = pd.read_sql('SELECT * FROM work_experience;', conn)

    regionales_q = pd.read_sql('SELECT * FROM var_dpto_gob;', conn)
    distrital_q = pd.read_sql('SELECT * FROM var_distritales;', conn)
    distrital_q = distrital_q.drop(['nombredd', 'nombrepv', 'nombredi'], axis=1)

    # Every reg and district var to quartiles
    for col in list(regionales_q.columns)[:-1]:
        regionales_q[col] = pd.qcut(regionales_q[col], 4, labels=list(range(4)))

    for col in list(distrital_q.columns)[1:25]:
        distrital_q[col] = pd.qcut(distrital_q[col], 4, labels=list(range(4)))
    for col in ["altitud", "D_pob_crim"]:
        distrital_q[col] = pd.qcut(distrital_q[col], 4, labels=list(range(4)))

    # Count if candidate has crim, civil records. As dummies
    civil_rec = civil_rec.groupby(['id_hdv'], as_index=True).count()[
        ['civi_rec']]
    civil_rec.loc[civil_rec['civi_rec'] > 0, 'civi_rec'] = 1

    criminal_rec = criminal_rec.groupby('id_hdv').count()[['crim_rec']]
    criminal_rec.loc[criminal_rec['crim_rec'] > 0, 'crim_rec'] = 1

    # Number of assets in quartiles. Other assets as dummies
    other_assets = other_assets.groupby('id_hdv').count()[['othe_rec']]
    other_assets.loc[other_assets['othe_rec'] > 0, 'othe_rec'] = 1

    properties = properties.groupby('id_hdv').count()[['prop_rec']]
    properties['prop_rec'] = properties['prop_rec'].rank(method='first')
    properties['prop_rec'] = pd.qcut(properties['prop_rec'].values, 4).codes

    vehicles = vehicles.groupby('id_hdv').count()[['vehi_rec']]
    vehicles['vehi_rec'] = vehicles['vehi_rec'].rank(method='first')
    vehicles['vehi_rec'] = pd.qcut(vehicles['vehi_rec'].values, 4).codes

    # Has university degree / work experience as dummies
    univ_record = univ_record.groupby('id_hdv').count()[['univ_rec']]
    univ_record.loc[univ_record['univ_rec'] > 0, 'univ_rec'] = 1

    work_experience = work_experience.groupby('id_hdv').count()[['work_rec']]
    work_experience.loc[work_experience['work_rec'] > 0, 'work_rec'] = 1

    # Income

    sankey_vars = candidate.copy()
    sankey_vars['total_ing'] = sankey_vars['inc_pub'] + sankey_vars[
        'inc_priv'] + \
                               sankey_vars['rent_pub'] + sankey_vars[
                                   'rent_priv'] + \
                               sankey_vars['other_inc_pub'] + sankey_vars[
                                   'other_inc_priv']
    sankey_vars['total_ing'] = pd.qcut(sankey_vars['total_ing'], 4, \
                                       labels=list(range(4)))

    #### Clean unnecesary vars
    sankey_vars = sankey_vars[sankey_vars.columns.drop( \
        list(sankey_vars.filter(regex='rent')))]  # erase rent...
    sankey_vars = sankey_vars[sankey_vars.columns.drop( \
        list(sankey_vars.filter(regex='inc')))]  # erase inc...
    sankey_vars = sankey_vars[sankey_vars.columns.drop( \
        list(sankey_vars.filter(regex='other')))]  # erase other...
    sankey_vars = sankey_vars[sankey_vars.columns.drop( \
        list(sankey_vars.filter(regex='grad')))]  # erase grad...
    sankey_vars = sankey_vars[sankey_vars.columns.drop( \
        list(sankey_vars.filter(regex='no_')))]  # erase no...
    sankey_vars = sankey_vars[sankey_vars.columns.drop( \
        list(sankey_vars.filter(regex='technical')))]  # erase tech...
    sankey_vars = sankey_vars[sankey_vars.columns.drop('comment')]

    #### Merging
    for t in [criminal_rec, civil_rec, other_assets, properties, univ_record,
              vehicles]:
        sankey_vars = pd.merge(sankey_vars, t, on='id_hdv', how='left')

    sankey_vars = pd.merge(sankey_vars, regionales_q, how='left', \
                           left_on=['dept_dom'], right_on=['dept'])

    sankey_vars = pd.merge(sankey_vars, distrital_q, how='left', \
                           left_on=['dept_dom', 'prov_dom', 'dist_dom'], \
                           right_on=['dept', 'prov', 'dist'])

    #### Fill zeros of those required
    to_fill_zero = ['crim_rec', 'civi_rec', 'othe_rec', 'prop_rec', 'univ_rec', \
                    'vehi_rec', 'total_ing', 'has_primary_complete', \
                    'has_secondary', 'has_secondary_complete', 'has_univ']
    sankey_vars[to_fill_zero] = sankey_vars[to_fill_zero].fillna(0)

    #### Update db and close connection
    sankey_vars.to_sql('sankey_vars', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()
