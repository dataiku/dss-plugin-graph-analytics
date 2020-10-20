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
        self.source_column = graph_params.get('source', None)
        self.target_column = graph_params.get('target', None)
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
        self.nodes = {}
        self.edges = {}

        self._check_data_type(df)

        for idx, row in df.iterrows():
            if nodes_nb >= self.max_nodes:
                break

            source = row[self.source_column]
            target = row[self.target_column]

            nodes_nb += self._process_source(source, row, source_nodes, target_nodes)
            nodes_nb += self._process_target(target, row, source_nodes, target_nodes)

            if not self.directed_edges:
                try:
                    if target < source:  # edges are sorted when directed
                        source, target = target, source
                except Exception as e:
                    logging.info("Exception when comparing source ({}) and target ({}) nodes: {}".format(source, target, e))
                    continue

            self._process_edge(source, target, row)

        for node_id in self.nodes:
            self._add_node_title(self.nodes[node_id])
        for edge_id in self.edges:
            self._add_edge_title(self.edges[edge_id])

        self.groups = {}
        if self.source_nodes_color or self.target_nodes_color:
            self.group_values = set()
            for node_id in self.nodes:
                self._add_group_value(self.nodes[node_id])
            self._create_groups()

        logging.info("Graph object created in {:.4f} seconds".format(time.time()-start))

    def _process_source(self, source, row, source_nodes, target_nodes):
        """ add source node if not already seen and update it if it was seen as a target node """
        if source not in source_nodes and source not in target_nodes:
            self.nodes[source] = self._create_source_node(row)
            source_nodes.add(source)
            return 1
        elif source not in source_nodes and source in target_nodes:
            self._update_source_node(row, self.nodes[source])
            source_nodes.add(source)
        return 0

    def _process_target(self, target, row, source_nodes, target_nodes):
        """ add target node if not already seen and update it if it was seen as a source node """
        if target not in source_nodes and target not in target_nodes:
            self.nodes[target] = self._create_target_node(row)
            target_nodes.add(target)
            return 1
        elif target in source_nodes and target not in target_nodes:
            self._update_target_node(row, self.nodes[target])
            target_nodes.add(target)
        return 0

    def _process_edge(self, source, target, row):
        """ add edge node if not already seen and update the width if width is based on weight """
        if (source, target) not in self.edges:
            self.edges[(source, target)] = self._create_edge(row, source, target)
        elif not self.edges_width:  # here edge weight must be computed (cause width is weight by default)
            self._update_edge(self.edges[(source, target)])

    def _create_source_node(self, row):
        node = {'id': row[self.source_column], 'label': row[self.source_column]}
        if self.source_nodes_color:
            node['group'] = row[self.source_nodes_color]
        if self.source_nodes_size and not np.isnan(row[self.source_nodes_size]):
            node['value'] = row[self.source_nodes_size]
        return node

    def _create_target_node(self, row):
        node = {'id': row[self.target_column], 'label': row[self.target_column]}
        if self.target_nodes_color:
            node['group'] = row[self.target_nodes_color]
        if self.target_nodes_size and not np.isnan(row[self.target_nodes_size]):
            node['value'] = row[self.target_nodes_size]
        return node

    def _create_edge(self, row, source, target):
        edge = {'from': source, 'to': target}
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

        iGraph.add_vertices(len(self.nodes))
        iGraph.add_edges(edge_list)

        return iGraph, id_to_node

    def _contract_nodes(self, positions, translation_factor=0.8, std_nb=2):
        """
        contract nodes by removing empty zones between them, nodes that are 'too' far from others
        are translated toward their neighbors

        :param positions: a 2D-array of x and y positions
        :param translation_factor: how much of the distance to the closest node (one one axis) to remove
        :param std_nb: nodes are 'too' far if the distance to the closest node on one axis is more than
        the average distance between nodes + 'std_nb' standard-deviation
        """
        columns = ['x', 'y']
        positions_df = pd.DataFrame(positions, columns=columns)
        positions_df['id'] = positions_df.index

        for col in columns:
            positions_df = positions_df.sort_values(by=[col])
            consecutive_difference_column = '{}_diff'.format(col)
            positions_df[consecutive_difference_column] = positions_df[col] - positions_df[col].shift(1)
            positions_df = positions_df.sort_values(by=[consecutive_difference_column], ascending=False).reset_index(drop=True)

            outliers_bound = positions_df[consecutive_difference_column].mean() + std_nb * positions_df[consecutive_difference_column].std()

            i = 0
            threshold = positions_df.loc[i, col]
            diff = positions_df.loc[i, consecutive_difference_column]
            while diff > outliers_bound:
                mask = (positions_df[col] >= threshold)
                masked_df = positions_df[mask]
                positions_df.loc[mask, col] = masked_df[col] - diff * translation_factor

                i += 1
                threshold = positions_df.loc[i, col]
                diff = positions_df.loc[i, consecutive_difference_column]

            logging.info("{} translations done in axis {}".format(i, col))

        positions_df = positions_df.sort_values(by=['id'], ascending=True).reset_index(drop=True)
        return positions_df[columns].values

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

    def _igraph_layout_algorithms(self, iGraph, kamada_iter=5000, fruchterman_iter=300):
        """ 
        compute nodes positions of an iGraph object,
        first generate a fast inital layout using the Kamada-Kawai algorithm,
        then use the slower Fruchterman-Reingold algorithm to improve the layout,
        return the positions as a numpy array
        """
        kamada_start = time.time()
        kamada_positions = iGraph.layout_kamada_kawai(maxiter=kamada_iter)
        fruchterman_start = time.time()
        logging.info("Kamada-Kawai layout computed in {:.4f} seconds".format(fruchterman_start-kamada_start))
        fruchterman_positions = iGraph.layout_fruchterman_reingold(seed=kamada_positions, grid=False, niter=fruchterman_iter)
        logging.info("Fruchterman-Reingold layout computed in {:.4f} seconds".format(time.time()-fruchterman_start))
        return np.array(fruchterman_positions)

    def compute_layout(self, scale, scale_ratio):
        """
        create an iGraph object from the Graph class,
        compute nodes positions using igraph layout algorithms
        tranform and rescale the positions to improve the layout,
        update the nodes properties with the positions
        """
        logging.info("Computing layout ...")
        start_time = time.time()

        iGraph, id_to_node = self._create_igraph()

        positions = self._igraph_layout_algorithms(iGraph)

        if len(positions) > 500:
            positions = self._contract_nodes(positions)

        positions = self._transform_positions(positions, scale, scale_ratio)

        for i, pos in enumerate(positions):
            self.nodes[id_to_node[i]].update({'x': pos[0], 'y': pos[1]})

        logging.info("Global layout computed in {:.4f} seconds for {} nodes".format(time.time()-start_time, len(positions)))

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
        self.groups["nogroup"] = {'color': "#85bcf8"}
        if self.numerical_colors:
            if len(self.group_values) > 0:
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
