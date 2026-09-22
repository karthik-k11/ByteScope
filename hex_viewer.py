def generate_hex_view(file_path, bytes_per_row=16, max_bytes=256):
    rows = []

    with open(file_path, "rb") as file:
        data = file.read(max_bytes)

    for offset in range(0, len(data), bytes_per_row):
        chunk = data[offset:offset + bytes_per_row]

        hex_bytes = " ".join(f"{byte:02X}" for byte in chunk)

        ascii_text = "".join(
            chr(byte) if 32 <= byte <= 126 else "."
            for byte in chunk
        )

        rows.append({
            "offset": f"{offset:08X}",
            "hex": hex_bytes,
            "ascii": ascii_text
        })

    return rows