import os
import sys
# === 解决 Anaconda 打包 Numba 报错的终极补丁 ===
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.makedirs(os.path.join(sys._MEIPASS, 'Library', 'bin'), exist_ok=True)
# ===============================================

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
# ... 下面全是你原来的代码，保持不变 ...
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import json
import heapq
import numpy as np
from collections import Counter
from pathlib import Path
from numba import njit


# ================= 1. 核心解压引擎 (保持巅峰性能) =================
@njit
def fast_decode_core(compressed_data, target_size, tree_left, tree_right, leaf_values, start_byte_idx, start_bits_left):
    out_buffer = np.zeros(target_size, dtype=np.uint8)
    out_idx = 0
    node = 0
    byte_idx, bits_left = start_byte_idx, start_bits_left
    while out_idx < target_size and byte_idx < len(compressed_data):
        if bits_left == 0:
            byte_idx += 1
            if byte_idx >= len(compressed_data): break
            bits_left = 8
        bits_left -= 1
        bit = (compressed_data[byte_idx] >> bits_left) & 1
        node = tree_left[node] if bit == 0 else tree_right[node]
        if leaf_values[node] != -1:
            out_buffer[out_idx] = leaf_values[node]
            out_idx += 1
            node = 0
    return out_buffer, byte_idx, bits_left


class FastBitWriter:
    def __init__(self, file_object):
        self.file = file_object
        self.bit_buffer = ""

    def write_bits(self, bit_string):
        self.bit_buffer += bit_string
        if len(self.bit_buffer) >= 8000000:
            num_bytes = len(self.bit_buffer) // 8
            bits_to_write = self.bit_buffer[:num_bytes * 8]
            self.bit_buffer = self.bit_buffer[num_bytes * 8:]
            self.file.write(int(bits_to_write, 2).to_bytes(num_bytes, byteorder='big'))

    def flush(self):
        if self.bit_buffer:
            padding_bits = (8 - len(self.bit_buffer) % 8) % 8
            self.bit_buffer += '0' * padding_bits
            num_bytes = len(self.bit_buffer) // 8
            self.file.write(int(self.bit_buffer, 2).to_bytes(num_bytes, byteorder='big'))
            return padding_bits
        return 0


# ================= 2. 增强型多语言配置 =================
LANG = {
    "Chinese": {
        "title": "哈夫曼极速压缩还原系统 - Pro Ultra",
        "btn_comp": "🚀 极速压缩\n(两步完成)",
        "btn_decomp": "📦 极速还原\n(两步完成)",
        "path_info": "当前任务: ",
        "status_idle": "● 系统就绪",
        "status_running": "● 正在处理...",
        "status_done": "● 任务完成",
        "timer": "总耗时: ",
        "log_scan": "正在深度扫描文件系统...",
        "log_build": "正在构建高性能哈夫曼树...",
        "log_write": "正在执行流式压缩...",
        "log_restore": "正在启动 Numba 还原引擎...",
        "msg_done": "任务已圆满完成！"
    },
    "English": {
        "title": "Huffman Ultra - Research Edition",
        "btn_comp": "🚀 QUICK COMPRESS\n(2 Steps)",
        "btn_decomp": "📦 QUICK RESTORE\n(2 Steps)",
        "path_info": "Current Task: ",
        "status_idle": "● System Ready",
        "status_running": "● Processing...",
        "status_done": "● Task Completed",
        "timer": "Elapsed: ",
        "log_scan": "Scanning file system deeply...",
        "log_build": "Building High-Perf Huffman Tree...",
        "log_write": "Executing bitstream compression...",
        "log_restore": "Initializing Numba Engine...",
        "msg_done": "Task completed successfully!"
    }
}


