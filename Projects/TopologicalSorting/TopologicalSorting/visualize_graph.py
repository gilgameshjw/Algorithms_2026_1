import networkx as nx
import matplotlib.pyplot as plt


def draw_graph(graph, limit=50):

    G = nx.DiGraph()

    count = 0

    for u in graph:
        for v in graph[u]:
            G.add_edge(u, v)
            count += 1

            if count > limit:
                break
        if count > limit:
            break

    plt.figure(figsize=(10, 8))

    pos = nx.spring_layout(G)

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=1200,
        node_color="lightblue",
        font_size=8,
        arrows=True
    )

    plt.title("Graph Visualisation (Partial Dataset)")

    plt.show()
def draw_topological_order(order, limit=30):

    import networkx as nx
    import matplotlib.pyplot as plt

    G = nx.DiGraph()

    nodes = order[:limit]

    for i in range(len(nodes) - 1):
        G.add_edge(nodes[i], nodes[i + 1])

    plt.figure(figsize=(12, 6))

    pos = nx.spring_layout(G)

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=1200,
        node_color="lightgreen",
        font_size=8,
        arrows=True
    )

    plt.title("Topological Order Path")

    plt.show()