import osmnx as ox
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
import collections
import os
import heapq
import math

# 解决中文显示为方块的问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 第一部分：下载北京中关村路网
# ============================================================
print("正在下载路网，请稍等（第一次需要联网，约1-2分钟）...")
G = ox.graph_from_place("Zhongguancun, Haidian, Beijing, China", network_type="drive")
print(f"路网下载完成！节点数：{G.number_of_nodes()}，边数：{G.number_of_edges()}")

# ============================================================
# 第二部分：从6666个文件中收集所有有效轨迹
# ============================================================
tdrive_folder = "tdrive"


txt_files = sorted([f for f in os.listdir(tdrive_folder) if f.endswith('.txt')])
print(f"\n找到 {len(txt_files)} 个轨迹文件")
print("正在筛选有效轨迹（起点≠终点），请稍等...")

# 收集所有有效的起终点对
valid_trajectories = []  # 每项: (start_node, end_node, filename, straight_line_dist)

for idx, txt_file in enumerate(txt_files):
    if (idx + 1) % 500 == 0:
        print(f"  已检查 {idx + 1}/{len(txt_files)} 个文件，已找到 {len(valid_trajectories)} 个有效轨迹")

    filepath = os.path.join(tdrive_folder, txt_file)
    try:
        df = pd.read_csv(filepath, header=None, names=["id", "time", "lon", "lat"])
        df = df.head(10)
        if len(df) < 2:
            continue

        nodes = []
        for i, row in df.iterrows():
            node = ox.nearest_nodes(G, row["lon"], row["lat"])
            nodes.append(node)

        s = nodes[0]
        e = nodes[-1]

        if s != e and nx.has_path(G, s, e):
            # 计算起终点直线距离（用于分组）
            lat1, lon1 = G.nodes[s]['y'], G.nodes[s]['x']
            lat2, lon2 = G.nodes[e]['y'], G.nodes[e]['x']
            R = 6371000
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlam = math.radians(lon2 - lon1)
            a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
            dist = 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            if dist > 100:  # 过滤掉距离太近的（<100m）
                valid_trajectories.append((s, e, txt_file, dist))
    except:
        continue

print(f"\n筛选完成！共找到 {len(valid_trajectories)} 个有效轨迹")

if len(valid_trajectories) == 0:
    print("错误：没有找到有效轨迹，无法运行。")
    exit()


# ============================================================
# 第三部分：四个算法定义
# ============================================================

def haversine(u, v):
    """计算路网节点 u 到 v 的直线距离（米），作为 A* 的 h(n)"""
    lat1, lon1 = G.nodes[u]['y'], G.nodes[u]['x']
    lat2, lon2 = G.nodes[v]['y'], G.nodes[v]['x']
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# --- 算法1：A*（f(n) = g(n) + h(n)，启发函数为直线距离）---
def run_astar(G, start, end):
    t0 = time.time()
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {start: None}
    g_score = {start: 0}
    visited_count = 0

    while open_set:
        _, current = heapq.heappop(open_set)
        visited_count += 1
        if current == end:
            path = []
            node = end
            while node is not None:
                path.append(node)
                node = came_from[node]
            path.reverse()
            t1 = time.time()
            length = nx.path_weight(G, path, weight="length")
            return path, length, round((t1 - t0) * 1000, 2), visited_count
        for neighbor in G.neighbors(current):
            edge_len = G.edges[current, neighbor, 0].get("length", 1)
            tentative_g = g_score[current] + edge_len
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                f = tentative_g + haversine(neighbor, end)
                heapq.heappush(open_set, (f, neighbor))
                came_from[neighbor] = current
    t1 = time.time()
    return None, -1, round((t1 - t0) * 1000, 2), visited_count


