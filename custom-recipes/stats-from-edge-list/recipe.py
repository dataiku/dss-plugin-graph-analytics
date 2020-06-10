# -*- coding: utf-8 -*-
from dataiku.customrecipe import get_recipe_config
from utils import get_input_dataset, get_output_dataset, get_recipe_params
import logging
import pandas as pd
import networkx as nx
logger = logging.getLogger(__name__)


input_dataset = get_input_dataset('Input Dataset')
output_dataset = get_output_dataset('Output Dataset')

recipe_config = get_recipe_config()
params = get_recipe_params(recipe_config)

df = input_dataset.get_dataframe()

logger.info("Graph Features - Creating NetworkX graph")
if params['directed_graph']:
    graph = nx.from_pandas_edgelist(df, source=params['source'], target=params['target'], create_using=nx.DiGraph)
else:
    graph = nx.from_pandas_edgelist(df, source=params['source'], target=params['target'], create_using=nx.Graph)

# Always run: nodes degree
logger.info("Graph Features - Computing degree")
deg = pd.Series(nx.degree(graph), name='degree')
stats = pd.DataFrame(list(deg), columns=[params['source'], 'degree'])

if params['eigenvector_centrality']:
    logger.info("Graph Features - Computing eigenvector centrality")
    eig = pd.Series(nx.eigenvector_centrality_numpy(graph), name='eigenvector_centrality').reset_index()
    eig.columns = ['node_name', 'eigenvector_centrality']

if params['clustering']:
    logger.info("Graph Features - Computing clustering coefficient")
    clu = pd.Series(nx.clustering(graph), name='clustering_coefficient').reset_index()
    clu.columns = ['node_name', 'clustering_coefficient']

if params['triangles'] and not params['directed_graph']:
    logger.info("Graph Features - Computing number of triangles")
    tri = pd.Series(nx.triangles(graph), name='triangles').reset_index()
    tri.columns = ['node_name', 'triangles']

if params['closeness']:
    logger.info("Graph Features - Computing closeness centrality")
    clo = pd.Series(nx.closeness_centrality(graph), name='closeness_centrality').reset_index()
    clo.columns = ['node_name', 'closeness_centrality']

if params['pagerank']:
    logger.info("Graph Features - Computing pagerank")
    pag = pd.Series(nx.pagerank(graph), name='pagerank').reset_index()
    pag.columns = ['node_name', 'pagerank']

if params['sq_clustering']:
    logger.info("Graph Features - Computing square clustering")
    squ = pd.Series(nx.square_clustering(graph), name='square_clustering_coefficient').reset_index()
    squ.columns = ['node_name', 'square_clustering_coefficient']

# Always run: connected components
if not params['directed_graph']:
    _cco = {}
    for i, c in enumerate(nx.connected_components(graph)):
        for e in c:
            _cco[e] = i
    cco = pd.Series(_cco, name='connected_component_id').reset_index()
    cco.columns = ['node_name', 'connected_component_id']
    cco['connected_component_size'] = cco.groupby('connected_component_id')['connected_component_id'].transform('count')

# Putting all together
if params['output_type'] == 'output_edges':
    df_output = df.merge(stats, on=params['source'], how='left')
else:
    df_output = stats

if params['eigenvector_centrality']:
    df_output = df_output.merge(eig, left_on=params['source'], right_on='node_name', how='left').drop(['node_name'], axis=1)
if params['clustering']:
    df_output = df_output.merge(clu, left_on=params['source'], right_on='node_name', how='left').drop(['node_name'], axis=1)
if params['triangles'] and not params['directed_graph']:
    df_output = df_output.merge(tri, left_on=params['source'], right_on='node_name', how='left').drop(['node_name'], axis=1)
if params['closeness']:
    df_output = df_output.merge(clo, left_on=params['source'], right_on='node_name', how='left').drop(['node_name'], axis=1)
if params['pagerank']:
    df_output = df_output.merge(pag, left_on=params['source'], right_on='node_name', how='left').drop(['node_name'], axis=1)
if params['sq_clustering']:
    df_output = df_output.merge(squ, left_on=params['source'], right_on='node_name', how='left').drop(['node_name'], axis=1)
if not params['directed_graph']:
    df_output = df_output.merge(cco, left_on=params['source'], right_on='node_name', how='left').drop(['node_name'], axis=1)

output_dataset.write_with_schema(df_output)
