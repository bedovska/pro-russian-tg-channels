import pickle

import networkx as nx
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from tqdm.cli import tqdm
from fire import Fire

import warnings
warnings.filterwarnings("ignore", category=FutureWarning) 
warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning) 


def load_done(folder):
    print("Load channels done")
    short_names = [fn.stem for fn in folder.glob("*.csv")]
    done = [f"https://t.me/{sn}" for sn in short_names]
    return done

def get_forwards(messages, min_forwards):
    forwards_with_count = messages["forward_from"].value_counts()
    forwards = forwards_with_count.index[forwards_with_count.values >= min_forwards].tolist()
    return forwards

def load_waitlist(folder, min_forwards):
    print("Load channels in waitlist (aka forwarded)")
    waitlist = []
    for fn in folder.glob("*.csv"):
        forwards = get_forwards(pd.read_csv(fn), min_forwards)
        forwards = [f for f in forwards if f not in waitlist]
        waitlist += forwards
    return waitlist


def create_graph(messages_folder, stats_filename, graph_filename):
    print(graph_filename)
    if graph_filename.exists():
        with open(graph_filename, "rb") as f:
            g = pickle.load(f)
    else:
        channels_done = load_done(messages_folder)
        channels_waitlist = load_waitlist(messages_folder, 1)

        channels = list(set(channels_done) | set(channels_waitlist))
        channels_amount = len(channels)
        print(f"Overall number of channels (both downloaded and forwarded): {channels_amount}")

        adjacency = []
        for _ in range(channels_amount):
            s = []
            for _ in range(channels_amount):
                s.append(0)
            adjacency.append(s)

        # Write down how many times any channel forwarded another channel
        for channel in tqdm(channels_done, desc="build adjacency matrix"):
            file_name = channel.replace("https://t.me/", str(messages_folder) + "/") + ".csv"
            b = pd.read_csv(file_name)
            kilkist = b["forward_from"].value_counts()
            index = channels.index(channel)


            for forward_channel_name, forward_amount in zip(
                    kilkist.index.tolist(),
                    kilkist.values.tolist()
            ):
                forward_channel_index = channels.index(forward_channel_name)
                adjacency[index][forward_channel_index] = forward_amount


        g = nx.DiGraph(np.array(adjacency))


        # TODO check if stats file constains information for all channels
        stats_df = pd.read_csv(stats_filename)
        stats_df["id"] = stats_df["id"].fillna(0).astype(int)
        stats_df = stats_df.rename(columns={"id": "tg_id"})

        channels_with_stats = stats_df["username"].tolist()

        nodes_attr = {}
        for node_idx in tqdm(range(channels_amount), "add node attributes"):
            node_link = channels[node_idx]
            node_username = node_link.replace("https://t.me/", "")
            is_downloaded = node_username in channels_done
            has_stats = node_username in channels_with_stats

            node_attr = {
                "link": node_link,
                "username": node_username,
                "is_downloaded": is_downloaded,
                "has_stats": has_stats,
            }

            if has_stats:
                node_stats = stats_df[stats_df["username"] == node_username].iloc[0].to_dict()
                del node_stats["username"]

                node_attr = {
                    **node_attr,
                    **node_stats,
                }

            nodes_attr[node_idx] = node_attr

        nx.set_node_attributes(g, nodes_attr)

        # Rename node from idx to username
        # mapping = {i: channels[i].replace("https://t.me/", "") for i in range(len(channels))}
        # g = nx.relabel_nodes(g, mapping)

        with open(graph_filename, 'wb') as f:
            pickle.dump(g, f)
    return g


def graph_to_geojson(g: nx.DiGraph, output_filename: str) -> None:
    import math
    import geopandas as gpd
    from shapely.geometry import Point, LineString

    for u, v, d in g.edges(data=True):
        # log_weight = math.log(d["weight"], 1.1)
        log_weight = np.log(d["weight"])
        # nx.set_edge_attributes(g, {(u, v): {"log_weight": (log_weight) / d["weight"]}})
        # nx.set_edge_attributes(g, {(u, v): {"log_weight": (log_weight ** 2) / d["weight"]}})
        nx.set_edge_attributes(g, {(u, v): {"log_weight": log_weight / (d["weight"] ** 1.5)}})
    pos = nx.kamada_kawai_layout(g, weight="log_weight")

    graph_gdf_items = []
    for u, d in g.nodes(data=True):
        graph_gdf_items.append({
            **d,
            "geometry": Point(*pos[u])
        })

    for u, v, d in g.edges(data=True):
        graph_gdf_items.append({
            **d,
            "geometry": LineString([pos[u], pos[v]])
        })
    graph_gdf = gpd.GeoDataFrame(graph_gdf_items)
    print(type(graph_gdf))
    graph_gdf.to_file(output_filename, driver="GeoJSON")


def filter_graph(g: nx.DiGraph, min_connections: int) -> nx.DiGraph:
    none_nodes = [n_idx for n_idx, n_data in g.nodes(data=True) if n_data["username"] == "None"]
    # Check if None node is actually exists
    if len(none_nodes) >= 1:
        none_node = none_nodes[0]
        none_edges = list(g.in_edges(none_node))
        g.remove_edges_from(none_edges)
        g.remove_node(none_node)


    edges_to_remove = [nodes for nodes in g.edges() \
                       if g.get_edge_data(*nodes)["weight"] <= min_connections]
    g.remove_edges_from(edges_to_remove)
    nodes_to_remove = [n for n in g.nodes if g.degree(n) == 0]
    g.remove_nodes_from(nodes_to_remove)

    return g


def main(
    messages_folder: str,
    stats_filename: str,

    graph_filename: str,
) -> None:
    messages_folder = Path(messages_folder)
    stats_filename = Path(stats_filename)
    graph_filename = Path(graph_filename)

    g = create_graph(messages_folder, stats_filename, graph_filename)
    print(g)

    g = filter_graph(g, 50)
    print(g)

    # from netxd3 import simpleNetworkx
    # print(simpleNetworkx(g))

    # edgewidth = [len(g.get_edge_data(u, v)) for u, v in g.edges()]
    # pos = nx.kamada_kawai_layout(g)
    # fig, ax = plt.subplots(figsize=(30, 30))
    # nx.draw_networkx_edges(g, pos, alpha=0.3, width=edgewidth, edge_color="m")
    # nx.draw_networkx_nodes(g, pos, node_color="#210070", alpha=0.9)
    # nx.draw_networkx_labels(g, pos, font_size=14)
    # ax.margins(0.1, 0.05)
    # fig.tight_layout()
    # plt.axis("off")
    # # plt.show()

    # plt.savefig("test.png", bbox_inches="tight")

    # print(list(g.edges())[0])

    # import matplotlib.pyplot as plt
    # plt.show()

    # folder = Path("data/channels-downloaded-2023-04-30-14/")
    # all_csv = list(folder.glob("*.csv"))
    # # print(all_csv)

    # G = nx.Graph()
    # G.add_node(0) # Adds one node
    # G.add_nodes_from([4, 1, 2]) # Adds many nodes

    # G.add_edge(0, 1) # Adds one edge 
    # G.add_edges_from([(0, 2), (1, 2)]) # Adds list of edges

    # print( G.number_of_nodes(), G.number_of_edges() )
    # nx.draw(G)

    # plt.show()


if __name__ == "__main__":
    Fire(main)