# --- 算法2：Dijkstra（f(n) = g(n) + 0，A* 去掉启发函数）---
def run_dijkstra(G, start, end):
    t0 = time.time()
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {start: None}
    g_score = {start: 0}
    visited_count = 0

    while open_set:
        _, current = heapq.heappop(open_set)
        visited_count += 1
        if current == end:
            path = []
            node = end
            while node is not None:
                path.append(node)
                node = came_from[node]
            path.reverse()
            t1 = time.time()
            length = nx.path_weight(G, path, weight="length")
            return path, length, round((t1 - t0) * 1000, 2), visited_count
        for neighbor in G.neighbors(current):
            edge_len = G.edges[current, neighbor, 0].get("length", 1)
            tentative_g = g_score[current] + edge_len
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                f = tentative_g + 0  # 没有启发函数，就是 Dijkstra
                heapq.heappush(open_set, (f, neighbor))
                came_from[neighbor] = current
    t1 = time.time()
    return None, -1, round((t1 - t0) * 1000, 2), visited_count


# --- 算法3：BFS（队列迭代）---
def run_bfs(G, start, end):
    t0 = time.time()
    visited = set()
    queue = collections.deque()
    queue.append(start)
    visited.add(start)
    parent = {start: None}
    found = False
    while queue:
        current = queue.popleft()
        if current == end:
            found = True
            break
        for neighbor in G.neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)
    t1 = time.time()
    if not found:
        return None, -1, round((t1 - t0) * 1000, 2), len(visited)
    path = []
    node = end
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    length = nx.path_weight(G, path, weight="length")
    return path, length, round((t1 - t0) * 1000, 2), len(visited)


# --- 算法4：DFS（显式栈迭代）---
def run_dfs(G, start, end):
    t0 = time.time()
    visited = set()
    stack = [start]
    parent = {start: None}
    found = False
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        if current == end:
            found = True
            break
        for neighbor in G.neighbors(current):
            if neighbor not in visited:
                parent[neighbor] = current
                stack.append(neighbor)
    t1 = time.time()
    if not found:
        return None, -1, round((t1 - t0) * 1000, 2), len(visited)
    path = []
    node = end
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    length = nx.path_weight(G, path, weight="length")
    return path, length, round((t1 - t0) * 1000, 2), len(visited)


# ============================================================
# 第四部分：对所有有效轨迹运行四种算法
# ============================================================
print(f"\n正在对 {len(valid_trajectories)} 个有效轨迹运行四种算法...")
print("这可能需要几分钟，请耐心等待...\n")

results = []  # 存所有实验结果
example_paths = None  # 保存一组典型轨迹的路径（用于可视化）

for idx, (start, end, filename, straight_dist) in enumerate(valid_trajectories):
    if (idx + 1) % 10 == 0 or idx == 0:
        print(f"  正在处理第 {idx + 1}/{len(valid_trajectories)} 个轨迹...")

    row = {"file": filename, "straight_dist": straight_dist}

    # A*
    p_a, l_a, t_a, v_a = run_astar(G, start, end)
    row["astar_len"] = l_a
    row["astar_time"] = t_a
    row["astar_visited"] = v_a

    # Dijkstra
    p_d, l_d, t_d, v_d = run_dijkstra(G, start, end)
    row["dijkstra_len"] = l_d
    row["dijkstra_time"] = t_d
    row["dijkstra_visited"] = v_d

    # BFS
    p_b, l_b, t_b, v_b = run_bfs(G, start, end)
    row["bfs_len"] = l_b
    row["bfs_time"] = t_b
    row["bfs_visited"] = v_b

    # DFS
    p_f, l_f, t_f, v_f = run_dfs(G, start, end)
    row["dfs_len"] = l_f
    row["dfs_time"] = t_f
    row["dfs_visited"] = v_f

    # 路径质量比（相对于 A* 的路径长度）
    if l_a > 0:
        row["dijkstra_ratio"] = l_d / l_a if l_d > 0 else -1
        row["bfs_ratio"] = l_b / l_a if l_b > 0 else -1
        row["dfs_ratio"] = l_f / l_a if l_f > 0 else -1
    else:
        row["dijkstra_ratio"] = -1
        row["bfs_ratio"] = -1
        row["dfs_ratio"] = -1

    results.append(row)

    # 保存一组中等距离的典型轨迹用于可视化
    if example_paths is None and 1000 < straight_dist < 3000 and p_a and p_d and p_b and p_f:
        example_paths = {
            "start": start, "end": end, "file": filename,
            "astar": p_a, "dijkstra": p_d, "bfs": p_b, "dfs": p_f,
            "astar_len": l_a, "dijkstra_len": l_d, "bfs_len": l_b, "dfs_len": l_f,
        }

