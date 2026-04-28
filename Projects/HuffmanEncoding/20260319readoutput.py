with open("compressedimg.huf", "rb") as f:
    header_len = int.from_bytes(f.read(4), "big")
    header = f.read(header_len)

    print("HEADER:")
    print(header.decode())

    rest = f.read()
    print("\nBODY (binary):", rest[:20])