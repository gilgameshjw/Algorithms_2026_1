import osmnx as ox
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import time
import collections
import os

# ============================================================
# 第一部分：下载北京中关村路网
# ============================================================
print("正在下载路网，请稍等（第一次需要联网，约1-2分钟）...")
G = ox.graph_from_place("Zhongguancun, Haidian, Beijing, China", network_type="drive")
print("路网下载完成！")

# ============================================================
# 第二部分：智能搜索最优轨迹（从9999个文件中）
# ============================================================
tdrive_folder = r"tdrive"  # 根据你的文件夹路径修改
# tdrive_folder = r"D:\Data (D:)\周四项目\tdrive"  # 如果上面的路径不对，用这个绝对路径

# 列出所有 .txt 文件
files_in_folder = os.listdir(tdrive_folder)
txt_files = [f for f in files_in_folder if f.endswith('.txt')]

if not txt_files:
    print("错误：tdrive 文件夹中没有找到 .txt 文件！")
    print(f"文件夹内容：{files_in_folder[:10]}...")  # 只显示前10个
    exit()

print(f"找到 {len(txt_files)} 个文件")


# ============================================================
# 第三部分：函数定义 - 评估轨迹质量
# ============================================================
def evaluate_trajectory(filepath, max_points=300):
    """
    评估一个轨迹文件的质量
    返回 (唯一节点数, 最远两节点距离, 文件名, 节点列表)
    如果质量不好返回 (0, 0, 文件名, [])
    """
    try:
        # 读取文件
        df = pd.read_csv(filepath, header=None, names=["id", "time", "lon", "lat"])

        if len(df) < 10:  # 点数太少
            return 0, 0, os.path.basename(filepath), []

        # 限制点数（太多点会很慢）
        df = df.head(max_points)

        # 吸附到路网节点
        nodes = []
        for i, row in df.iterrows():
            try:
                node = ox.nearest_nodes(G, row["lon"], row["lat"])
                nodes.append(node)
            except:
                pass

        if len(nodes) < 2:
            return 0, 0, os.path.basename(filepath), []

        # 删除重复，保留唯一节点
        unique_nodes = []
        for node in nodes:
            if node not in unique_nodes:
                unique_nodes.append(node)

        if len(unique_nodes) < 2:  # 节点太少（都在同一个地方）
            return 0, 0, os.path.basename(filepath), []

        # 找最远的两个节点
        max_distance = 0
        best_pair = None
        for i in range(len(unique_nodes)):
            for j in range(i + 1, len(unique_nodes)):
                node_i = unique_nodes[i]
                node_j = unique_nodes[j]
                try:
                    if nx.has_path(G, node_i, node_j):
                        distance = nx.shortest_path_length(G, node_i, node_j, weight="length")
                        if distance > max_distance:
                            max_distance = distance
                            best_pair = (node_i, node_j)
                except:
                    pass

        if max_distance < 500:  # 距离太近（不够有意义）
            return 0, 0, os.path.basename(filepath), []

        return len(unique_nodes), max_distance, os.path.basename(filepath), unique_nodes

    except Exception as e:
        return 0, 0, os.path.basename(filepath), []


# ============================================================
# 第四部分：搜索最优轨迹
# ============================================================
print("\n正在搜索最优轨迹（从9999个文件中）...")
print("这可能需要几分钟，请耐心等待...\n")

best_score = 0
best_result = None
checked_count = 0
found_good_trajectory = False

# 逐个检查文件，找到最好的
for idx, txt_file in enumerate(txt_files):
    filepath = os.path.join(tdrive_folder, txt_file)
    unique_count, max_dist, filename, nodes = evaluate_trajectory(filepath)

    checked_count += 1

    # 每检查100个文件打印一次进度
    if checked_count % 100 == 0:
        percentage = (checked_count / len(txt_files)) * 100
        print(f"  已检查 {checked_count:>5} 个文件...  ({percentage:>5.1f}%)")
    # 评分：唯一节点数 * 最远距离（综合考虑两个因素）
    score = unique_count * (max_dist / 1000)  # 距离用 km 衡量

    if score > best_score:
        best_score = score
        best_result = (unique_count, max_dist, filename, nodes)
        if max_dist > 1000 and unique_count > 5:
            found_good_trajectory = True

print(f"\n✓ 已检查 {checked_count} 个文件")

if not found_good_trajectory or best_result is None:
    print("\n⚠️  警告：没有找到理想的轨迹（距离 > 1000m 且节点 > 5 个）")
    print("将使用找到的最优轨迹...")

unique_count, max_dist, best_file, unique_nodes = best_result
print(f"\n✓ 最优轨迹文件：{best_file}")
print(f"✓ 唯一节点数：{unique_count} 个")
print(f"✓ 最远距离：{max_dist:.1f} 米（约 {max_dist / 1000:.2f} 公里）")


# 从唯一节点中找最远的两个
def find_farthest_nodes(G, node_list):
    """找出列表中距离最远的两个节点"""
    max_distance = 0
    best_pair = None

    for i in range(len(node_list)):
        for j in range(i + 1, len(node_list)):
            node_i = node_list[i]
            node_j = node_list[j]
            try:
                if nx.has_path(G, node_i, node_j):
                    distance = nx.shortest_path_length(G, node_i, node_j, weight="length")
                    if distance > max_distance:
                        max_distance = distance
                        best_pair = (node_i, node_j)
            except:
                pass

    return best_pair, max_distance


(start_node, end_node), route_distance = find_farthest_nodes(G, unique_nodes)

print(f"\n✓ 起点节点：{start_node}")
print(f"✓ 终点节点：{end_node}")
print(f"✓ 路由距离：{route_distance:.1f} 米")


