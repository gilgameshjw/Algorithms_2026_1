def compress_graph(graph, sccs):
    # 每个节点属于哪个 SCC
    node_to_scc = {}
    for i, comp in enumerate(sccs):
        for node in comp:
            node_to_scc[node] = i

    # 新图
    new_graph = {i: [] for i in range(len(sccs))}

    for u in graph:
        for v in graph[u]:
            if node_to_scc[u] != node_to_scc[v]:
                new_graph[node_to_scc[u]].append(node_to_scc[v])

    return new_graph