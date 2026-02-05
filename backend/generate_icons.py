"""
Generate simple placeholder icons for the Chrome extension.
Creates minimal PNG files without external dependencies.
"""

import struct
import zlib
import os


def create_png(width: int, height: int, color: tuple) -> bytes:
    """Create a simple solid-color PNG image."""
    def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        chunk_len = len(data)
        chunk_crc = zlib.crc32(chunk_type + data) & 0xffffffff
        return struct.pack('>I', chunk_len) + chunk_type + data + struct.pack('>I', chunk_crc)

    # PNG signature
    signature = b'\x89PNG\r\n\x1a\n'

    # IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)  # 8-bit RGB
    ihdr = make_chunk(b'IHDR', ihdr_data)

    # IDAT chunk (image data)
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # Filter type: None
        for x in range(width):
            # Create a simple circular gradient
            cx, cy = width // 2, height // 2
            dx, dy = x - cx, y - cy
            dist_sq = dx * dx + dy * dy
            radius_sq = (min(width, height) // 2 - 2) ** 2

            if dist_sq <= radius_sq:
                # Inside circle - use primary color
                raw_data += bytes(color[:3])
            else:
                # Outside circle - transparent (but since RGB, use white)
                raw_data += b'\xff\xff\xff'

    compressed = zlib.compress(raw_data, 9)
    idat = make_chunk(b'IDAT', compressed)

    # IEND chunk
    iend = make_chunk(b'IEND', b'')

    return signature + ihdr + idat + iend


def create_icon_with_design(size: int) -> bytes:
    """Create an icon with a hanger design."""
    def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        chunk_len = len(data)
        chunk_crc = zlib.crc32(chunk_type + data) & 0xffffffff
        return struct.pack('>I', chunk_len) + chunk_type + data + struct.pack('>I', chunk_crc)

    # PNG signature
    signature = b'\x89PNG\r\n\x1a\n'

    # IHDR chunk with RGBA
    ihdr_data = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA
    ihdr = make_chunk(b'IHDR', ihdr_data)

    # Primary color (indigo)
    primary = (99, 102, 241)
    white = (255, 255, 255)

    # Build pixel data
    raw_data = b''
    center = size // 2
    radius = size // 2 - max(1, size // 16)

    for y in range(size):
        raw_data += b'\x00'  # Filter type: None
        for x in range(size):
            dx, dy = x - center, y - center
            dist = (dx * dx + dy * dy) ** 0.5

            if dist <= radius:
                # Inside circle
                # Check if pixel is part of hanger design
                is_hanger = False

                # Hook at top (simplified)
                hook_y = size // 4
                hook_radius = size // 8
                if abs(y - hook_y) < hook_radius and abs(x - center) < hook_radius:
                    hook_dist = ((x - center) ** 2 + (y - hook_y) ** 2) ** 0.5
                    if abs(hook_dist - hook_radius * 0.7) < max(2, size // 16):
                        if y < hook_y + hook_radius // 2:
                            is_hanger = True

                # Diagonal lines
                top_y = size // 3
                bottom_y = size * 2 // 3
                line_width = max(2, size // 12)

                if top_y <= y <= bottom_y:
                    # Left diagonal
                    expected_x_left = center - (y - top_y) * (size // 4) // (bottom_y - top_y)
                    if abs(x - expected_x_left) < line_width:
                        is_hanger = True

                    # Right diagonal
                    expected_x_right = center + (y - top_y) * (size // 4) // (bottom_y - top_y)
                    if abs(x - expected_x_right) < line_width:
                        is_hanger = True

                # Bottom horizontal line
                if abs(y - bottom_y) < line_width:
                    left_x = center - size // 4
                    right_x = center + size // 4
                    if left_x <= x <= right_x:
                        is_hanger = True

                if is_hanger:
                    raw_data += bytes(white) + b'\xff'
                else:
                    raw_data += bytes(primary) + b'\xff'
            else:
                # Outside circle - transparent
                raw_data += b'\x00\x00\x00\x00'

    compressed = zlib.compress(raw_data, 9)
    idat = make_chunk(b'IDAT', compressed)

    # IEND chunk
    iend = make_chunk(b'IEND', b'')

    return signature + ihdr + idat + iend


def main():
    # Get the icons directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(script_dir, '..', 'extension', 'icons')

    # Ensure directory exists
    os.makedirs(icons_dir, exist_ok=True)

    # Generate icons
    sizes = [16, 48, 128]
    for size in sizes:
        output_path = os.path.join(icons_dir, f'icon{size}.png')
        png_data = create_icon_with_design(size)
        with open(output_path, 'wb') as f:
            f.write(png_data)
        print(f"Created: {output_path}")

    print("Done! Icons created in extension/icons/")


if __name__ == "__main__":
    main()
