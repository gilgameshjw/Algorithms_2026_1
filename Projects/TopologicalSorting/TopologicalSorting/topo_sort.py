from collections import deque

def topological_sort(graph):

    indegree = {u: 0 for u in graph}

    for u in graph:
        for v in graph[u]:
            indegree[v] += 1

    queue = deque([u for u in graph if indegree[u] == 0])

    order = []

    while queue:

        u = queue.popleft()
        order.append(u)

        for v in graph[u]:

            indegree[v] -= 1

            if indegree[v] == 0:
                queue.append(v)

    # cycle detection
    if len(order) != len(graph):
        print("Cycle detected in the graph!")
        return None

    return order