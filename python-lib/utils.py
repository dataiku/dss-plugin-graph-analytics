import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role


def get_input_dataset(role):
    names = get_input_names_for_role(role)
    return dataiku.Dataset(names[0]) if len(names) > 0 else None


def get_output_dataset(role):
    names = get_output_names_for_role(role)
    return dataiku.Dataset(names[0]) if len(names) > 0 else None


def get_recipe_params(recipe_config):
    params = {}
    params['source'] = recipe_config['node_A']
    params['target'] = recipe_config['node_B']

    # new parameters
    params['directed_graph'] = recipe_config.get('directed_graph', False)
    params['output_type'] = recipe_config.get('output_type', 'output_nodes')
    params['computation_mode'] = recipe_config.get('computation_mode', 'select_features')

    if params['computation_mode'] != 'compute_all_features':
        params['eigenvector_centrality'] = recipe_config.get('eigenvector_centrality', False)
        params['clustering'] = recipe_config.get('clustering', False)
        params['closeness'] = recipe_config.get('closeness', False)
        params['pagerank'] = recipe_config.get('pagerank', False)
        params['sq_clustering'] = recipe_config.get('sq_clustering', False)
        # algorithm only for undirected graphs
        params['triangles'] = recipe_config.get('triangles', False) if not params['directed_graph'] else False
    else:
        params['eigenvector_centrality'] = True
        params['clustering'] = True
        params['closeness'] = True
        params['pagerank'] = True
        params['sq_clustering'] = True
        # algorithm only for undirected graphs
        params['triangles'] = not params['directed_graph']

    return params
