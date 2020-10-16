from dataiku.customrecipe import get_recipe_config
from utils import get_input_dataset, get_output_dataset, get_analytics_recipe_params, AlgorithmError
from constants import Constants
from dku_graph_analytics.graph_analytics import GRAPH_ALGORITHMS
import logging
import time
import pandas as pd
import networkx as nx


input_dataset = get_input_dataset('Input Dataset')
output_dataset = get_output_dataset('Output Dataset')

recipe_config = get_recipe_config()
params = get_analytics_recipe_params(recipe_config)

input_df = input_dataset.get_dataframe()

start = time.time()
logging.info("Graph analytics - Creating NetworkX graph ...")
if params[Constants.DIRECTED]:
    graph = nx.from_pandas_edgelist(input_df, source=params[Constants.SOURCE], target=params[Constants.TARGET], create_using=nx.DiGraph)
else:
    graph = nx.from_pandas_edgelist(input_df, source=params[Constants.SOURCE], target=params[Constants.TARGET], create_using=nx.Graph)
logging.info("Graph analytics - NetworkX graph created in {:.4f} seconds".format(time.time()-start))

# Always run: nodes degree
start = time.time()
logging.info("Graph analytics - Computing degree ...")
deg = pd.Series(nx.degree(graph), name='degree')
deg_df = pd.DataFrame(list(deg), columns=[Constants.NODE_NAME, 'degree'])
logging.info("Graph analytics - degree computed in {:.4f} seconds".format(time.time()-start))

algo_series = {"degrees": deg_df}

# output all edges or only nodes
if params[Constants.OUTPUT_TYPE] == 'output_edges':
    # keep all rows in output
    output_df = input_df
    node_columns = [Constants.SOURCE, Constants.TARGET]  # merge graph features with both source and target node columns
else:
    # output one row per node
    output_df = deg_df[Constants.NODE_NAME].to_frame()
    output_df.columns = [params[Constants.SOURCE]]
    node_columns = [Constants.SOURCE]

# computing all selected graph features algorithms
for algo, algo_params in GRAPH_ALGORITHMS.items():
    label, method = algo_params['label'], algo_params['method']
    if params[algo]:
        if not params.get(algo_params.get('param_restriction', None), None):
            start = time.time()
            logging.info("Graph analytics - Computing {} ...".format(label))
            try:
                pd_series = pd.Series(method[0](graph, **method[1]), name=label).reset_index()
                pd_series.columns = [Constants.NODE_NAME, label]
                algo_series[label] = pd_series
                logging.info("Graph analytics - {} computed in {:.4f} seconds".format(label, time.time()-start))
            except Exception as e:
                raise AlgorithmError("Error while computing {}: {}".format(label, e))

if not params[Constants.DIRECTED]:
    start = time.time()
    logging.info("Graph analytics - Computing connected_components ...")
    connected_components_dict = {}
    for component_id, component in enumerate(nx.connected_components(graph)):
        for element in component:
            connected_components_dict[element] = component_id
    connected_components = pd.Series(connected_components_dict, name='connected_component_id').reset_index()
    connected_components.columns = [Constants.NODE_NAME, 'connected_component_id']
    connected_components['connected_component_size'] = connected_components.groupby('connected_component_id')['connected_component_id'].transform('count')
    algo_series["connected_component"] = connected_components
    logging.info("Graph analytics - connected_components computed in {:.4f} seconds".format(time.time()-start))

# merge all series into one (merge both with source and target columns if output a dataset of edges)
for series in algo_series.values():
    for node_col in node_columns:
        output_df = output_df.merge(series, left_on=params[node_col], right_on=Constants.NODE_NAME, how='left',
                                    suffixes=('_source', '_target')).drop([Constants.NODE_NAME], axis=1)

output_dataset.write_with_schema(output_df)
