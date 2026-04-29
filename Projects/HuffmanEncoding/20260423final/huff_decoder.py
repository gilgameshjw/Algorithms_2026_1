import json
import os
import numpy as np
from pathlib import Path
from numba import njit


# ================= 1. 构建扁平化数组树 =================
def build_flat_tree(huff_dict):
    max_nodes = 2000
    tree_left = np.full(max_nodes, -1, dtype=np.int32)
    tree_right = np.full(max_nodes, -1, dtype=np.int32)
    leaf_values = np.full(max_nodes, -1, dtype=np.int32)

    node_count = 1
    for char_str, code_str in huff_dict.items():
        current = 0
        for bit in code_str:
            if bit == '0':
                if tree_left[current] == -1:
                    tree_left[current] = node_count
                    node_count += 1
                current = tree_left[current]
            else:
                if tree_right[current] == -1:
                    tree_right[current] = node_count
                    node_count += 1
                current = tree_right[current]
        leaf_values[current] = int(char_str)

    return tree_left, tree_right, leaf_values


# ================= 2. 【核心修复】带位指针记忆的 C 引擎 =================
@njit
def fast_decode_core(compressed_data, target_size, tree_left, tree_right, leaf_values, start_byte_idx, start_bits_left):
    out_buffer = np.zeros(target_size, dtype=np.uint8)
    out_idx = 0
    node = 0

    # 接收上一个文件停下的精确位置
    byte_idx = start_byte_idx
    bits_left = start_bits_left

    while out_idx < target_size and byte_idx < len(compressed_data):
        # 如果当前字节的 8 个位都读完了，跨到下一个字节
        if bits_left == 0:
            byte_idx += 1
            if byte_idx >= len(compressed_data):
                break
            bits_left = 8

        bits_left -= 1
        bit = (compressed_data[byte_idx] >> bits_left) & 1

        if bit == 0:
            node = tree_left[node]
        else:
            node = tree_right[node]

        if leaf_values[node] != -1:
            out_buffer[out_idx] = leaf_values[node]
            out_idx += 1
            node = 0

            # 解压完这个文件后，把停顿的精确位置返回给 Python 主程序
    return out_buffer, byte_idx, bits_left


# ================= 3. 极速解压主控 =================
def decompress_folder(archive_path, output_folder):
    print(f"\n[解压 4.1 Numba 终极无损版] 准备从 {archive_path} 还原文件...")
    output_base = Path(output_folder)

    with open(archive_path, 'rb') as f:
        header_length = int.from_bytes(f.read(4), byteorder='big')
        header_info = json.loads(f.read(header_length).decode('utf-8'))
        files_info = header_info["files"]

        tree_left, tree_right, leaf_values = build_flat_tree(header_info["huff_dict"])

        f.seek(4 + header_length)

        print("  -> 正在一次性载入压缩二进制流...")
        # 直接把所有二进制数据吞进 numpy 数组
        compressed_data = np.frombuffer(f.read(), dtype=np.uint8)

        # 【全场最关键】：定义全局位指针，从第 0 个字节的第 8 位开始
        current_byte_idx = 0
        current_bits_left = 8

        for file_meta in files_info:
            target_path = output_base / file_meta["path"]
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_size = file_meta["size"]

            print(f"  -> ⚡ Numba 极速解码中: {file_meta['path']} (预计 {target_size} 字节)")

            # 将全局指针传进去，再把更新后的全局指针接出来，实现真正的无缝衔接！
            decoded_array, current_byte_idx, current_bits_left = fast_decode_core(
                compressed_data, target_size, tree_left, tree_right, leaf_values,
                current_byte_idx, current_bits_left
            )

            with open(target_path, 'wb') as out_f:
                out_f.write(decoded_array.tobytes())

    print("\n✅ 所有文件还原成功！")


# ================= 测试执行 =================
if __name__ == "__main__":
    archive_file_name = r"E:\pycharm\Huffman\compressed_data.huff"
    restore_folder = r"E:\pycharm\Huffman\test_unpacked"  # 新建一个文件夹，看奇迹发生

    decompress_folder(archive_file_name, restore_folder)