# -*- coding: utf-8 -*-
'''
  __________________________________________________________
 |                                                         |
 | "Ideologists or Opportunists?": Party Switching in Peru |
 | Authors: -Andrei Bartra (andreibartra)                  |
 |          -Angelo Cozzubo (acozzubo)                     |
 |          -Marc Richardson (mtrichardson)                |
 |          -Reymond Eid (reid7)                           |
 | Date: February 2020                                     |
 |_________________________________________________________|


 =============================================================================
 Highlights:
    -Webscrapping of resume data from JNE website:
         https://plataformaelectoral.jne.gob.pe/ListaDeCandidatos/Index
    -SQL database configuration
    -Network builder function
    -Network Clusterization
    -Edges and nodes attributes generation
    -Network Visualization

Main Function:
    Authors: Marc Richardson
    Responsible: Marc Richardson
    Date: March 2020
 =============================================================================
'''
#  ________________________________________
# |                                        |
# |              1: Libraries              |
# |________________________________________|


import os, sys
import sqlite3
import pandas as pd

#  ________________________________________
# |                                        |
# |              2: Settings               |
# |________________________________________|

wd = os.getcwd()
os.chdir(wd)
sys.path.append(os.chdir(wd))

sys.path.insert(0, './code')
sys.path.insert(1, './code/ws')
sys.path.insert(2, './code/sql')
sys.path.insert(3, './code/analysis')
sys.path.insert(4, './code/graph')
sys.path.insert(5, './code/vis')

#  ________________________________________
# |                                        |
# |            3: Local Modules            |
# |________________________________________|


import web_scrape as ws
import db_config as db
import foreign_data as fd
import network_metrics as nm
import network_structure as ns
import build_sankey as bs
import gen_clusters as gen
import sankey_vars as sv
import nodes_coordinates as nc
import total_graph as tg

#  ________________________________________
# |                                        |
# |               4: Globals               |
# |________________________________________|

MAIN_MENU = '''
########## Party-Switching Analysis ##########
Welcome to the application. Please select an
option below to get started.

(1) Web-Scraping Demo
(2) Single-Party Switching Analysis
(3) Full-Network Analysis
(4) Candidate-Level Analysis
(5) Quit Program
'''

SANKEY_MENU = '''
########## Single-Party Analysis ##########
Please select a party to analyze.
'''

FULL_NETWORK_MENU = '''
########## Full Network Analysis ##########
Please select an option from below.

(1) Display Network Metrics
(2) Display Full Network
(3) Display Clusters Network
(4) Exit Back to Main Menu
'''

NETWORK_METRICS_MENU = '''
########## Network Metrics ##########
Please select the centrality measure by which to order the nodes.

(1) In Degree
(2) Out Degree
(3) Betweeness Centrality
(4) Eigenvector Centrality
(5) Exit Back to Previous Menu
'''

CANDIDATE_DISTRICT_MENU = '''
########## Candidate Path Visualization ##########
Please select an electoral district

{}
'''

PARTY_DISTRICT_MENU = '''
########## Candidate Path Visualization ##########
Please select a Party

{}
'''

CANDIDATE_MENU = '''
########## Candidate Path Visualization ##########
Please select a candidate

{}
'''

CENTRALITY_MEASURES = {1: "in_degree", 2: "out_degree", 3: "betweeness",
                       4: "eigenvector"}

SANKEY_PARTY_OPTIONS = ["APRISTA PERUANO", "POPULAR CRISTIANO",
                        "NACIONALISTA", "ACCION POPULAR",
                        "PERU POSIBLE", "SOMOS PERU",
                        "ALIANZA POR EL PROGRESO", "SOLIDARIDAD NACIONAL",
                        "UNION POR EL PERU", "TODOS POR EL PERU"]

SANKEY_VARIABLES_OPTIONS = {1: 'University Degree', 
                            2: 'Candidate Income (by Quartile)',
                            3: 'District Gini Index',
                            4: 'District Poverty Level (by Quartile)',
                            5: 'Share of Indigenous Population (by Quartile)',
                            6: 'District Share of Pop w/ no Schooling (by Quartile)', 
                            7: 'Criminal Record',
                            8: 'No Attribute'}

SANKEY_VARS = {1: 'univ_rec', 2: 'total_ing',3 : 'D_gini', 4: 'D_pobreza', 
               5: 'lengua_originaria', 6: 'sin_nivel_educ', 7: 'crim_rec', 
               8: 'None'}


#  ________________________________________
# |                                        |
# |          5: Helper Functions           |
# |________________________________________|

def retrieve_task():
    '''
    Retrieves the selected input option in the main menu.
    '''

    print(MAIN_MENU)
    while True:
        option = int(input("Option: "))
        if option >= 1 and option <= 5:
            break
        else:
            print("Invalid Option: Please select an option the menu above.")

    return option


def fetch_single_parties():
    '''
    Builds the menu of parties for the sankey graph.
    Output:
    dictionary of party codes as key and party name as value.
    '''

    parties = bs.gen_party_indexer(db.db_file)

    return {k: v for k, v in parties.items() if v in SANKEY_PARTY_OPTIONS}


#  ________________________________________
# |                                        |
# |            6: Web Scrape Demo          |
# |________________________________________|

def web_scrape_wrapper():
    '''
    Wrapper function for the 'web-scraping demo'
    '''

    print("Scraping the JNE website for candidate data...")
    print()
    ws.web_scrape('data/input/hdv_fields.xlsx', 'output/demo_csv',
                  break_early=True)
    print('CSV files from demo available at output/')
    print()


