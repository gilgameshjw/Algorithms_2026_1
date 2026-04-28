import json
def decode_file(input_file, output_file):
    with open(input_file, "rb") as f:
        header_len = int.from_bytes(f.read(4), "big")
        header = f.read(header_len)
        codes = json.loads(header.decode())
        codes = {v: int(k) for k, v in codes.items()}
        padding = ord(f.read(1))
        data = f.read()
    bit_string = ""
    for byte in data:
        bit_string += format(byte, "08b")
    bit_string = bit_string[:-padding]
    current = ""
    decoded_bytes = []
    for bit in bit_string:
        current += bit
        if current in codes:
            decoded_bytes.append(codes[current])
            current = ""
    with open(output_file, "wb") as f:
        f.write(bytes(decoded_bytes))

if __name__ == "__main__":
    import sys
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    decode_file(input_file, output_file)

    print("Decoding finished.")