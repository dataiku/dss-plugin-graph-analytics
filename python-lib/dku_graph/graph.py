import time
import numpy as np
import pandas as pd
import logging
import igraph


def rescale_positions(positions, scale=1):
    """ return a numpy array of scaled positions between -scale and +scale """ 
    positions -= positions.mean()
    positions = scale * positions / abs(positions.max())
    return positions


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
        self.directed_edges = graph_params.get('directed_edges', True)
        self.numerical_colors = graph_params.get('numerical_colors', False)

    def create_graph(self, df):
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

            # edges.append(self._create_edge(row))

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
        if self.source_nodes_size:
            node['value'] = row[self.source_nodes_size]
        return node

    def _create_target_node(self, row):
        node = {'id': row[self.target], 'label': row[self.target]}
        if self.target_nodes_color:
            node['group'] = row[self.target_nodes_color]
        if self.target_nodes_size:
            node['value'] = row[self.target_nodes_size]
        return node

    def _create_edge(self, row, src, tgt):
        edge = {'from': src, 'to': tgt}
        if self.edges_caption:
            edge['label'] = str(row[self.edges_caption])
        if self.edges_width:
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
        if self.source_nodes_size:
            node_params['value'] = row[self.source_nodes_size]

    def _update_target_node(self, row, node_params):
        """ add new params if they were not set for the node when it was a source node """
        if 'group' not in node_params and self.target_nodes_color:
            node_params['group'] = row[self.target_nodes_color]
        if 'value' not in node_params and self.target_nodes_size:
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

    def _transform_positions(self, positions, scale_ratio=1, remove_empty_zones=-1):
        """
        remove empty zones by translating nodes that are too far (distance on one axis more than than 2 STD away from other nodes)
        (do it if there are more than remove_empty_zones nodes, do nothing if it's -1)
        and rescale positions based on the total number of nodes
        """
        # remove empty zones when more than remove_empty_zones nodes
        N = len(positions)
        if remove_empty_zones != -1 and N > remove_empty_zones:
            columns = ['x', 'y']
            translation_factor = 0.95
            df = pd.DataFrame(positions, columns=columns)
            df['id'] = df.index

            for col in columns:
                df = df.sort_values(by=[col])
                df['{}_diff'.format(col)] = df[col] - df[col].shift(1)
                df = df.sort_values(by=['{}_diff'.format(col)], ascending=False).reset_index(drop=True)

                # only do translation when diff is higher than mean + 2 * std
                outliers_bound = df['{}_diff'.format(col)].mean() + 2 * df['{}_diff'.format(col)].std()

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

            positions = df[columns].values

        scale = 500 + np.sqrt(N) * 100
        positions[:, 0] = rescale_positions(positions[:, 0], scale=scale * scale_ratio)  # x-axis
        positions[:, 1] = rescale_positions(positions[:, 1], scale=scale)  # y-axis

        return positions

    def compute_layout(self, scale_ratio=1):
        logging.info("Computing layout ...")
        start = time.time()

        iGraph, id_to_node = self._create_igraph()

        positions = np.array(iGraph.layout_fruchterman_reingold(grid=False))

        positions = self._transform_positions(positions, scale_ratio=scale_ratio, remove_empty_zones=200)

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

        # src_col, tgt_col = self.source_nodes_color, self.target_nodes_color
        # self.numerical_color = False
        # if src_col and tgt_col:
        #     if df[src_col].dtype in [np.dtype(float)] and df[tgt_col].dtype in [np.dtype(float)]:
        #         self.numerical_color = True
        # elif src_col and df[src_col].dtype in [np.dtype(float)]:
        #     self.numerical_color = True
        # elif tgt_col and df[tgt_col].dtype in [np.dtype(float)]:
        #     self.numerical_color = True

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
        # if self.numerical_color and len(self.group_values) > 10:  # no color palette with only few numbers
        if self.numerical_colors:
            mini, maxi = min(self.group_values), max(self.group_values)
            for group in self.group_values:
                x = (maxi - group)/(maxi - mini) * 225  # would be white if 255
                self.groups[group] = {'color': "rgba(255, {0}, {0}, 1)".format(x)}
        else:
            for group in self.group_values:
                if group != "nogroup":
                    color = list(np.random.choice(range(50, 200), size=3))
                    self.groups[group] = {'color': "rgba({}, {}, {}, 1)".format(color[0], color[1], color[2])}
