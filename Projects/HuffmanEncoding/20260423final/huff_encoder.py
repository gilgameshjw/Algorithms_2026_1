import json
import heapq
import time
from collections import Counter
from pathlib import Path


# ================= 1. 【核心优化】大容量比特写入器 =================
class FastBitWriter:
    def __init__(self, file_object):
        self.file = file_object
        self.bit_buffer = ""  # 使用字符串作为位缓冲池

    def write_bits(self, bit_string):
        self.bit_buffer += bit_string
        # 当缓冲区积累到 1MB 大小时（800万个位），触发一次性转换并写入
        if len(self.bit_buffer) >= 8000000:
            # 确保只处理 8 的倍数
            num_bytes = len(self.bit_buffer) // 8
            bits_to_write = self.bit_buffer[:num_bytes * 8]
            self.bit_buffer = self.bit_buffer[num_bytes * 8:]

            # 【提速神技】：利用底层 C 函数将 01 字符串转为字节流
            self.file.write(int(bits_to_write, 2).to_bytes(num_bytes, byteorder='big'))

    def flush(self):
        """处理最后剩余不足 8 位的数据"""
        if self.bit_buffer:
            padding_bits = (8 - len(self.bit_buffer) % 8) % 8
            self.bit_buffer += '0' * padding_bits
            num_bytes = len(self.bit_buffer) // 8
            self.file.write(int(self.bit_buffer, 2).to_bytes(num_bytes, byteorder='big'))
            return padding_bits
        return 0


# ================= 2. 文件与频率扫描 (保持不变) =================
def scan_folder(folder_path):
    folder = Path(folder_path)
    file_registry = []
    for file_path in folder.rglob('*'):
        if file_path.is_file():
            file_registry.append({
                "relative_path": str(file_path.relative_to(folder)),
                "absolute_path": file_path,
                "size_bytes": file_path.stat().st_size
            })
    return file_registry


def count_global_frequencies(file_registry):
    print("[1/3] 正在扫描文件内容，统计哈夫曼频率...")
    global_freq = Counter()
    for f in file_registry:
        with open(f["absolute_path"], 'rb') as file:
            while True:
                chunk = file.read(1024 * 1024)
                if not chunk: break
                global_freq.update(chunk)
    return global_freq


# ================= 3. 哈夫曼树核心算法 (保持不变) =================
def build_huffman_dict(frequencies):
    print("[2/3] 正在生成哈夫曼树与编码字典...")
    heap = [[weight, [byte, ""]] for byte, weight in frequencies.items()]
    heapq.heapify(heap)
    if len(heap) == 1: return {heap[0][1][0]: "0"}
    while len(heap) > 1:
        low1, low2 = heapq.heappop(heap), heapq.heappop(heap)
        for pair in low1[1:]: pair[1] = '0' + pair[1]
        for pair in low2[1:]: pair[1] = '1' + pair[1]
        heapq.heappush(heap, [low1[0] + low2[0]] + low1[1:] + low2[1:])
    return dict(heap[0][1:])


# ================= 4. 压缩主控 (提速版) =================
def compress_folder(input_folder, output_archive_path):
    start_total = time.time()

    files = scan_folder(input_folder)
    if not files: return

    t1 = time.time()
    global_freq = count_global_frequencies(files)
    print(f"      -> 扫描完成: {time.time() - t1:.2f}s")

    t2 = time.time()
    huff_dict = build_huffman_dict(global_freq)
    print(f"      -> 建树完成: {time.time() - t2:.2f}s")

    # 【提速优化】：预先将哈夫曼字典转换为快速查找表
    # 之前是 huff_dict[byte]，现在我们建立一个 256 长度的列表，直接用索引取，速度更快
    lookup_table = [huff_dict.get(i, "") for i in range(256)]

    print(f"[3/3] 开始极速压缩写入...")
    t3 = time.time()

    header_info = {
        "files": [{"path": f["relative_path"], "size": f["size_bytes"]} for f in files],
        "huff_dict": {str(k): v for k, v in huff_dict.items()},
        "padding_bits": 0
    }

    with open(output_archive_path, 'wb') as archive_file:
        header_json = json.dumps(header_info).encode('utf-8')
        archive_file.write(len(header_json).to_bytes(4, byteorder='big'))
        archive_file.write(header_json)

        writer = FastBitWriter(archive_file)
        for f in files:
            print(f"  -> 正在压缩: {f['relative_path']}")
            with open(f["absolute_path"], 'rb') as source_file:
                while True:
                    chunk = source_file.read(1024 * 1024)
                    if not chunk: break
                    # 【提速关键】：一次性处理整个 chunk
                    bit_string = "".join(lookup_table[b] for b in chunk)
                    writer.write_bits(bit_string)

        padding = writer.flush()
        archive_file.write(bytes([padding]))

    total_duration = time.time() - start_total
    print("-" * 30)
    print(f"✅ 极速压缩成功！")
    print(f"⏱️ 总共耗时: {total_duration:.2f} 秒 (对比之前 233 秒)")
    print("-" * 30)


if __name__ == "__main__":
    test_folder = r"E:\pycharm\Huffman\test"
    archive_file_name = r"E:\pycharm\Huffman\compressed_data.huff"
    compress_folder(test_folder, archive_file_name)