# ================= 3. 主界面设计 =================
class HuffmanApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_lang = "Chinese"
        self.title("Huffman Ultra Pro")
        self.geometry("950x780")
        ctk.set_appearance_mode("dark")
        self.setup_ui()

    def setup_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))
        self.lbl_title = ctk.CTkLabel(header, text=LANG[self.current_lang]["title"],
                                      font=("Microsoft YaHei", 26, "bold"))
        self.lbl_title.pack(side="left")
        self.lang_switch = ctk.CTkSegmentedButton(header, values=["Chinese", "English"], selected_color="#6C5CE7",
                                                  command=self.update_lang)
        self.lang_switch.set("Chinese")
        self.lang_switch.pack(side="right")

        self.info_card = ctk.CTkFrame(self, fg_color="#2D3436", corner_radius=10)
        self.info_card.pack(fill="x", padx=30, pady=10)
        self.lbl_path_title = ctk.CTkLabel(self.info_card, text=LANG[self.current_lang]["path_info"],
                                           font=("Consolas", 12))
        self.lbl_path_title.pack(side="left", padx=15)
        self.entry_info = ctk.CTkEntry(self.info_card, height=40, fg_color="transparent", border_width=0,
                                       font=("Consolas", 13), placeholder_text="Waiting...")
        self.entry_info.pack(side="left", fill="x", expand=True, padx=5)

        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.pack(pady=30)
        self.btn_comp = ctk.CTkButton(btn_container, text=LANG[self.current_lang]["btn_comp"], width=380, height=140,
                                      font=("Microsoft YaHei", 22, "bold"), fg_color="#00B894", hover_color="#008B70",
                                      corner_radius=15, command=self.compress_workflow)
        self.btn_comp.pack(side="left", padx=20)
        self.btn_decomp = ctk.CTkButton(btn_container, text=LANG[self.current_lang]["btn_decomp"], width=380,
                                        height=140, font=("Microsoft YaHei", 22, "bold"), fg_color="#0984E3",
                                        hover_color="#086AB5", corner_radius=15, command=self.decompress_workflow)
        self.btn_decomp.pack(side="left", padx=20)

        p_container = ctk.CTkFrame(self, fg_color="transparent")
        p_container.pack(fill="x", padx=40)
        self.lbl_status = ctk.CTkLabel(p_container, text=LANG[self.current_lang]["status_idle"],
                                       font=("Microsoft YaHei", 13))
        self.lbl_status.pack(side="left")
        self.lbl_timer = ctk.CTkLabel(p_container, text="0.00s", font=("Consolas", 18, "bold"), text_color="#FDCB6E")
        self.lbl_timer.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(self, width=870, height=18, corner_radius=5, progress_color="#6C5CE7",
                                               fg_color="#34495E")
        self.progress_bar.pack(pady=10);
        self.progress_bar.set(0)

        self.textbox = ctk.CTkTextbox(self, width=870, height=220, font=("Consolas", 12), fg_color="#1E272E",
                                      border_width=1, border_color="#57606F")
        self.textbox.pack(padx=20, pady=10)

    def update_lang(self, choice):
        self.current_lang = choice
        L = LANG[choice]
        self.lbl_title.configure(text=L["title"])
        self.btn_comp.configure(text=L["btn_comp"])
        self.btn_decomp.configure(text=L["btn_decomp"])
        self.lbl_path_title.configure(text=L["path_info"])
        self.lbl_status.configure(text=L["status_idle"])

    def log(self, text):
        self.textbox.insert("end", f"[{time.strftime('%H:%M:%S')}] {text}\n");
        self.textbox.see("end")

    def set_ui_state(self, is_running):
        state = "disabled" if is_running else "normal"
        self.btn_comp.configure(state=state);
        self.btn_decomp.configure(state=state)
        self.lbl_status.configure(text=LANG[self.current_lang]["status_running" if is_running else "status_done"])
        if is_running:
            self.progress_bar.start()
        else:
            self.progress_bar.stop(); self.progress_bar.set(1)

    # ================= 核心流程 (暴力排除 .huff) =================
    def compress_workflow(self):
        src = filedialog.askdirectory(title="Step 1: Select Target Folder")
        if not src: return
        dst = filedialog.askdirectory(title="Step 2: Save Archive To")
        if not dst: return
        final_huff = str(Path(dst) / (Path(src).name + ".huff"))
        self.entry_info.delete(0, "end");
        self.entry_info.insert(0, final_huff)
        self.set_ui_state(True)
        threading.Thread(target=self.engine_compress, args=(src, final_huff), daemon=True).start()

    def decompress_workflow(self):
        huff = filedialog.askopenfilename(filetypes=[("Huffman", "*.huff")])
        if not huff: return
        out = filedialog.askdirectory(title="Step 2: Extract To")
        if not out: return
        self.entry_info.delete(0, "end");
        self.entry_info.insert(0, out)
        self.set_ui_state(True)
        threading.Thread(target=self.engine_decompress, args=(huff, out), daemon=True).start()

    def engine_compress(self, src, dest):
        try:
            start_t = time.time()
            self.log(LANG[self.current_lang]["log_scan"])
            root = Path(src)
            # 【暴力防御】：直接无视所有以 .huff 结尾的文件，不管它是谁
            f_list = [p for p in root.rglob('*') if p.is_file() and p.suffix.lower() != '.huff']

            freq = Counter()
            for i, f in enumerate(f_list):
                with open(f, 'rb') as file:
                    while chunk := file.read(1024 * 1024): freq.update(chunk)
                self.after(0, lambda v=i: self.progress_bar.set((v + 1) / len(f_list) * 0.3))

            self.log(LANG[self.current_lang]["log_build"])
            heap = [[w, [b, ""]] for b, w in freq.items()]
            heapq.heapify(heap)
            while len(heap) > 1:
                l1, l2 = heapq.heappop(heap), heapq.heappop(heap)
                for p in l1[1:]: p[1] = '0' + p[1]
                for p in l2[1:]: p[1] = '1' + p[1]
                heapq.heappush(heap, [l1[0] + l2[0]] + l1[1:] + l2[1:])
            h_dict = dict(heap[0][1:]);
            lookup = [h_dict.get(i, "") for i in range(256)]

            self.log(LANG[self.current_lang]["log_write"])
            header = {"files": [{"path": str(f.relative_to(root)), "size": f.stat().st_size} for f in f_list],
                      "huff_dict": {str(k): v for k, v in h_dict.items()}}
            with open(dest, 'wb') as arc:
                h_json = json.dumps(header).encode('utf-8')
                arc.write(len(h_json).to_bytes(4, 'big'));
                arc.write(h_json)
                writer = FastBitWriter(arc)
                for i, f in enumerate(f_list):
                    self.log(f" -> Packing: {f.name}")
                    with open(f, 'rb') as sf:
                        while chunk := sf.read(1024 * 1024): writer.write_bits("".join(lookup[b] for b in chunk))
                    self.after(0, lambda v=i: self.progress_bar.set(0.3 + (v + 1) / len(f_list) * 0.7))
                writer.flush()
            self.after(0, lambda: self.lbl_timer.configure(text=f"{time.time() - start_t:.2f}s"))
            self.log(f"✅ Success!")
        except Exception as e:
            self.log(f"❌ Error: {e}")
        finally:
            self.after(0, lambda: self.set_ui_state(False))

    def engine_decompress(self, src, dest):
        try:
            start_t = time.time()
            self.log(LANG[self.current_lang]["log_restore"])
            with open(src, 'rb') as f:
                h_len = int.from_bytes(f.read(4), 'big')
                header = json.loads(f.read(h_len).decode('utf-8'))
                tl, tr, lv = self.build_flat_tree(header["huff_dict"])
                f.seek(4 + h_len);
                data = np.frombuffer(f.read(), dtype=np.uint8)
            cb, cbit, root = 0, 8, Path(dest)
            for i, fi in enumerate(header["files"]):
                target = root / fi["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                self.log(f" -> Restoring: {fi['path']}")
                decoded, cb, cbit = fast_decode_core(data, fi["size"], tl, tr, lv, cb, cbit)
                with open(target, 'wb') as of: of.write(decoded.tobytes())
                self.after(0, lambda v=i: self.progress_bar.set((v + 1) / len(header["files"])))
            self.after(0, lambda: self.lbl_timer.configure(text=f"{time.time() - start_t:.2f}s"))
            self.log(f"✅ Success!")
        except Exception as e:
            self.log(f"❌ Error: {e}")
        finally:
            self.after(0, lambda: self.set_ui_state(False))

    def build_flat_tree(self, h_dict):
        tl, tr, lv = np.full(2000, -1, np.int32), np.full(2000, -1, np.int32), np.full(2000, -1, np.int32)
        nc = 1
        for char_str, code in h_dict.items():
            curr = 0
            for bit in code:
                if bit == '0':
                    if tl[curr] == -1: tl[curr] = nc; nc += 1
                    curr = tl[curr]
                else:
                    if tr[curr] == -1: tr[curr] = nc; nc += 1
                    curr = tr[curr]
            lv[curr] = int(char_str)
        return tl, tr, lv


if __name__ == "__main__":
    app = HuffmanApp()
    app.mainloop()