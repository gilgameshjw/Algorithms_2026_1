import heapq
import math
from collections import Counter


def huffman_encoding(text):
    freq = Counter(text)

    heap = [[weight, [char, ""]] for char, weight in freq.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        low1 = heapq.heappop(heap)
        low2 = heapq.heappop(heap)

        for pair in low1[1:]:
            pair[1] = '0' + pair[1]
        for pair in low2[1:]:
            pair[1] = '1' + pair[1]

        heapq.heappush(heap, [low1[0] + low2[0]] + low1[1:] + low2[1:])

    return dict(heap[0][1:])


# 计算熵
def entropy(text):
    freq = Counter(text)
    n = len(text)

    H = 0
    for count in freq.values():
        p = count / n
        H -= p * math.log2(p)

    return H


# 计算平均编码长度
def avg_code_length(text, codes):
    freq = Counter(text)
    n = len(text)

    L = 0
    for char, count in freq.items():
        p = count / n
        L += p * len(codes[char])

    return L


# =====================
# Example
# =====================

text = "shjjhjhjhjssksk jskdjwwmkllllsda jjj"

codes = huffman_encoding(text)

encoded = ''.join(codes[c] for c in text)

H = entropy(text)

L = avg_code_length(text, codes)

print("Original text:", text)
print("Huffman Codes:", codes)
print("Encoded text:", encoded)

print("\nEntropy H(X):", H)
print("Average Code Length L:", L)

print("\nShannon Bound:")
print("H(X) ≤ L < H(X)+1")