import heapq
import json
from collections import Counter


def huffman_encoding(data):
    freq = Counter(data)

    heap = [[weight, [byte, ""]] for byte, weight in freq.items()]
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


def encode_file(input_file, output_file):

    with open(input_file, "rb") as f:
        data = f.read()

    codes = huffman_encoding(data)

    encoded_bits = ''.join(codes[b] for b in data)

    padding = 8 - len(encoded_bits) % 8
    encoded_bits += "0" * padding

    byte_array = bytearray()

    for i in range(0, len(encoded_bits), 8):
        byte_array.append(int(encoded_bits[i:i+8], 2))

    header = json.dumps({str(k): v for k, v in codes.items()})
    header_bytes = header.encode()

    with open(output_file, "wb") as f:

        f.write(len(header_bytes).to_bytes(4, "big"))

        f.write(header_bytes)

        f.write(bytes([padding]))

        f.write(byte_array)


if __name__ == "__main__":

    import sys

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    encode_file(input_file, output_file)

    print("Encoding finished.")