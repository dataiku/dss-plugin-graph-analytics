import dataiku
from flask import request
import simplejson as json
import traceback
import logging
import numpy as np
from dku_filtering.filtering import filter_dataframe
from dku_graph.graph import Graph


def convert_numpy_int64_to_int(o):
    if isinstance(o, np.int64):
        return int(o)
    raise TypeError


@app.route('/get_graph_data', methods=['POST'])
def get_graph_data():
    try:
        data = json.loads(request.data)

        config = json.loads(data.get('config', None))
        filters = json.loads(data.get('filters', None))
        scale_ratio = float(data.get('scale_ratio', 1))

        dataset_name = config.get('dataset_name')

        df = dataiku.Dataset(dataset_name).get_dataframe(limit=100000)
        if df.empty:
            raise Exception("Dataframe is empty")

        if len(filters) > 0:  # apply filters to dataframe
            df = filter_dataframe(df, filters)

        graph = Graph(config)
        graph.create_graph(df)

        scale = np.sqrt(len(graph.nodes)) * 100
        graph.compute_layout(scale=scale, scale_ratio=scale_ratio)

        nodes, edges = list(graph.nodes.values()), list(graph.edges.values())

        return json.dumps({'nodes': nodes, 'edges': edges, 'groups': graph.groups}, ignore_nan=True, default=convert_numpy_int64_to_int)

    except Exception as e:
        logging.error(traceback.format_exc())
        return str(e), 500