# 如果没找到中等距离的，用第一组有效的
if example_paths is None:
    for idx, (start, end, filename, straight_dist) in enumerate(valid_trajectories):
        p_a, l_a, _, _ = run_astar(G, start, end)
        p_d, l_d, _, _ = run_dijkstra(G, start, end)
        p_b, l_b, _, _ = run_bfs(G, start, end)
        p_f, l_f, _, _ = run_dfs(G, start, end)
        if p_a and p_d and p_b and p_f:
            example_paths = {
                "start": start, "end": end, "file": filename,
                "astar": p_a, "dijkstra": p_d, "bfs": p_b, "dfs": p_f,
                "astar_len": l_a, "dijkstra_len": l_d, "bfs_len": l_b, "dfs_len": l_f,
            }
            break

print(f"\n四种算法全部运行完成！共处理 {len(results)} 个轨迹")

# 转为 DataFrame 方便统计
df_results = pd.DataFrame(results)
# 过滤掉任何算法失败的行
df_valid = df_results[(df_results["astar_len"] > 0) & (df_results["dijkstra_len"] > 0) &
                      (df_results["bfs_len"] > 0) & (df_results["dfs_len"] > 0)].copy()
print(f"四种算法都成功的轨迹数：{len(df_valid)} 个")


# ============================================================
# 第五部分：打印汇总结果
# ============================================================

# --- 表1：总体平均值 ---
print("\n" + "=" * 80)
print("                    算法对比汇总（所有有效轨迹平均值）")
print("=" * 80)
print(f"  {'算法':<12} {'平均路径长度(m)':<18} {'平均访问节点数':<16} {'平均耗时(ms)':<14} {'路径质量比'}")
print("-" * 80)

avg_a_len = df_valid["astar_len"].mean()
avg_a_vis = df_valid["astar_visited"].mean()
avg_a_time = df_valid["astar_time"].mean()

avg_d_len = df_valid["dijkstra_len"].mean()
avg_d_vis = df_valid["dijkstra_visited"].mean()
avg_d_time = df_valid["dijkstra_time"].mean()
avg_d_ratio = df_valid["dijkstra_ratio"].mean()

avg_b_len = df_valid["bfs_len"].mean()
avg_b_vis = df_valid["bfs_visited"].mean()
avg_b_time = df_valid["bfs_time"].mean()
avg_b_ratio = df_valid["bfs_ratio"].mean()

avg_f_len = df_valid["dfs_len"].mean()
avg_f_vis = df_valid["dfs_visited"].mean()
avg_f_time = df_valid["dfs_time"].mean()
avg_f_ratio = df_valid["dfs_ratio"].mean()

print(f"  {'A*':<12} {avg_a_len:<18.1f} {avg_a_vis:<16.1f} {avg_a_time:<14.2f} {'1.00 (基准)'}")
print(f"  {'Dijkstra':<12} {avg_d_len:<18.1f} {avg_d_vis:<16.1f} {avg_d_time:<14.2f} {avg_d_ratio:.2f}")
print(f"  {'BFS':<12} {avg_b_len:<18.1f} {avg_b_vis:<16.1f} {avg_b_time:<14.2f} {avg_b_ratio:.2f}")
print(f"  {'DFS':<12} {avg_f_len:<18.1f} {avg_f_vis:<16.1f} {avg_f_time:<14.2f} {avg_f_ratio:.2f}")
print("=" * 80)

