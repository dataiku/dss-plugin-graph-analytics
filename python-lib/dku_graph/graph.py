import time
import networkx as nx
# import pandas as pd
import logging

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
        self.directed_edges = graph_params.get('directed_edges', False)

        print(self.__dict__)

    def create_graph(self, df):
        logger.info("Creating graph object ...")
        start = time.time()
        source_nodes, target_nodes = set(), set()
        nodes_nb = 0
        nodes = {}
        edges = {}
        for idx, row in df.iterrows():
            if nodes_nb >= self.max_nodes:
                break

            src = row[self.source]
            tgt = row[self.target]
            if src not in source_nodes and src not in target_nodes:
                nodes[src] = self.create_source_node(row)
                source_nodes.add(src)
                nodes_nb += 1
            elif src not in source_nodes and src in target_nodes:
                self.update_source_node(row, nodes[src])
                source_nodes.add(src)

            if tgt not in source_nodes and tgt not in target_nodes:
                nodes[tgt] = self.create_target_node(row)
                target_nodes.add(tgt)
                nodes_nb += 1
            elif tgt in source_nodes and tgt not in target_nodes:
                self.update_target_node(row, nodes[tgt])
                target_nodes.add(tgt)

            if not self.directed_edges:
                try:
                    if tgt < src:  # edges are sorted when directed
                        src, tgt = tgt, src
                except Exception as e:
                    logger.info("Exception when comparing source ({}) and target ({}) nodes: {}".format(src, tgt, e))
                    continue
            if (src, tgt) not in edges:
                edges[(src, tgt)] = self.create_edge(row, src, tgt)
            elif not self.edges_width:  # here edge weight must be computed (cause width is weight by default)
                self.update_edge(edges[(src, tgt)])

            # edges.append(self.create_edge(row))

        for node_id in nodes:
            self.add_node_title(nodes[node_id])
        for edge_id in edges:
            self.add_edge_title(edges[edge_id])

        # compute layout
        self.nodes = nodes
        self.edges = edges

        # self.nodes = list(nodes.values())
        # self.edges = list(edges.values())
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

    def create_edge(self, row, src, tgt):
        edge = {'from': src, 'to': tgt}
        if self.edges_caption:
            edge['label'] = row[self.edges_caption]
        if self.edges_width:
            edge['value'] = row[self.edges_width]
        else:  # initialize edge weight
            edge['value'] = 1
        return edge

    def update_edge(self, edge_params):
        """ update value (weight) of edges that have already been initialized when self.edges_width is False """
        edge_params['value'] += 1
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

    def compute_layout(self):
        logger.info("Computing layout ...")
        start = time.time()
        if self.directed_edges:
            G = nx.Graph()
        else:
            G = nx.DiGraph()

        G.add_nodes_from(list(self.nodes.keys()))
        G.add_edges_from(list(self.edges.keys()))

        # positions = nx.nx_agraph.graphviz_layout(G, prog='sfdp')
        # positions = nx.nx_pydot.pydot_layout(G, prog='sfdp')

        # for node, pos in positions.items():
        #     self.nodes[node].update({'x': pos[0], 'y': pos[1]})

        # logger.info("Layout computed in {:.4f} seconds".format(time.time()-start))
