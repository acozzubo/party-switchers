# -*- coding: utf-8 -*-
'''
  ________________________________________
 |                                        |
 | Various Queries                        |
 | Team: Party Switchers                  |
 | Authors: Andrei Batra                  |
 | Date: February, 2020                   |
 |________________________________________|


 =============================================================================
 It just stores query strings needed for analysis and graph generation
 =============================================================================
'''

all_network = \
"""
SELECT
    *
FROM
    network
"""



all_nodes = \
"""
SELECT
    *
FROM
    nodes
"""

add_clusters = \
"""
ALTER TABLE nodes ADD COLUMN clusters INTEGER
"""

add_cluster_labels = \
"""
ALTER TABLE nodes ADD COLUMN cluster_labels TEXT(30)
"""

add_neighboor_dg = \
"""
ALTER TABLE nodes ADD COLUMN neighbor_dg  NUMERIC
"""

update_nodes = \
"""
UPDATE nodes
SET clusters = (SELECT )
"""


com_network = \
"""
SELECT
     source_com as source
    ,target_com as target
    ,SUM(edge) as weight
FROM
    (
    SELECT
         a.*
        ,b.clusters as source_com
        ,c.clusters as target_com
    FROM
        network  a
        LEFT JOIN
        nodes  b
            ON b.node = a.source
        LEFT JOIN
        nodes c
            ON c.node = a.target
    ) nw  
GROUP BY nw.source_com, nw.target_com

"""

com_nodes = \
"""
SELECT
     clusters as node
    ,cluster_labs
FROM
    nodes
GROUP BY
    clusters, cluster_labs
"""

com_nodes_coords = \
"""
SELECT
     clusters as node
    ,cluster_labs
    ,clu_x
    ,clu_y
FROM
    nodes
GROUP BY
    clusters, cluster_labs, clu_x, clu_y
"""


candidates = \
"""
SELECT
    a.id_hdv,
    a.nombres,
    a.ape_pat,
    a.ape_mat,
    a.elec_dist,
    b.node,
    b.p_name
FROM
    candidate a
    LEFT JOIN
    (
    SELECT
         org_pol
        ,p_name
        ,node
    FROM
        edges
    GROUP BY
        org_pol) b
        ON a.org_pol = b.org_pol
"""
