import dataiku
from flask import request
import simplejson as json
import traceback
import logging
from dku_filtering.filtering import filter_dataframe
from dku_graph.graph import Graph

logger = logging.getLogger(__name__)


@app.route('/get_graph_data')
def get_graph_data():
    try:
        config = json.loads(request.args.get('config', None))
        filters = json.loads(request.args.get('filters', None))

        dataset_name = config.get('dataset_name')
        # graph_params = get_graph_params(config)

        df = dataiku.Dataset(dataset_name).get_dataframe()
        if df.empty:
            raise Exception("Dataframe is empty")

        if len(filters) > 0:  # apply filters to dataframe
            df = filter_dataframe(df, filters)

        graph = Graph(config)
        graph.create_graph(df)
        graph.compute_layout()

        nodes, edges = list(graph.nodes.values()), list(graph.edges.values())
        # results = json.dumps({'nodes': graph.nodes}, ignore_nan=True)

        return json.dumps({'nodes': nodes, 'edges': edges, 'groups': graph.groups}, ignore_nan=True)

    except Exception as e:
        logger.error(traceback.format_exc())
        return str(e), 500
