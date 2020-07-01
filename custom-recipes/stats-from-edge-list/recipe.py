# -*- coding: utf-8 -*-
from dataiku.customrecipe import get_recipe_config
from utils import get_input_dataset, get_output_dataset, get_analytics_recipe_params
from constants import Constants
import logging
import pandas as pd
import networkx as nx
logger = logging.getLogger(__name__)


input_dataset = get_input_dataset('Input Dataset')
output_dataset = get_output_dataset('Output Dataset')

recipe_config = get_recipe_config()
params = get_analytics_recipe_params(recipe_config)

df = input_dataset.get_dataframe()

logger.info("Graph Features - Creating NetworkX graph")
if params[Constants.DIRECTED]:
    graph = nx.from_pandas_edgelist(df, source=params[Constants.SOURCE], target=params[Constants.TARGET], create_using=nx.DiGraph)
else:
    graph = nx.from_pandas_edgelist(df, source=params[Constants.SOURCE], target=params[Constants.TARGET], create_using=nx.Graph)

# Always run: nodes degree
logger.info("Graph Features - Computing degree")
deg = pd.Series(nx.degree(graph), name='degree')
stats = pd.DataFrame(list(deg), columns=[Constants.NODE_NAME, 'degree'])

if params[Constants.EIGEN_CENTRALITY]:
    logger.info("Graph Features - Computing eigenvector centrality")
    eig = pd.Series(nx.eigenvector_centrality_numpy(graph), name='eigenvector_centrality').reset_index()
    eig.columns = [Constants.NODE_NAME, 'eigenvector_centrality']

if params[Constants.CLUSTERING]:
    logger.info("Graph Features - Computing clustering coefficient")
    clu = pd.Series(nx.clustering(graph), name='clustering_coefficient').reset_index()
    clu.columns = [Constants.NODE_NAME, 'clustering_coefficient']

if params[Constants.TRIANGLES] and not params[Constants.DIRECTED]:
    logger.info("Graph Features - Computing number of triangles")
    tri = pd.Series(nx.triangles(graph), name='triangles').reset_index()
    tri.columns = [Constants.NODE_NAME, 'triangles']

if params[Constants.CLOSENESS]:
    logger.info("Graph Features - Computing closeness centrality")
    clo = pd.Series(nx.closeness_centrality(graph), name='closeness_centrality').reset_index()
    clo.columns = [Constants.NODE_NAME, 'closeness_centrality']

if params[Constants.PAGERANK]:
    logger.info("Graph Features - Computing pagerank")
    pag = pd.Series(nx.pagerank(graph), name='pagerank').reset_index()
    pag.columns = [Constants.NODE_NAME, 'pagerank']

if params[Constants.SQ_CLUSTERING]:
    logger.info("Graph Features - Computing square clustering")
    squ = pd.Series(nx.square_clustering(graph), name='square_clustering_coefficient').reset_index()
    squ.columns = [Constants.NODE_NAME, 'square_clustering_coefficient']

# Always run: connected components
if not params[Constants.DIRECTED]:
    _cco = {}
    for i, c in enumerate(nx.connected_components(graph)):
        for e in c:
            _cco[e] = i
    cco = pd.Series(_cco, name='connected_component_id').reset_index()
    cco.columns = [Constants.NODE_NAME, 'connected_component_id']
    cco['connected_component_size'] = cco.groupby('connected_component_id')['connected_component_id'].transform('count')

# Putting all together
if params['output_type'] == 'output_edges':
    # keep all rows in output
    df_output = df
    node_columns = [Constants.SOURCE, Constants.TARGET]  # merge graph features with both source and target node columns
else:
    # output one row per node
    df_output = stats[Constants.NODE_NAME].to_frame()
    df_output.columns = [params[Constants.SOURCE]]
    node_columns = [Constants.SOURCE]

for node_col in node_columns:
    df_output = df_output.merge(stats, left_on=params[node_col], right_on=Constants.NODE_NAME, how='left', suffixes=('_source', '_target')).drop([Constants.NODE_NAME], axis=1)

    if params[Constants.EIGEN_CENTRALITY]:
        df_output = df_output.merge(eig, left_on=params[node_col], right_on=Constants.NODE_NAME, how='left', suffixes=('_source', '_target')).drop([Constants.NODE_NAME], axis=1)
    if params[Constants.CLUSTERING]:
        df_output = df_output.merge(clu, left_on=params[node_col], right_on=Constants.NODE_NAME, how='left', suffixes=('_source', '_target')).drop([Constants.NODE_NAME], axis=1)
    if params[Constants.TRIANGLES] and not params[Constants.DIRECTED]:
        df_output = df_output.merge(tri, left_on=params[node_col], right_on=Constants.NODE_NAME, how='left', suffixes=('_source', '_target')).drop([Constants.NODE_NAME], axis=1)
    if params[Constants.CLOSENESS]:
        df_output = df_output.merge(clo, left_on=params[node_col], right_on=Constants.NODE_NAME, how='left', suffixes=('_source', '_target')).drop([Constants.NODE_NAME], axis=1)
    if params[Constants.PAGERANK]:
        df_output = df_output.merge(pag, left_on=params[node_col], right_on=Constants.NODE_NAME, how='left', suffixes=('_source', '_target')).drop([Constants.NODE_NAME], axis=1)
    if params[Constants.SQ_CLUSTERING]:
        df_output = df_output.merge(squ, left_on=params[node_col], right_on=Constants.NODE_NAME, how='left', suffixes=('_source', '_target')).drop([Constants.NODE_NAME], axis=1)
    if not params[Constants.DIRECTED]:
        df_output = df_output.merge(cco, left_on=params[node_col], right_on=Constants.NODE_NAME, how='left', suffixes=('_source', '_target')).drop([Constants.NODE_NAME], axis=1)

output_dataset.write_with_schema(df_output)
