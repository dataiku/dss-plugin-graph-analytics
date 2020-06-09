import dataiku
from flask import request
import pandas as pd
import json
import traceback
import logging
import time
from dku_filtering.filtering import filter_dataframe

logger = logging.getLogger(__name__)


class Graph:

    def __init__(self, graph_params):
        self.source = graph_params.get('source', None)
        self.target = graph_params.get('target', None)
        self.max_nodes = int(graph_params.get('max_nodes', None))
        self.source_nodes_color = graph_params.get('source_nodes_color', None)
        self.source_nodes_size = graph_params.get('source_nodes_size', None)
        self.target_nodes_color = graph_params.get('target_nodes_color', None)
        self.target_nodes_size = graph_params.get('target_nodes_size', None)
        self.edges_caption = graph_params.get('edges_caption', None)
        self.edges_width = graph_params.get('edges_width', None)

        print(self.__dict__)

    # def create_graph(self, df):
    #     logger.info("Creating graph object ...")
    #     start = time.time()
    #     nodes_set, nodes_nb = set(), 0
    #     nodes, edges = [], []
    #     for idx, row in df.iterrows():
    #         if nodes_nb > self.max_nodes:
    #             break
    #         if row[self.source] not in nodes_set:
    #             nodes.append(self.create_source_node(row))
    #             nodes_set.add(row[self.source])
    #             nodes_nb += 1
    #         if row[self.target] not in nodes_set:
    #             nodes.append(self.create_target_node(row))
    #             nodes_set.add(row[self.target])
    #             nodes_nb += 1
    #         edges.append(self.create_edge(row))

    #     self.nodes = nodes
    #     self.edges = edges
    #     logger.info("Graph object created in {:.4f} seconds".format(time.time()-start))

    def create_graph(self, df):
        logger.info("Creating graph object ...")
        start = time.time()
        source_nodes, target_nodes = set(), set()
        nodes_nb = 0
        nodes = {}
        edges = []
        for idx, row in df.iterrows():
            if nodes_nb >= self.max_nodes:
                break

            src = row[self.source]
            tgt = row[self.target]
            if src not in source_nodes and src not in target_nodes:
                nodes[src] = self.create_source_node(row)
                source_nodes.add(src)
                # nodes_set.add(src)
                nodes_nb += 1
            elif src not in source_nodes and src in target_nodes:
                # nodes[src] = self.update_source_node(row, nodes[src])
                self.update_source_node(row, nodes[src])
                source_nodes.add(src)

            if tgt not in source_nodes and tgt not in target_nodes:
                nodes[tgt] = self.create_target_node(row)
                target_nodes.add(tgt)
                nodes_nb += 1
            elif tgt in source_nodes and tgt not in target_nodes:
                self.update_target_node(row, nodes[tgt])
                target_nodes.add(tgt)

            # if row[self.source] not in nodes_set:
            #     nodes.append(self.create_source_node(row))
            #     nodes_set.add(row[self.source])
            #     nodes_nb += 1
            # if row[self.target] not in nodes_set:
            #     nodes.append(self.create_target_node(row))
            #     nodes_set.add(row[self.target])
            #     nodes_nb += 1
            edges.append(self.create_edge(row))

        for node_id in nodes:
            self.add_node_title(nodes[node_id])
        for edge_params in edges:
            self.add_edge_title(edge_params)

        self.nodes = nodes.values()
        self.edges = edges
        logger.info("Graph object created in {:.4f} seconds".format(time.time()-start))

    def create_source_node(self, row):
        node = {'id': row[self.source], 'label': row[self.source]}
        if self.source_nodes_color:
            node['group'] = row[self.source_nodes_color]
        if self.source_nodes_size:
            node['value'] = row[self.source_nodes_size]
        return node

    def create_target_node(self, row):
        node = {'id': row[self.target], 'label': row[self.target]}
        if self.target_nodes_color:
            node['group'] = row[self.target_nodes_color]
        if self.target_nodes_size:
            node['value'] = row[self.target_nodes_size]
        return node

    def create_edge(self, row):
        edge = {'from': row[self.source], 'to': row[self.target]}
        if self.edges_caption:
            edge['label'] = row[self.edges_caption]
        if self.edges_width:
            edge['value'] = row[self.edges_width]
        return edge

    def update_source_node(self, row, node_params):
        """ overwrite the old params that were set for the node when it was a target node (or add new params)"""
        if self.source_nodes_color:
            node_params['group'] = row[self.source_nodes_color]
        if self.source_nodes_size:
            node_params['value'] = row[self.source_nodes_size]

    def update_target_node(self, row, node_params):
        """ add new params if they were not set for the node when it was a source node """
        if 'group' not in node_params and self.target_nodes_color:
            node_params['group'] = row[self.target_nodes_color]
        if 'value' not in node_params and self.target_nodes_size:
            node_params['value'] = row[self.target_nodes_size]

    def add_node_title(self, node_params):
        """ create a nice title string to display on node popup """
        title = "id: {}".format(node_params['id'])
        if 'group' in node_params:
            title += "<br>color: {}".format(node_params['group'])
        if 'value' in node_params:
            title += "<br>size: {}".format(node_params['value'])
        node_params['title'] = title

    def add_edge_title(self, edge_params):
        """ create a nice title string to display on edge popup """
        title = "{} -> {}".format(edge_params['from'], edge_params['to'])
        if 'label' in edge_params:
            title += "<br>caption: {}".format(edge_params['label'])
        if 'value' in edge_params:
            title += "<br>width: {}".format(edge_params['value'])
        edge_params['title'] = title


@app.route('/reformat_data')
def reformat_data():
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

        # nodes, edges = graph.nodes, graph.edges
        # print("nodes : ", nodes)
        # print("edges: ", edges)

        return json.dumps({'nodes': graph.nodes, 'edges': graph.edges})

        # return json.dumps({'result': df.values.tolist()})
    except Exception as e:
        logger.error(traceback.format_exc())
        return str(e), 500
