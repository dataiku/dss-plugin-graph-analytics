import networkx as nx
from dku_constants import Constants


GRAPH_ALGORITHMS = {
    Constants.EIGEN_CENTRALITY: {
        "method": (nx.eigenvector_centrality_numpy, {}),
        "label": "eigenvector_centrality"
    },
    Constants.CLUSTERING: {
        "method": (nx.clustering, {}),
        "label": "clustering_coefficient",
    },
    Constants.TRIANGLES: {
        "method": (nx.triangles, {}),
        "label": "triangles",
        "param_restriction": "directed_graph"
    },
    Constants.CLOSENESS: {
        "method": (nx.closeness_centrality, {}),
        "label": "closeness_centrality"
    },
    Constants.PAGERANK: {
        "method": (nx.pagerank, {}),
        "label": "pagerank"
    },
    Constants.SQ_CLUSTERING: {
        "method": (nx.square_clustering, {}),
        "label": "square_clustering_coefficient"
    }
}
