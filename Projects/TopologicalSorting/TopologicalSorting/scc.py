def kosaraju_scc(graph):
    visited = set()
    stack = []

    # Step 1: fill order
    def dfs(u):
        visited.add(u)
        for v in graph[u]:
            if v not in visited:
                dfs(v)
        stack.append(u)

    for node in graph:
        if node not in visited:
            dfs(node)

    # Step 2: reverse graph
    reversed_graph = {u: [] for u in graph}
    for u in graph:
        for v in graph[u]:
            reversed_graph[v].append(u)

    # Step 3: DFS on reversed graph
    visited.clear()
    sccs = []

    def dfs_reverse(u, component):
        visited.add(u)
        component.append(u)
        for v in reversed_graph[u]:
            if v not in visited:
                dfs_reverse(v, component)

    while stack:
        node = stack.pop()
        if node not in visited:
            component = []
            dfs_reverse(node, component)
            sccs.append(component)

    return sccs