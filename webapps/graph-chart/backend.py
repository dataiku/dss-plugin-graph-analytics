import dataiku
from flask import request
import pandas as pd
import json
import traceback
import logging
from functools import reduce
import time

logger = logging.getLogger(__name__)


def numerical_filter(df, filter):
    conditions = []
    if filter["minValue"]:
        conditions += [df[filter['column']] >= filter['minValue']]
    if filter["maxValue"]:
        conditions += [df[filter['column']] <= filter['maxValue']]
    return conditions


def alphanum_filter(df, filter):
    conditions = []
    excluded_values = []
    for k, v in filter['excludedValues'].items():
        if k != '___dku_no_value___':
            if v:
                excluded_values += [k]
        else:
            if v:
                conditions += [~df[filter['column']].isnull()]
    if len(excluded_values) > 0:
        if filter['columnType'] == 'NUMERICAL':
            excluded_values = [float(x) for x in excluded_values]
        conditions += [~df[filter['column']].isin(excluded_values)]
    return conditions


def date_filter(df, filter):
    if filter["dateFilterType"] == "RANGE":
        return date_range_filter(df, filter)
    else:
        return special_date_filter(df, filter)


def date_range_filter(df, filter):
    conditions = []
    if filter["minValue"]:
        conditions += [df[filter['column']] >= pd.Timestamp(filter['minValue'], unit='ms')]
    if filter["maxValue"]:
        conditions += [df[filter['column']] <= pd.Timestamp(filter['maxValue'], unit='ms')]
    return conditions


def special_date_filter(df, filter):
    conditions = []
    excluded_values = []
    for k, v in filter['excludedValues'].items():
        if v:
            excluded_values += [k]
    if len(excluded_values) > 0:
        if filter["dateFilterType"] == "YEAR":
            conditions += [~df[filter['column']].dt.year.isin(excluded_values)]
        elif filter["dateFilterType"] == "QUARTER_OF_YEAR":
            conditions += [~df[filter['column']].dt.quarter.isin([int(k)+1 for k in excluded_values])]
        elif filter["dateFilterType"] == "MONTH_OF_YEAR":
            conditions += [~df[filter['column']].dt.month.isin([int(k)+1 for k in excluded_values])]
        elif filter["dateFilterType"] == "WEEK_OF_YEAR":
            conditions += [~df[filter['column']].dt.week.isin([int(k)+1 for k in excluded_values])]
        elif filter["dateFilterType"] == "DAY_OF_MONTH":
            conditions += [~df[filter['column']].dt.day.isin([int(k)+1 for k in excluded_values])]
        elif filter["dateFilterType"] == "DAY_OF_WEEK":
            conditions += [~df[filter['column']].dt.dayofweek.isin(excluded_values)]
        elif filter["dateFilterType"] == "HOUR_OF_DAY":
            conditions += [~df[filter['column']].dt.hour.isin(excluded_values)]
        else:
            raise Exception("Unknown date filter.")

    return conditions


def apply_filter_conditions(df, conditions):
    """
    return a function to apply filtering conditions on df
    """
    if len(conditions) == 0:
        return df
    elif len(conditions) == 1:
        return df[conditions[0]]
    else:
        return df[reduce(lambda c1, c2: c1 & c2, conditions[1:], conditions[0])]


def filter_dataframe(df, filters):
    """
    return the input dataframe df with filters applied to it
    """
    for filter in filters:
        try:
            if filter["filterType"] == "NUMERICAL_FACET":
                df = apply_filter_conditions(df, numerical_filter(df, filter))
            elif filter["filterType"] == "ALPHANUM_FACET":
                df = apply_filter_conditions(df, alphanum_filter(df, filter))
            elif filter["filterType"] == "DATE_FACET":
                df = apply_filter_conditions(df, date_filter(df, filter))
        except Exception as e:
            raise Exception("Error with filter on column {} - {}".format(filter["column"], e))
    if df.empty:
        raise Exception("Dataframe is empty after filtering")
    return df


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

    def create_graph(self, df):
        logger.info("Creating graph object ...")
        start = time.time()
        nodes_set, nodes_nb = set(), 0
        nodes, edges = [], []
        for idx, row in df.iterrows():
            if nodes_nb > self.max_nodes:
                break
            if row[self.source] not in nodes_set:
                nodes.append(self.create_source_node(row))
                nodes_set.add(row[self.source])
                nodes_nb += 1
            if row[self.target] not in nodes_set:
                nodes.append(self.create_target_node(row))
                nodes_set.add(row[self.target])
                nodes_nb += 1
            edges.append(self.create_edge(row))

        self.nodes = nodes
        self.edges = edges
        logger.info("Graph object created in {:.4f} seconds".format(time.time()-start))

    def create_source_node(self, row):
        node = {}
        node['id'] = row[self.source]
        node['label'] = row[self.source]
        title = "{}: {}".format(self.source, row[self.source])
        if self.source_nodes_color:
            node['group'] = row[self.source_nodes_color]
            title += "<br>{}: {}".format(self.source_nodes_color, row[self.source_nodes_color])
        if self.source_nodes_size:
            node['value'] = row[self.source_nodes_size]
            title += "<br>{}: {}".format(self.source_nodes_size, row[self.source_nodes_size])
        node['title'] = title
        return node

    def create_target_node(self, row):
        node = {}
        node['id'] = row[self.target]
        node['label'] = row[self.target]
        title = "{}: {}".format(self.target, row[self.target])
        if self.target_nodes_color:
            node['group'] = row[self.target_nodes_color]
            title += "<br>{}: {}".format(self.target_nodes_color, row[self.target_nodes_color])
        if self.target_nodes_size:
            node['value'] = row[self.target_nodes_size]
            title += "<br>{}: {}".format(self.target_nodes_size, row[self.target_nodes_size])
        node['title'] = title
        return node

    def create_edge(self, row):
        edge = {}
        edge['from'] = row[self.source]
        edge['to'] = row[self.target]
        title = "{} -> {}".format(row[self.source], row[self.target])
        if self.edges_caption:
            edge['label'] = row[self.edges_caption]
            title += "<br>{}: {}".format(self.edges_caption, row[self.edges_caption])
        if self.edges_width:
            edge['value'] = row[self.edges_width]
            title += "<br>{}: {}".format(self.edges_width, row[self.edges_width])
        edge['title'] = title
        return edge


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
