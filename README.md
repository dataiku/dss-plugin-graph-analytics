# Dataiku Graph Analytics Plugin

Version: 1.0.1<br>
Compatible with DSS version: 8.0.2 and higher<br>

## Overview

This plugin offers three recipes and one custom chart to create graphs and compute graph algorithms:


* **Projected graph**: for example, create a graph of Product (dataset of Product pairs) from a dataset of Product - Customer pairs where 2 products are linked if they share a same customer.
* **Graph features**: from a dataset of edges (Source - Target pairs), compute some graph algorithms to get node features such as degree, closeness centrality, pagerank, ... . It can output either a dataset of edges with the new source and target graph features in each row, or output a dataset of nodes and their corresponding new graph features.
* **Graph clustering**: from a dataset of edges, compute some graph clustering algorithms and assign nodes to their cluster Id. Same as the Graph features recipe, it can output a dataset of edges or nodes with their newly computed clusters Id.

This plugin also provides a custom chart to visualize your graph:
* You can specify the maximum number of nodes you want to display in the chart.
* You can filter nodes based on some column conditions.
* You can select some columns:
    * to color nodes (nodes with same column value will have the same color)
    * for node sizes (node sizes will depend on the column value)
    * for edge widths and label
* When double-clicking on a node, itself and its first-degree neighbor will be highligthed.
