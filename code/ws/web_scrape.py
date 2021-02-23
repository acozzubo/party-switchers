# -*- coding: utf-8 -*-
'''
  ________________________________________
 |                                        |
 | Webscrapping of JNE Website            |
 | Team: Party Switchers                  |
 | Authors: Raymond Eid - Andrei Batra    |
 | Date: February, 2020                   |
 |________________________________________|


 =============================================================================
 Webscrapping of resume data from JNE website:
     https://plataformaelectoral.jne.gob.pe/ListaDeCandidatos/Index
 =============================================================================
'''


#  ________________________________________
# |                                        |
# |              1: Libraries              |
# |________________________________________|


##pip install selenimum
import os, sys

##selenium
from selenium.webdriver import Chrome
import time
import pandas as pd
import numpy as np
#  ________________________________________
# |                                        |
# |            2: Local Modules            |
# |________________________________________|

#Global variables
import glb
import party_switching as ps

#  ________________________________________
# |                                        |
# |               3: Settings              |
# |________________________________________|

#Current path

os.chdir(ps.wd)
sys.path.append(os.chdir(ps.wd))




#  ________________________________________
# |                                        |
# |          4: Table Structures           |
# |________________________________________|


def table_structure(file_name):
    '''
    Creates a dictionary with tables to be filled with the scrapping process.
    The field structures are located in the 'file_name' excel file.
    Output:
        tables: Dictionary with pandas dataframes according to the structure
        in the "file_name"
        fields: The file_name as a pandas dataframe
    '''

    fields = pd.read_excel(file_name)

    table_list = list(fields.raw_table.unique())

    tables = {}
    for t in table_list:
        iterator = fields[fields.raw_table == t].iterate.iloc[0]
        tables[t] = pd.DataFrame(columns =
                  ['id_hdv'] +
                  ([iterator] if isinstance(iterator, str) else []) +
                  list(fields[fields.raw_table == t].campo))
    return tables, fields


#  ________________________________________
# |                                        |
# |             5: Web Crawler             |
# |________________________________________|


def hdv_crawler(tables, fields, break_early=False, ini_wait=2, pag_wait=5, \
                vm_wait=3, std_wait=2):
    '''
    Web crawler of the JNE webpage: 

    https://plataformaelectoral.jne.gob.pe/ListaDeCandidatos/Index

    It sets up the webpage and go through all the curriculum vitae pages
    (HDV by it translation to spanish).
    To get to HDV it locates the 'ver mas' button (see more) and go 
    through all the valid links in the table.
    
    When there are no more 'see more' buttons, it goes to the next pages
    
    When a link is opened, it switches to the new window and performs the
    scrapping. 
    '''
    # Load Page
    driver = Chrome(glb.driver_path)
    driver.get(glb.url)
    driver.maximize_window()

    #Activate searcher

    buscar = driver.find_element_by_xpath(glb.m_xpaths['buscar'])
    buscar.click()
    time.sleep(ini_wait)
    buscar = driver.find_element_by_xpath(glb.m_xpaths['buscar'])
    buscar.click()

    #Expand to max count of political parties
    time.sleep(pag_wait)
    view150 = driver.find_element_by_xpath(glb.m_xpaths['view_150'])
    view150.click()

    #Crawling HDV
    pg_index = 0
    vm_index = 0
    break_count = 0
    while True:
        try:
            if break_early and break_count == 10:
                break
            vm_index += 1
            time.sleep(std_wait)
            ver_mas = driver \
                .find_element_by_xpath(glb.m_xpaths['ver_mas'] \
                                       .format(vm_index))
        except:
            try:
                pg_index += 1
                vm_index = 0
                next_page = driver \
                          .find_element_by_xpath(glb.m_xpaths['page'] \
                                                 .format(pg_index))
            except:
                break
            else:
                next_page.click()
        else:
            ver_mas.click()
            row_index = 0
            time.sleep(vm_wait)
            while True:
                try:
                    row_index += 1
                    driver.find_element_by_xpath(glb.m_xpaths['row'] \
                                                 .format(vm_index, row_index))
                    if break_early and break_count == 10:
                        break
                except:
                    break
                else:
                    try:
                        hdv = driver \
                            .find_element_by_xpath(glb.m_xpaths['hdv'] \
                                                   .format(vm_index, row_index))
                    except:
                        pass
                    else:
                        break_count += 1
                        hdv.click()
                        time.sleep(std_wait)
                        id_hdv = "-".join([str(pg_index),
                                           str(vm_index),
                                           str(row_index)])
                        driver.switch_to.window(driver.window_handles[1])
                        print(id_hdv)
                        scrapping(driver, tables, fields, id_hdv)
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
    driver.close()
    return None
#  ________________________________________
# |                                        |
# |              6: Web Scrape             |
# |________________________________________|


def scrapping(driver, tables, fields, id_hdv):
    '''
    Retrieves the HDV information following the instructions in the fields file
    It stores the information in the tables dictionary, following the 
    instructions in the field file.
    '''
    for field in fields.itertuples(index=False):
        _, _, name, scheme, att, t, it_rec, ini, inc, _ = field
        i = 0
        while True:
            i += 1
            i_dir = ini + i*(0 if np.isnan(inc) else int(inc))
            xpath = scheme.format(None if np.isnan(i_dir) else int(i_dir))
            try:
                if att == 'text':
                    value = getattr(driver.find_element_by_xpath(xpath), att)
                else:
                    value = getattr(driver.find_element_by_xpath(xpath), att)()
            except:
                break
            else:

                if not np.isnan(ini):
                    if tables[t].loc[(tables[t]['id_hdv'] == id_hdv) &
                                              (tables[t][it_rec] == int(i)),
                                              name].empty:
                        tables[t] = tables[t].append({'id_hdv': id_hdv,
                                                      it_rec: int(i),
                                                      name: value},
                                                     ignore_index = True)
                    else:
                        tables[t].loc[(tables[t]['id_hdv'] == id_hdv) &
                                      (tables[t][it_rec] == int(i))
                                      , name] = value
                else:
                    if tables[t].loc[(tables[t]['id_hdv'] == id_hdv),
                                              name].empty:
                        tables[t] = tables[t].append({'id_hdv': id_hdv,
                                                      name: value},
                                                     ignore_index = True)
                    else:
                        tables[t].loc[tables[t].id_hdv == id_hdv, name] = value
                    break

    return None

#  ________________________________________
# |                                        |
# |              7: CSV Export             |
# |________________________________________|


def csv_export(tables, data_dir):
    '''
    Saves all the information in the tables dictionary in individual csv files.
    '''
    schema = data_dir + '{}' +'.csv'
    for tab_name, table in tables.items():
        table.to_csv(schema.format(tab_name))
    return None

#  ________________________________________
# |                                        |
# |               8: Wrapper               |
# |________________________________________|


def web_scrape(file_name, data_dir, break_early=False):
    '''
    Performs the webscrapping.
    '''
    tables, fields = table_structure(file_name)
    hdv_crawler(tables, fields, break_early)
    csv_export(tables, data_dir)
    return tables

