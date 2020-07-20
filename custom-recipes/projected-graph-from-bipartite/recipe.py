# -*- coding: utf-8 -*-
from dataiku.customrecipe import get_recipe_config
from utils import get_input_dataset, get_output_dataset, get_bipartite_recipe_params
from constants import Constants
import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite
import logging
logger = logging.getLogger(__name__)


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
logger.info("Bipartite Graph - Dataset loaded...")

# Delete nulls
df = df[(df[params[Constants.GRAPH_OF]].notnull()) & (df[params[Constants.LINKED_BY]].notnull())]
logger.info("Bipartite Graph - Removed null values...")

# Dedup
dd = df.groupby(columns).size().reset_index().rename(columns={0: 'w'})
logger.info("Bipartite Graph - Created deduplicated dataset...")

# Creating the bipartite graph
G = nx.Graph()
G.add_nodes_from(dd[params[Constants.GRAPH_OF]].unique(),  bipartite=0)
G.add_nodes_from(dd[params[Constants.LINKED_BY]].unique(), bipartite=1)
G.add_edges_from(zip(dd[params[Constants.GRAPH_OF]], dd[params[Constants.LINKED_BY]]))
logger.info("Bipartite Graph - Created bipartite graph...")

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

logger.info("Bipartite Graph - Created projected graph...")

# Recipe outputs
logger.info("Bipartite Graph - Writing output dataset...")
# graph = output_dataset
output_dataset.write_with_schema(df)