# --- 表2：按距离分组 ---
print("\n" + "=" * 80)
print("                    按起终点距离分组统计")
print("=" * 80)

df_valid["dist_group"] = pd.cut(df_valid["straight_dist"],
                                 bins=[0, 1000, 3000, float('inf')],
                                 labels=["Short (<1km)", "Medium (1-3km)", "Long (>3km)"])

for group_name in ["Short (<1km)", "Medium (1-3km)", "Long (>3km)"]:
    group = df_valid[df_valid["dist_group"] == group_name]
    if len(group) == 0:
        continue
    print(f"\n  [{group_name}] - {len(group)} trajectories")
    print(f"  {'算法':<12} {'平均路径长度(m)':<18} {'平均访问节点数':<16} {'平均耗时(ms)'}")
    print(f"  {'-' * 60}")
    print(f"  {'A*':<12} {group['astar_len'].mean():<18.1f} {group['astar_visited'].mean():<16.1f} {group['astar_time'].mean():<14.2f}")
    print(f"  {'Dijkstra':<12} {group['dijkstra_len'].mean():<18.1f} {group['dijkstra_visited'].mean():<16.1f} {group['dijkstra_time'].mean():<14.2f}")
    print(f"  {'BFS':<12} {group['bfs_len'].mean():<18.1f} {group['bfs_visited'].mean():<16.1f} {group['bfs_time'].mean():<14.2f}")
    print(f"  {'DFS':<12} {group['dfs_len'].mean():<18.1f} {group['dfs_visited'].mean():<16.1f} {group['dfs_time'].mean():<14.2f}")

print("\n" + "=" * 80)


# ============================================================
# 第六部分：可视化
# ============================================================
print("\n正在生成可视化图表...")

# --- 图1：四种算法平均值柱状图 ---
fig1, axes1 = plt.subplots(1, 3, figsize=(18, 5))
algo_names = ["A*", "Dijkstra", "BFS", "DFS"]
colors = ["#EF4444", "#F97316", "#3B82F6", "#22C55E"]

# 平均路径长度
vals = [avg_a_len, avg_d_len, avg_b_len, avg_f_len]
bars = axes1[0].bar(algo_names, vals, color=colors, edgecolor="white", linewidth=1.5)
axes1[0].set_title("Average Path Length (m)", fontsize=13, fontweight='bold')
axes1[0].set_ylabel("meters")
for bar, val in zip(bars, vals):
    axes1[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(vals) * 0.01,
                  f"{val:.0f}", ha='center', va='bottom', fontsize=10, fontweight='bold')

# 平均访问节点数
vals = [avg_a_vis, avg_d_vis, avg_b_vis, avg_f_vis]
bars = axes1[1].bar(algo_names, vals, color=colors, edgecolor="white", linewidth=1.5)
axes1[1].set_title("Average Nodes Visited", fontsize=13, fontweight='bold')
axes1[1].set_ylabel("nodes")
for bar, val in zip(bars, vals):
    axes1[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(vals) * 0.01,
                  f"{val:.0f}", ha='center', va='bottom', fontsize=10, fontweight='bold')

