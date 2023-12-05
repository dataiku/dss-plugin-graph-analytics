# -*- coding: utf-8 -*-
from dataiku.customrecipe import get_recipe_config
from graph_analytics_utils import get_input_dataset, get_output_dataset
from graph_analytics_constants import Constants
import pandas as pd
import networkx as nx
from networkx.algorithms import union
import logging
import time

def create_ego_graph(graph, node, radius=1, predecessors=False):
  try:
    # Create a directed ego-graph from node to get it's successors
    node_ego_graph = nx.ego_graph(graph, node, radius)

    # Reverse graph to get level 1 predecessors
    if predecessors:
      tmp_graph = graph.reverse()
      predecessors_ego_graph = nx.ego_graph(tmp_graph, node, radius=1)
      predecessors_ego_graph = predecessors_ego_graph.reverse()
      node_ego_graph.update(predecessors_ego_graph)

    return node_ego_graph
  
  # Return an empty directed graph if node is not found in graph
  except:
    logging.warn("Ego graph - Node " + node + " not found in graph")
    return nx.DiGraph()


# Read recipe config
input_dataset = get_input_dataset('Input Dataset')
output_dataset = get_output_dataset('Output Dataset')

recipe_config = get_recipe_config()

# List of necessary columns
columns = []
columns.append(recipe_config['source_nodes'])
columns.append(recipe_config['target_nodes'])
for col in recipe_config['edges_label']:
  columns.append(col)

# Recipe input
input_df = input_dataset.get_dataframe(columns=columns)
logging.info("Ego graph - Dataset loaded")

# Delete nulls
input_df = input_df[(input_df[recipe_config['source_nodes']].notnull()) & (input_df[recipe_config['target_nodes']].notnull())]
logging.info("Ego graph - Null values removed")

# Dedup
deduplicated_df = input_df.groupby(columns).size().reset_index().rename(columns={0: 'w'})
logging.info("Ego graph - Deduplicated dataset created")

# Creating the directed graph
graph = nx.from_pandas_edgelist(deduplicated_df, recipe_config['source_nodes'], recipe_config['target_nodes'], recipe_config['edges_label'], nx.DiGraph)
logging.info("Base NetworkX graph created")

node_ego_graph = nx.DiGraph()
for node in recipe_config["nodes"]:
    node_ego_graph.update(create_ego_graph(graph, node, recipe_config["ego_graph_radius"], True))

# Write output dataframe
output_df = pd.DataFrame(list(node_ego_graph.edges(data=True)))
output_df.columns = [recipe_config['source_nodes'], recipe_config['target_nodes'], "Edges labels"] 

logging.info("Ego graph - Ego graph computed")

output_dataset.write_with_schema(output_df)


