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

# List of necessary columns
columns = []
columns.append(params[Constants.GRAPH_OF])
columns.append(params[Constants.LINKED_BY])

# Recipe input
input_df = input_dataset.get_dataframe(columns=columns)
logging.info("Projected graph - Dataset loaded")

# Delete nulls
input_df = input_df[(input_df[params[Constants.GRAPH_OF]].notnull()) & (input_df[params[Constants.LINKED_BY]].notnull())]
logging.info("Projected graph - Null values removed")

# Dedup
deduplicated_df = input_df.groupby(columns).size().reset_index().rename(columns={0: 'w'})
logging.info("Projected graph - Deduplicated dataset created")

# Creating the Projected graph
bipartite_graph = nx.Graph()
bipartite_graph.add_nodes_from(deduplicated_df[params[Constants.GRAPH_OF]].unique(),  bipartite=0)
bipartite_graph.add_nodes_from(deduplicated_df[params[Constants.LINKED_BY]].unique(), bipartite=1)
bipartite_graph.add_edges_from(zip(deduplicated_df[params[Constants.GRAPH_OF]], deduplicated_df[params[Constants.LINKED_BY]]))
logging.info("Projected graph - NetworkX graph created")

start = time.time()
logging.info("Projected graph - Creating projected graph...")
# Projecting the main projected graph
if params[Constants.WEIGHTED]:
    projected_graph = bipartite.weighted_projected_graph(bipartite_graph, deduplicated_df[params[Constants.GRAPH_OF]].unique())
    edges_list = [(src, tgt, w['weight']) for src, tgt, w in projected_graph.edges(data=True)]
    output_df = pd.DataFrame(list(edges_list))
    output_df.columns = [params[Constants.GRAPH_OF] + '_1', params[Constants.GRAPH_OF] + '_2', 'weight']
else:
    projected_graph = bipartite.projected_graph(bipartite_graph, deduplicated_df[params[Constants.GRAPH_OF]].unique(), multigraph=False)
    # Outputting the corresponding data frame
    output_df = pd.DataFrame(list(projected_graph.edges()))
    output_df.columns = [params[Constants.GRAPH_OF] + '_1', params[Constants.GRAPH_OF] + '_2']

logging.info("Projected graph - Projected graph computed in {:.4f} seconds".format(time.time()-start))

output_dataset.write_with_schema(output_df)
