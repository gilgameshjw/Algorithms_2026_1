from dataset_loader import load_graph
from topo_sort import topological_sort
from visualize_graph import draw_graph, draw_topological_order

from scc import kosaraju_scc
from compress import compress_graph


def has_real_cycle(sccs):
    """
    判断是否存在真正的 cycle
    （SCC里有多个节点才算）
    """
    for comp in sccs:
        if len(comp) > 1:
            return True
    return False


def main():

    # load dataset
    graph = load_graph("dataset.txt")

    print("Number of nodes:", len(graph))

    # draw original graph（可以关掉加快速度）
    draw_graph(graph)

    # -------------------------------
    # STEP 1: 尝试拓扑排序
    # -------------------------------
    order = topological_sort(graph)

    if order is not None:
        print("\nTopological Sorted List (Original Graph):")
        for i, node in enumerate(order[:50], 1):  # 只显示前50个，避免太长
            print(i, "-", node)

        draw_topological_order(order)

    else:
        print("\nCycle detected in original graph!")

    # -------------------------------
    # STEP 2: 一定执行 SCC（关键🔥）
    # -------------------------------
    print("\nRunning SCC (Kosaraju)...")

    sccs = kosaraju_scc(graph)

    print("\nStrongly Connected Components:")
    for i, comp in enumerate(sccs[:20], 1):  # 只显示前20个
        print(f"SCC {i}:", comp)

    # -------------------------------
    # STEP 3: 判断是否真的有环
    # -------------------------------
    if has_real_cycle(sccs):
        print("\nReal cycles detected (SCC with multiple nodes).")
    else:
        print("\nGraph is almost DAG (no large cycles).")

    # -------------------------------
    # STEP 4: 压缩图（无论如何都做🔥）
    # -------------------------------
    new_graph = compress_graph(graph, sccs)

    print("\nCompressed Graph (first 20 nodes):")
    for i, (k, v) in enumerate(new_graph.items()):
        if i > 20:
            break
        print(k, "->", v)

    # -------------------------------
    # STEP 5: 在压缩图上做拓扑排序
    # -------------------------------
    new_order = topological_sort(new_graph)

    print("\nTopological Order (SCC Graph):")
    for i, node in enumerate(new_order[:30], 1):
        print(i, "-", f"SCC {node}")

    print("\nDone!")


if __name__ == "__main__":
    main()