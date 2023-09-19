import pickle

import networkx as nx
import simplejson as json

from pathlib import Path
from fire import Fire
from typing import Optional, List


def load_graph(graph_filename: Path) -> nx.DiGraph:
    assert graph_filename.exists(), f"Graph {graph_filename} does not exists, " \
                                    f"run build_graph.py script first"

    with open(graph_filename, "rb") as f:
        g = pickle.load(f)
    return g

def filter_graph(
    g: nx.DiGraph,
    min_connections: int,
    langs_to_use: Optional[List[str]],
    only_downloaded: bool,
) -> nx.DiGraph:
    none_nodes = [n_idx for n_idx, n_data in g.nodes(data=True) if n_data["username"] == "None"]
    # Check if None node is actually exists
    if len(none_nodes) >= 1:
        none_node = none_nodes[0]
        none_edges = list(g.in_edges(none_node))
        g.remove_edges_from(none_edges)
        g.remove_node(none_node)


    # Remove self forwards
    g.remove_edges_from(nx.selfloop_edges(g, data=True))


    if langs_to_use is not None:
        # langs = {}
        # for i, d in g.nodes(data=True):
        #     if "language_full" in d:
        #         if d["language_full"] in langs:
        #             langs[d["language_full"]] += 1
        #         else:
        #             langs[d["language_full"]] = 1

        # print(langs)
        # exit(0)
        # print(g)
        print(f"Languages to use: {langs_to_use}")
        nodes_to_remove = [
            n_idx for n_idx, n_data in g.nodes(data=True)
            if ("language_full" in n_data) and (n_data["language_full"] not in langs_to_use)
        ]
        # Remove nodes and edges from langs that are not listed
        g.remove_nodes_from(nodes_to_remove)
        # Remove nodes without edges
        nodes_to_remove = [n for n in g.nodes if g.degree(n) == 0]
        g.remove_nodes_from(nodes_to_remove)

    if only_downloaded:
        nodes_to_remove = [
            n_idx for n_idx, n_data in g.nodes(data=True)
            if not n_data["has_stats"]
        ]
        g.remove_nodes_from(nodes_to_remove)


    # Remove edges with low connections
    edges_to_remove = [nodes for nodes in g.edges() \
                       if g.get_edge_data(*nodes)["weight"] <= min_connections]
    g.remove_edges_from(edges_to_remove)
    nodes_to_remove = [n for n in g.nodes if g.degree(n) == 0]
    g.remove_nodes_from(nodes_to_remove)

    return g



def main(
    graph_filename: str,
    output_filename: str,

    min_connections: int = 50,
    langs_to_use: Optional[List[str]] = ["Russian", "Italian", "English"],
    only_downloaded: bool = False,
):
    graph_filename = Path(graph_filename)
    output_filename = Path(output_filename)

    g = load_graph(graph_filename)
    # for n, d in g.nodes(data=True):
    #     print(g.in_edges(n), g.out_edges(n), n)
    # exit(0)
    # print(g)
    g = filter_graph(g, min_connections, langs_to_use, only_downloaded)
    print(g)
    # print([(g.in_edges(n), g.out_edges(n), n)
    #        for n, d in g.nodes(data=True) if d["username"] == "nuce_ciwan_ENG"])
    # print([(g.edges(n), n) for n, d in g.nodes(data=True) if d["username"] == "BritainFirst"])
    # print([n for n in g.nodes if g.degree(n) == 0])

    nodes = [
        {
            "id": node_idx,
            **node_data,
        }
        for node_idx, node_data in g.nodes(data=True)
    ]

    links = [
        {
            "source": node_from,
            "target": node_to,
            **edge_data,
        }
        for node_from, node_to, edge_data in g.edges(data=True)
    ]

    graph_dict = { "nodes": nodes, "links": links }

    with open(output_filename, "w") as json_file:
        json.dump(graph_dict, json_file, indent=4, ignore_nan=True)


if __name__ == "__main__":
    Fire(main)
