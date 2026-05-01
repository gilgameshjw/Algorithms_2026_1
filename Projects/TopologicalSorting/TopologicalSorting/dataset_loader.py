def load_graph(filename):

    graph = {}
    count = 0
    limit = 5000   # only read first 5000 edges

    with open(filename, "r") as f:
        for line in f:

            if line.startswith("#"):
                continue

            parts = line.strip().split()

            if len(parts) != 2:
                continue

            u, v = parts

            if u not in graph:
                graph[u] = []

            graph[u].append(v)

            if v not in graph:
                graph[v] = []

            count += 1

            if count >= limit:
                break

    return graph