# ============================================================
# 第五部分：三个算法定义
# ============================================================

# --- 算法1：A* ---
def run_astar(G, start, end):
    t0 = time.time()
    try:
        path = nx.astar_path(G, start, end, weight="length")
        t1 = time.time()
        length = nx.path_weight(G, path, weight="length")
        return path, length, round((t1 - t0) * 1000, 2)
    except Exception as e:
        print(f"  [警告] A* 算法出错：{e}")
        return None, -1, -1


# --- 算法2：BFS（迭代，队列实现）---
def run_bfs(G, start, end):
    t0 = time.time()
    visited = set()
    queue = collections.deque()
    queue.append([start])
    visited.add(start)
    path = None

    while queue:
        current_path = queue.popleft()
        current_node = current_path[-1]

        if current_node == end:
            path = current_path
            break

        for neighbor in G.neighbors(current_node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(current_path + [neighbor])

    t1 = time.time()
    length = nx.path_weight(G, path, weight="length") if path else -1
    return path, length, round((t1 - t0) * 1000, 2)


# --- 算法3：DFS（迭代，显式栈，不用递归）---
def run_dfs(G, start, end):
    t0 = time.time()
    visited = set()
    stack = [[start]]
    path = None

    while stack:
        current_path = stack.pop()
        current_node = current_path[-1]

        if current_node in visited:
            continue
        visited.add(current_node)

        if current_node == end:
            path = current_path
            break

        for neighbor in G.neighbors(current_node):
            if neighbor not in visited:
                stack.append(current_path + [neighbor])

    t1 = time.time()
    length = nx.path_weight(G, path, weight="length") if path else -1
    return path, length, round((t1 - t0) * 1000, 2)


# ============================================================
# 第六部分：运行三个算法
# ============================================================
print("\n正在运行三个算法，请稍等...")

path_astar, len_astar, time_astar = run_astar(G, start_node, end_node)
print("  ✓ A* 完成")

path_bfs, len_bfs, time_bfs = run_bfs(G, start_node, end_node)
print("  ✓ BFS 完成")

path_dfs, len_dfs, time_dfs = run_dfs(G, start_node, end_node)
print("  ✓ DFS 完成")

# ============================================================
# 第七部分：打印对比表
# ============================================================
print("\n" + "=" * 70)
print("算法对比结果")
print("=" * 70)
print(f"{'算法':<8} {'路径长度(m)':<20} {'访问节点数':<15} {'耗时(ms)':<12}")
print("-" * 70)

if path_astar:
    print(f"{'A*':<8} {len_astar:<20.1f} {len(path_astar):<15} {time_astar:<12}")
else:
    print(f"{'A*':<8} {'失败':<20} {'-':<15} {'-':<12}")

if path_bfs:
    print(f"{'BFS':<8} {len_bfs:<20.1f} {len(path_bfs):<15} {time_bfs:<12}")
else:
    print(f"{'BFS':<8} {'失败':<20} {'-':<15} {'-':<12}")

if path_dfs:
    print(f"{'DFS':<8} {len_dfs:<20.1f} {len(path_dfs):<15} {time_dfs:<12}")
else:
    print(f"{'DFS':<8} {'失败':<20} {'-':<15} {'-':<12}")

print("=" * 70)

# ============================================================
# 第八部分：可视化，三条路径分别画图
# ============================================================
print("\n正在生成地图...")

fig, axes = plt.subplots(1, 3, figsize=(20, 6))
titles = ["A* 算法", "BFS 算法", "DFS 算法"]
paths = [path_astar, path_bfs, path_dfs]
colors = ["red", "blue", "green"]

for ax, title, path, color in zip(axes, titles, paths, colors):
    if path:
        ox.plot_graph_route(
            G, path,
            route_color=color,
            route_linewidth=3,
            node_size=0,
            bgcolor="white",
            ax=ax,
            show=False,
            close=False
        )
    ax.set_title(title, fontsize=14, fontweight='bold')

plt.suptitle("三种算法路径对比（北京中关村路网）", fontsize=16, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig("result_map.png", dpi=150, bbox_inches="tight")
plt.show()
print("✓ 地图已保存为 result_map.png")

# 保存轨迹信息到文本文件
with open("trajectory_info.txt", "w", encoding="utf-8") as f:
    f.write("=" * 70 + "\n")
    f.write("轨迹信息\n")
    f.write("=" * 70 + "\n")
    f.write(f"使用的数据文件：{best_file}\n")
    f.write(f"唯一节点数：{unique_count}\n")
    f.write(f"起点节点：{start_node}\n")
    f.write(f"终点节点：{end_node}\n")
    f.write(f"路由距离：{route_distance:.1f} 米\n")
    f.write("\n" + "=" * 70 + "\n")
    f.write("算法对比结果\n")
    f.write("=" * 70 + "\n")
    f.write(f"{'算法':<8} {'路径长度(m)':<20} {'访问节点数':<15} {'耗时(ms)':<12}\n")
    f.write("-" * 70 + "\n")
    if path_astar:
        f.write(f"{'A*':<8} {len_astar:<20.1f} {len(path_astar):<15} {time_astar:<12}\n")
    if path_bfs:
        f.write(f"{'BFS':<8} {len_bfs:<20.1f} {len(path_bfs):<15} {time_bfs:<12}\n")
    if path_dfs:
        f.write(f"{'DFS':<8} {len_dfs:<20.1f} {len(path_dfs):<15} {time_dfs:<12}\n")

print("✓ 轨迹信息已保存为 trajectory_info.txt")

print("\n✓ 程序运行完成！")