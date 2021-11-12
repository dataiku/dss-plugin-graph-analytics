from graph_analytics_constants import Constants
import logging


CLUSTERING_ALGORITHMS = {
    Constants.FASTGREEDY: {
        'method': ('community_fastgreedy', {'weights': 'weight'}),
        'label': 'fastgreedy',
        'param_restriction': 'directed_graph'
    },
    Constants.MULTILEVEL: {
        'method': ('community_multilevel', {'weights': 'weight'}),
        'label': 'multilevel',
        'param_restriction': 'directed_graph'
    },
    Constants.INFOMAP: {
        'method': ('community_infomap', {'edge_weights': 'weight', 'trials': 10}),
        'label': 'infomap'
    },
    Constants.WALKTRAP: {
        'method': ('community_walktrap', {'weights': 'weight', 'steps': 10}),
        'label': 'walktrap'
    }
}


def fix_dendrogram(graph, dendogram):
    """ merge disconnected sub-dendograms 'randomly' """

    already_merged = set()
    for merge in dendogram.merges:
        already_merged.update(merge)

    logging.info("Fixing dendogram")

    num_dendrogram_nodes = graph.vcount() + len(dendogram.merges)
    not_merged_yet = sorted(set(range(num_dendrogram_nodes)) - already_merged)
    if len(not_merged_yet) < 2:
        return

    v1, v2 = not_merged_yet[:2]
    dendogram._merges.append((v1, v2))
    del not_merged_yet[:2]

    missing_nodes = range(num_dendrogram_nodes, num_dendrogram_nodes + len(not_merged_yet))
    dendogram._merges.extend(zip(not_merged_yet, missing_nodes))
    dendogram._nmerges = graph.vcount()-1
