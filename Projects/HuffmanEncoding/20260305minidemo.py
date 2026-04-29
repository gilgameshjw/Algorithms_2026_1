import heapq
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


# ===== Example =====
text = "aaabbc"

codes = huffman_encoding(text)

print("Original text:", text)
print("Huffman Codes:", codes)

encoded = ''.join(codes[c] for c in text)
print("Encoded text:", encoded)
