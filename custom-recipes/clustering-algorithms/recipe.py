from dataiku.customrecipe import get_recipe_config
from utils import get_input_dataset, get_output_dataset, get_clustering_recipe_params, AlgorithmError
from constants import Constants
from dku_graph_analytics.graph_clustering import CLUSTERING_ALGORITHMS, fix_dendrogram
import logging
import pandas as pd
import numpy as np
import igraph
import time


input_dataset = get_input_dataset('input_dataset')
output_dataset = get_output_dataset('output_dataset')

recipe_config = get_recipe_config()
params = get_clustering_recipe_params(recipe_config)

source, target = params[Constants.SOURCE], params[Constants.TARGET]

df = input_dataset.get_dataframe()

columns = [source, target]
if params[Constants.WEIGHT]:
    columns += [params[Constants.WEIGHT]]
# keep only the necessary columns
df_graph = df[columns]

if df_graph[source].dtype != df_graph[target].dtype:
    raise TypeError("Source and Target columns must have same datatype")

# swap source and target so that source < target to get unique undirected edges
if not params[Constants.DIRECTED]:  # and df_graph[source].dtype == df_graph[target].dtype:
    df_graph[source], df_graph[target] = np.where(df_graph[source] > df_graph[target],
                                                  [df_graph[target], df_graph[source]],
                                                  [df_graph[source], df_graph[target]])

# groupby to get unique edges
if params[Constants.WEIGHT]:
    # WEIGHT input parameter is summed within same edges
    df_graph = df_graph.groupby([source, target]).agg({params[Constants.WEIGHT]: "sum"}).reset_index()
else:
    # if no weight column was chosen by the user, then the number of same edge becomes the weight attribute
    df_graph = df_graph.groupby([source, target]).size().reset_index(name=Constants.WEIGHT)

df_graph.columns = [source, target, Constants.WEIGHT]

start = time.time()
logging.info("Graph clustering - Creating igraph graph ...")
iGraph = igraph.Graph.TupleList(df_graph.values, weights=True, directed=params[Constants.DIRECTED])

logging.info("Graph clustering - Graph created in {:.4f} seconds".format(time.time()-start))

# output all edges or only nodes
if params[Constants.OUTPUT_TYPE] == 'output_edges':
    df_output = df
    node_columns = [Constants.SOURCE, Constants.TARGET]
else:
    df_output = pd.DataFrame(iGraph.vs["name"], columns=[source])
    node_columns = [Constants.SOURCE]

# computing all selected graph clustering algorithms
for algo, algo_params in CLUSTERING_ALGORITHMS.items():
    label, method = algo_params['label'], algo_params['method']
    if params[algo]:
        if not params.get(algo_params.get('param_restriction', None), None):
            start = time.time()
            logging.info("Graph clustering - Computing {} ...".format(label))
            try:
                # call the clustering method on iGraph with the right attributes
                result = getattr(iGraph, method[0])(**method[1])
                logging.info("Graph clustering - {} computed in {:.4f} seconds".format(label, time.time()-start))
            except Exception as e:
                raise AlgorithmError("Error while computing {}: {}".format(label, e))
            else:
                if isinstance(result, igraph.clustering.VertexDendrogram):
                    # create a unique connected dendogram for when the graph is not connected
                    fix_dendrogram(iGraph, result)
                    clusters = result.as_clustering()
                elif isinstance(result, igraph.clustering.VertexClustering):
                    clusters = result
                else:
                    raise ValueError("Not a VertexDendrogram nor a VertexClustering !")
                membership = clusters.membership

                df_res = pd.DataFrame(columns=[Constants.NODE_NAME, label])
                df_res[Constants.NODE_NAME] = iGraph.vs["name"]
                df_res[label] = membership

                # merge result dataframe into df_output (merge both with source and target columns if output a dataset of edges)
                for node_col in node_columns:
                    df_output = df_output.merge(df_res, left_on=params[node_col], right_on=Constants.NODE_NAME, how='left',
                                                suffixes=('_source', '_target')).drop([Constants.NODE_NAME], axis=1)

output_dataset.write_with_schema(df_output)