# 平均耗时
vals = [avg_a_time, avg_d_time, avg_b_time, avg_f_time]
bars = axes1[2].bar(algo_names, vals, color=colors, edgecolor="white", linewidth=1.5)
axes1[2].set_title("Average Time (ms)", fontsize=13, fontweight='bold')
axes1[2].set_ylabel("ms")
for bar, val in zip(bars, vals):
    axes1[2].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(vals) * 0.01,
                  f"{val:.2f}", ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.suptitle(f"Algorithm Comparison Summary ({len(df_valid)} trajectories)",
             fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig("comparison_summary.png", dpi=150, bbox_inches="tight")
plt.show()
print("图1已保存：comparison_summary.png")


# --- 图2：典型轨迹四路径可视化（带路网底图）---
if example_paths:
    fig2, axes2 = plt.subplots(1, 4, figsize=(24, 6))

    titles = [
        f"A* ({example_paths['astar_len']:.0f}m)",
        f"Dijkstra ({example_paths['dijkstra_len']:.0f}m)",
        f"BFS ({example_paths['bfs_len']:.0f}m)",
        f"DFS ({example_paths['dfs_len']:.0f}m)",
    ]
    paths = [example_paths["astar"], example_paths["dijkstra"],
             example_paths["bfs"], example_paths["dfs"]]
    path_colors = ["red", "orange", "blue", "green"]

    for ax, title, path, color in zip(axes2, titles, paths, path_colors):
        # 画灰色路网底图
        ox.plot_graph(G, ax=ax, node_size=0, edge_color="gray", edge_linewidth=0.5,
                      bgcolor="white", show=False, close=False)
        # 叠加彩色路径
        if path:
            xs = [G.nodes[node]['x'] for node in path]
            ys = [G.nodes[node]['y'] for node in path]
            ax.plot(xs, ys, color=color, linewidth=3, alpha=0.9)
        ax.set_title(title, fontsize=13, fontweight='bold')

    plt.suptitle(f"Path Visualization - Example Trajectory ({example_paths['file']})",
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig("path_visualization.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("图2已保存：path_visualization.png")


# --- 图3：路径质量比箱线图 ---
fig3, ax3 = plt.subplots(figsize=(8, 5))
box_data = [
    [1.0] * len(df_valid),  # A* 始终为 1（基准）
    df_valid["dijkstra_ratio"].tolist(),
    df_valid["bfs_ratio"].tolist(),
    df_valid["dfs_ratio"].tolist(),
]
bp = ax3.boxplot(box_data, labels=algo_names, patch_artist=True, widths=0.5,
                 medianprops=dict(color="black", linewidth=2))
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)
ax3.axhline(y=1.0, color='red', linestyle='--', linewidth=1, alpha=0.5, label="Optimal (A* = 1.0)")
ax3.set_ylabel("Path Length / A* Path Length", fontsize=12)
ax3.set_title("Path Quality Ratio (closer to 1.0 = better)", fontsize=13, fontweight='bold')
ax3.legend()
plt.tight_layout()
plt.savefig("path_quality.png", dpi=150, bbox_inches="tight")
plt.show()
print("图3已保存：path_quality.png")


# ============================================================
# 第七部分：结论
# ============================================================
print("\n" + "=" * 80)
print("                           实验结论")
print("=" * 80)

print(f"""
  本实验对 {len(df_valid)} 条真实出租车轨迹，使用四种算法进行路径搜索对比，结论如下：

  1. A* 综合表现最优
     路径最短（平均 {avg_a_len:.0f}m），访问节点较少（平均 {avg_a_vis:.0f} 个），
     启发函数（Haversine直线距离）有效引导搜索方向，减少无效探索。

  2. Dijkstra 路径与 A* 相同，但更慢
     路径长度与 A* 完全一致（质量比 {avg_d_ratio:.2f}），但访问节点数更多（平均 {avg_d_vis:.0f} 个），
     因为没有启发函数，需要"盲目"搜索所有方向。
     这直接证明了 A* 的启发函数的价值。

  3. BFS 路径质量尚可，但效率最低
     路径质量比 {avg_b_ratio:.2f}（接近最优），但访问节点数最多（平均 {avg_b_vis:.0f} 个），
     因为 BFS 不考虑边权重，按跳数搜索。

  4. DFS 路径质量最差且不稳定
     路径质量比 {avg_f_ratio:.2f}（明显偏离最优），且不同轨迹间波动大，
     DFS 不保证最优解，不适合导航场景。

  未来工作：可考虑对比双向 A*、Contraction Hierarchies 等更高级的算法。
""")
print("=" * 80)
print("\n程序运行完成！")