#  ________________________________________
# |                                        |
# |               7: Sankey Menu           |
# |________________________________________|

def sankey_options():
    '''
    Manages the menu for the single party analysis.
    Output: selected party and selected variable entered by the user.
    '''

    print(SANKEY_MENU)
    print()
    parties = fetch_single_parties()
    for key, value in parties.items():
        print("({}) {}".format(key, value))
    print()
    while True:
        party_option = int(input("Party: "))
        if party_option not in parties.keys():
            print("Invalid option. Please select a party from the menu.")
            print()
            continue
        else:
            break
    print("Please select a filtering variable.")
    print()
    for key, value in SANKEY_VARIABLES_OPTIONS.items():
        print("({}) {}".format(key, value))
    print()
    while True:
        var_option = int(input("Variable: "))
        if var_option not in SANKEY_VARIABLES_OPTIONS.keys():
            print("Invalid option. Please select a variable from the menu.")
            print()
            continue
        else:
            break

    return party_option, var_option


def sankey_options_wrapper():
    '''
    Wrapper function for 'single-party analysis' menu
    '''

    p, v = sankey_options()
    v = SANKEY_VARS[v]
    if v == "None":
        v = None

    sys.stdout = open(os.devnull, "w")
    bs.sankey_wrapper(p, v)
    sys.stdout = sys.__stdout__


#  ________________________________________
# |                                        |
# |          8: Full Network Menu          |
# |________________________________________|

def network_metrics_options():
    '''
    Manages the menu for the network metrics analysis.
    output: Metric option selected by the user
    '''

    print(NETWORK_METRICS_MENU)
    while True:
        option = int(input("Option: "))
        if option < 1 or option > 5:
            print("Invalid option. Please select an option from the menu.")
            print()
            continue
        if option == 5:
            return
        else:
            rv = CENTRALITY_MEASURES[option]
            break

    return rv


def network_options_wrapper():
    '''
    Wrapper function for 'full network' analysis menu
    '''

    print(FULL_NETWORK_MENU)
    while True:
        opt = int(input("Option: "))
        if opt < 1 or opt > 4:
            print("Invalid option. Please select an option from the"
                  " menu.")
            print()
        if opt == 1:
            subopt = network_metrics_options()
            if subopt is None:
                print()
                print(FULL_NETWORK_MENU)
            else:
                nm.display_network_metrics(subopt)
                print()
                print(FULL_NETWORK_MENU)
        if opt == 2:
            tg.total_graph()
        if opt == 3:
            tg.cluster_graph()
        if opt == 4:
            break


#  ________________________________________
# |                                        |
# |            9: Candidate Menu           |
# |________________________________________|

def candidate_menu():
    '''
    Manages the menu for the single candidate analysis
    Output: Inputs for the single candidate graph
    '''

    conn = sqlite3.connect(db.db_file)
    c = conn.cursor()
    n_cursor = c.execute("SELECT * FROM candidate_menu")
    header = ns.get_header(c)

    df = pd.DataFrame(n_cursor.fetchall(), columns=header)
    dist_menu = df.loc[:,['dist_id','elec_dist']].groupby(['dist_id']). \
                   first()

    print(CANDIDATE_DISTRICT_MENU.format(dist_menu))
    while True:
        dist = int(input("Option: "))
        party_menu = df.loc[df.dist_id == dist, ['party_id','p_name']]. \
                        groupby('party_id').first()
        if party_menu.empty:
            print("Invalid option. Select a district from the menu.")
            print()
            continue
        else:
            break
    print(PARTY_DISTRICT_MENU.format(party_menu))
    while True:
        party = int(input("Option: "))
        cand_menu = df.loc[(df.dist_id == dist) & (df.party_id == party), \
                       ['cand_id','name']].set_index('cand_id')
        if cand_menu.empty:
            print("Invalid option. Select a party from the menu.")
            print()
            continue
        else:
            break
    print(CANDIDATE_MENU.format(cand_menu))
    while True:
        c_id = int(input("Option: "))
        if df.loc[(df.dist_id == dist) & (df.party_id == party) \
              & (df.cand_id == c_id)].empty:
            print("Invalid option. Select a candidate from the menu.")
            print()
            continue
        else:
            break

    return dist, party, c_id


def candidate_menu_wrapper():
    '''
    Wrapper function for 'candidate analysis' menu
    '''

    dist, party, c_id = candidate_menu()
    tg.candidate_graph(dist, party, c_id)


#  ________________________________________
# |                                        |
# |            10: Main Function           |
# |________________________________________|

def main():
    '''
    Console based interface
    '''

    handler = {1: web_scrape_wrapper, 2: sankey_options_wrapper,
               3: network_options_wrapper, 4: candidate_menu_wrapper}

    print("Warming up syrup...")
    print()
    print("Configuring SQL database...")
    print()
    db.db_config(db.data_fields, db.csv_path, db.db_file)
    print("SQL database configured")
    print()

    print("Updating database with external data...")
    print()
    fd.foreign_data(fd.foreign_tables, fd.foreign_path, fd.db_file)
    print("Database updated with external data")
    print()

    sv.gen_sankey_vars(db.db_file)

    print("Updating database with clusters...")
    print()
    gen.gen_clusters()
    print("Finished updating database with clusters")
    print()

    nc.nodes_coordinates()
    print("Pouring syrup")

    while True:
        option = retrieve_task()
        if option == 5:
            break
        handler[option]()


if __name__ == "__main__":
    # Access point for the application
    main()
