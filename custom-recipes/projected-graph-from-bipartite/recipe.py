# -*- coding: utf-8 -*-
from dataiku.customrecipe import get_recipe_config
from utils import get_input_dataset, get_output_dataset, get_bipartite_recipe_params
from constants import Constants
import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite
import logging
import time


# Read recipe config
input_dataset = get_input_dataset('Input Dataset')
output_dataset = get_output_dataset('Output Dataset')

recipe_config = get_recipe_config()
params = get_bipartite_recipe_params(recipe_config)

# CREATE_GRAPH_OF = get_recipe_config()['create_graph_of']
# params[Constants.LINKED_BY] = get_recipe_config()['params[Constants.LINKED_BY]']

# List of necessary columns
columns = []
columns.append(params[Constants.GRAPH_OF])
columns.append(params[Constants.LINKED_BY])

# Recipe input
df = input_dataset.get_dataframe(columns=columns)
logging.info("Projected graph - Dataset loaded")

# Delete nulls
df = df[(df[params[Constants.GRAPH_OF]].notnull()) & (df[params[Constants.LINKED_BY]].notnull())]
logging.info("Projected graph - Null values removed")

# Dedup
dd = df.groupby(columns).size().reset_index().rename(columns={0: 'w'})
logging.info("Projected graph - Deduplicated dataset created")

# Creating the Projected graph
G = nx.Graph()
G.add_nodes_from(dd[params[Constants.GRAPH_OF]].unique(),  bipartite=0)
G.add_nodes_from(dd[params[Constants.LINKED_BY]].unique(), bipartite=1)
G.add_edges_from(zip(dd[params[Constants.GRAPH_OF]], dd[params[Constants.LINKED_BY]]))
logging.info("Projected graph - NetworkX graph created")

start = time.time()
logging.info("Projected graph - Creating projected graph...")
# Projecting the main projected graph
if params[Constants.WEIGHTED]:
    graph = bipartite.weighted_projected_graph(G, dd[params[Constants.GRAPH_OF]].unique())
    edges_list = [(src, tgt, w['weight']) for src, tgt, w in graph.edges(data=True)]
    df = pd.DataFrame(list(edges_list))
    df.columns = [params[Constants.GRAPH_OF] + '_1', params[Constants.GRAPH_OF] + '_2', 'weight']
else:
    graph = bipartite.projected_graph(G, dd[params[Constants.GRAPH_OF]].unique(), multigraph=False)
    # Outputting the corresponding data frame
    df = pd.DataFrame(list(graph.edges()))
    df.columns = [params[Constants.GRAPH_OF] + '_1', params[Constants.GRAPH_OF] + '_2']

logging.info("Projected graph - Projected graph computed in {:.4f} seconds".format(time.time()-start))

output_dataset.write_with_schema(df)
