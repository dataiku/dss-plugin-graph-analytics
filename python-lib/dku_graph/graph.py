import time
import random
import numpy as np
import pandas as pd
import logging
import igraph
from constants import EXISTING_COLORS


class Graph:
    """
    class to create a graph object that consists of two dictionaries:
    - nodes: keys are nodes id and values are dictionaries of nodes properties (id, group, value, title, x, y)
    - edges: keys are pairs of nodes id (source, target) and values are dictionaries of edges properties (from, to, label, value, title)
    """

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
        self.directed_edges = graph_params.get('directed_edges', True)
        self.numerical_colors = graph_params.get('numerical_colors', False)

    def create_graph(self, df):
        """
        iterate over the datframe and add nodes and edges to the graph object
        """
        logging.info("Creating graph object ...")
        start = time.time()
        source_nodes, target_nodes = set(), set()
        nodes_nb = 0
        nodes = {}
        edges = {}

        self._check_data_type(df)

        for idx, row in df.iterrows():
            if nodes_nb >= self.max_nodes:
                break

            src = row[self.source]
            tgt = row[self.target]
            if src not in source_nodes and src not in target_nodes:
                nodes[src] = self._create_source_node(row)
                source_nodes.add(src)
                nodes_nb += 1
            elif src not in source_nodes and src in target_nodes:
                self._update_source_node(row, nodes[src])
                source_nodes.add(src)

            if tgt not in source_nodes and tgt not in target_nodes:
                nodes[tgt] = self._create_target_node(row)
                target_nodes.add(tgt)
                nodes_nb += 1
            elif tgt in source_nodes and tgt not in target_nodes:
                self._update_target_node(row, nodes[tgt])
                target_nodes.add(tgt)

            if not self.directed_edges:
                try:
                    if tgt < src:  # edges are sorted when directed
                        src, tgt = tgt, src
                except Exception as e:
                    logging.info("Exception when comparing source ({}) and target ({}) nodes: {}".format(src, tgt, e))
                    continue
            if (src, tgt) not in edges:
                edges[(src, tgt)] = self._create_edge(row, src, tgt)
            elif not self.edges_width:  # here edge weight must be computed (cause width is weight by default)
                self._update_edge(edges[(src, tgt)])

        for node_id in nodes:
            self._add_node_title(nodes[node_id])
        for edge_id in edges:
            self._add_edge_title(edges[edge_id])

        self.groups = {}
        self.group_values = set()
        for node_id in nodes:
            self._add_group_value(nodes[node_id])
        self._create_groups()

        # compute layout
        self.nodes = nodes
        self.edges = edges

        logging.info("Graph object created in {:.4f} seconds".format(time.time()-start))

    def _create_source_node(self, row):
        node = {'id': row[self.source], 'label': row[self.source]}
        if self.source_nodes_color:
            node['group'] = row[self.source_nodes_color]
        if self.source_nodes_size and not np.isnan(row[self.source_nodes_size]):
            node['value'] = row[self.source_nodes_size]
        return node

    def _create_target_node(self, row):
        node = {'id': row[self.target], 'label': row[self.target]}
        if self.target_nodes_color:
            node['group'] = row[self.target_nodes_color]
        if self.target_nodes_size and not np.isnan(row[self.target_nodes_size]):
            node['value'] = row[self.target_nodes_size]
        return node

    def _create_edge(self, row, src, tgt):
        edge = {'from': src, 'to': tgt}
        if self.edges_caption:
            edge['label'] = str(row[self.edges_caption])
        if self.edges_width:
            if not np.isnan(row[self.edges_width]):
                edge['value'] = row[self.edges_width]
        else:  # initialize edge weight
            edge['value'] = 1
        return edge

    def _update_edge(self, edge_params):
        """ update value (weight) of edges that have already been initialized when self.edges_width is False """
        edge_params['value'] += 1

    def _update_source_node(self, row, node_params):
        """ overwrite the old params that were set for the node when it was a target node (or add new params)"""
        if self.source_nodes_color:
            node_params['group'] = row[self.source_nodes_color]
        if self.source_nodes_size and not np.isnan(row[self.source_nodes_size]):
            node_params['value'] = row[self.source_nodes_size]

    def _update_target_node(self, row, node_params):
        """ add new params if they were not set for the node when it was a source node """
        if 'group' not in node_params and self.target_nodes_color:
            node_params['group'] = row[self.target_nodes_color]
        if 'value' not in node_params and self.target_nodes_size and not np.isnan(row[self.target_nodes_size]):
            node_params['value'] = row[self.target_nodes_size]

    def _add_node_title(self, node_params):
        """ create a nice title string to display on node popup """
        title = "id: {}".format(node_params['id'])
        if 'group' in node_params:
            title += "<br>color: {}".format(node_params['group'])
        if 'value' in node_params:
            title += "<br>size: {}".format(node_params['value'])
        node_params['title'] = title

    def _add_edge_title(self, edge_params):
        """ create a nice title string to display on edge popup """
        title = "{} -> {}".format(edge_params['from'], edge_params['to'])
        if 'label' in edge_params:
            title += "<br>caption: {}".format(edge_params['label'])
        if 'value' in edge_params:
            title += "<br>width: {}".format(edge_params['value'])
        edge_params['title'] = title

    def _create_igraph(self):
        iGraph = igraph.Graph()
        node_to_id = {}
        id_to_node = {}
        for i, node in enumerate(self.nodes):
            node_to_id[node] = i
            id_to_node[i] = node
        edge_list = []
        for edge in self.edges:
            edge_list += [(node_to_id[edge[0]], node_to_id[edge[1]])]

        iGraph.add_vertices(i+1)
        iGraph.add_edges(edge_list)

        return iGraph, id_to_node

    def _contract_nodes(self, positions, translation_factor=0.95, std_nb=2):
        """
        contract nodes by removing empty zones between them, nodes that are 'too' far from others
        are translated toward their neighbors

        :param positions: a 2D-array of x and y positions
        :param translation_factor: how much of the distance to the closest node (one one axis) to remove
        :param std_nb: nodes are 'too' far if the distance to the closest node on one axis is more than
        the average distance between nodes + 'std_nb' standard-deviation
        """
        columns = ['x', 'y']
        df = pd.DataFrame(positions, columns=columns)
        df['id'] = df.index

        for col in columns:
            df = df.sort_values(by=[col])
            df['{}_diff'.format(col)] = df[col] - df[col].shift(1)
            df = df.sort_values(by=['{}_diff'.format(col)], ascending=False).reset_index(drop=True)

            outliers_bound = df['{}_diff'.format(col)].mean() + std_nb * df['{}_diff'.format(col)].std()

            i = 0
            threshold = df.loc[i, col]
            diff = df.loc[i, '{}_diff'.format(col)]
            while diff > outliers_bound:
                mask = (df[col] >= threshold)
                df_valid = df[mask]
                df.loc[mask, col] = df_valid[col] - diff * translation_factor

                i += 1
                threshold = df.loc[i, col]
                diff = df.loc[i, '{}_diff'.format(col)]

            logging.info("{} translations done in axis {}".format(i, col))

        df = df.sort_values(by=['id'], ascending=True).reset_index(drop=True)
        return df[columns].values

    def _rescale_positions(self, positions, scale):
        """ return a numpy array of scaled positions between -scale and +scale """
        positions -= positions.mean()
        positions = scale * positions / abs(positions.max())
        return positions

    def _transform_positions(self, positions, scale=1, scale_ratio=1):
        """
        rescale positions using 'scale' for the y-axis and 'scale'*'scale_ratio' for the x-axis
        """
        positions[:, 0] = self._rescale_positions(positions[:, 0], scale=scale*scale_ratio)  # x-axis
        positions[:, 1] = self._rescale_positions(positions[:, 1], scale=scale)  # y-axis

        return positions

    def compute_layout(self, scale, scale_ratio):
        """
        create an iGraph object from the Graph class,
        compute nodes positions using the Fruchterman-Reingold layout algorithm of iGraph,
        tranform and rescale the positions to improve the layout,
        update the nodes properties with the positions
        """
        logging.info("Computing layout ...")
        start = time.time()

        iGraph, id_to_node = self._create_igraph()

        positions = np.array(iGraph.layout_fruchterman_reingold(grid=False))
        # positions = np.array(iGraph.layout_lgl())

        if len(positions) > 200:
            positions = self._contract_nodes(positions)

        positions = self._transform_positions(positions, scale, scale_ratio)

        for i, pos in enumerate(positions):
            self.nodes[id_to_node[i]].update({'x': pos[0], 'y': pos[1]})

        logging.info("Layout computed in {:.4f} seconds for {} nodes".format(time.time()-start, len(positions)))

    def _check_data_type(self, df):
        for col in [self.source_nodes_size, self.target_nodes_size, self.edges_width]:
            if col and df[col].dtype not in [np.dtype(int), np.dtype(float)]:
                raise ValueError("Columns for size or width must be numerical but column '{}' is not".format(col))

        if self.numerical_colors:
            for label, col in [('Source', self.source_nodes_color), ('Target', self.target_nodes_color)]:
                if col and df[col].dtype not in [np.dtype(int), np.dtype(float)]:
                    raise ValueError("{} nodes color column must be numerical but column '{}' is not".format(label, col))

    def _add_group_value(self, node_params):
        """ add all unique groups to self.group_values and add 'nogroup' for nodes without a group """
        if 'group' in node_params:
            self.group_values.add(node_params['group'])
        else:
            node_params['group'] = "nogroup"

    def _create_groups(self):
        """
        map a color to each group
        for numerical column as color column, compute a range of color from white to red depending on the value
        """
        self.groups["nogroup"] = {'color': "rgba(0, 125, 255, 1)"}
        if self.numerical_colors:
            mini, maxi = min(self.group_values), max(self.group_values)
            for group in self.group_values:
                x = (maxi - group)/(maxi - mini) * 225  # would be white if 255
                self.groups[group] = {'color': "rgba(255, {0}, {0}, 1)".format(x)}
        else:
            colors = EXISTING_COLORS[:]
            for group in self.group_values:
                if group != "nogroup":
                    if len(colors) > 0:
                        color = colors.pop()
                    else:  # all existing colors have been used
                        color_code = list(np.random.choice(range(50, 200), size=3))
                        color = "rgba({}, {}, {}, 1)".format(color_code[0], color_code[1], color_code[2])
                    self.groups[group] = {'color': color}
