import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role
from dku_constants import Constants


class AlgorithmError(Exception):
    """ Raised when error is from the Algorithm """
    pass


def get_input_dataset(role):
    names = get_input_names_for_role(role)
    return dataiku.Dataset(names[0]) if len(names) > 0 else None


def get_output_dataset(role):
    names = get_output_names_for_role(role)
    return dataiku.Dataset(names[0]) if len(names) > 0 else None


def get_analytics_recipe_params(recipe_config):
    params = {}
    params[Constants.SOURCE] = recipe_config['node_A']
    params[Constants.TARGET] = recipe_config['node_B']

    params[Constants.DIRECTED] = recipe_config.get('directed_graph', False)
    params[Constants.OUTPUT_TYPE] = recipe_config.get('output_type', 'output_nodes')
    params[Constants.COMPUTATION_MODE] = recipe_config.get('computation_mode', 'select_features')

    if params[Constants.COMPUTATION_MODE] != 'compute_all_features':
        params[Constants.EIGEN_CENTRALITY] = recipe_config.get('eigenvector_centrality', False)
        params[Constants.CLUSTERING] = recipe_config.get('clustering', False)
        params[Constants.CLOSENESS] = recipe_config.get('closeness', False)
        params[Constants.PAGERANK] = recipe_config.get('pagerank', False)
        params[Constants.SQ_CLUSTERING] = recipe_config.get('sq_clustering', False)
        # algorithm only for undirected graphs
        params[Constants.TRIANGLES] = recipe_config.get('triangles', False) if not params[Constants.DIRECTED] else False
    else:
        params[Constants.EIGEN_CENTRALITY] = True
        params[Constants.CLUSTERING] = True
        params[Constants.CLOSENESS] = True
        params[Constants.PAGERANK] = True
        params[Constants.SQ_CLUSTERING] = True
        # algorithm only for undirected graphs
        params[Constants.TRIANGLES] = not params[Constants.DIRECTED]

    return params


def get_clustering_recipe_params(recipe_config):
    params = {}
    params[Constants.SOURCE] = recipe_config['source']
    params[Constants.TARGET] = recipe_config['target']

    params[Constants.WEIGHT] = recipe_config.get('weight', None)

    params[Constants.DIRECTED] = recipe_config.get('directed_graph', False)
    params[Constants.OUTPUT_TYPE] = recipe_config.get('output_type', 'output_nodes')
    params[Constants.COMPUTATION_MODE] = recipe_config.get('computation_mode', 'select_features')

    if params[Constants.COMPUTATION_MODE] != 'compute_all_features':
        params[Constants.FASTGREEDY] = recipe_config.get('fastgreedy', False)
        params[Constants.MULTILEVEL] = recipe_config.get('multilevel', False)
        params[Constants.INFOMAP] = recipe_config.get('infomap', False)
        params[Constants.WALKTRAP] = recipe_config.get('walktrap', False)
    else:
        params[Constants.FASTGREEDY] = True
        params[Constants.MULTILEVEL] = True
        params[Constants.INFOMAP] = True
        params[Constants.WALKTRAP] = True
    return params


def get_bipartite_recipe_params(recipe_config):
    params = {}
    params[Constants.GRAPH_OF] = recipe_config['create_graph_of']
    params[Constants.LINKED_BY] = recipe_config['linked_by']
    params[Constants.WEIGHTED] = recipe_config['weighted']
    return params
