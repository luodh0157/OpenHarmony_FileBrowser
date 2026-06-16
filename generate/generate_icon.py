#!/usr/bin/env python3
"""
Universal icon generator - Convert images to ICO/ICNS formats.

Supports:
  Input formats: PNG, JPG, JPEG, BMP, GIF, TIFF, WEBP, SVG (via Pillow)
  Output formats: ICO (Windows), ICNS (macOS)

Usage:
  python generate_icon.py -i app.png                    # Generates app.ico and app.icns
  python generate_icon.py -i app.png -o app.ico          # Generates only app.ico
  python generate_icon.py -i app.png -o app.icns         # Generates only app.icns
  python generate_icon.py -i logo.jpg -o favicon.ico --sizes 16 32
"""

import argparse
import io
import struct
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)


SUPPORTED_INPUT_FORMATS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp", ".svg"}
SUPPORTED_OUTPUT_FORMATS = {".ico", ".icns"}

DEFAULT_ICO_SIZES = [16, 32, 48, 64, 128, 256]
DEFAULT_ICNS_SIZES = [16, 32, 48, 128, 256, 512, 1024]
DEFAULT_RADIUS_RATIO = 0.2  # 默认圆角半径为图片尺寸的20%


def create_rounded_mask(size: int, radius: int) -> Image:
    """Create a rounded rectangle mask with antialiased edges."""
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def apply_rounded_corners(image: Image.Image, radius: int) -> Image.Image:
    """Apply rounded corners to an image using a mask."""
    if radius <= 0:
        return image
    mask = create_rounded_mask(image.width, radius)
    result = image.copy()
    result.putalpha(mask)
    return result


def save_ico_with_images(images: list, output_path: Path):
    """Save multiple pre-resized images as a multi-frame ICO file."""
    sizes = [img.width for img in images]
    png_data = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_data.append(buf.getvalue())

    header = struct.pack("<HHH", 0, 1, len(sizes))
    entries = b""
    offset = 6 + 16 * len(sizes)

    for s, data in zip(sizes, png_data):
        w = 0 if s >= 256 else s
        h = 0 if s >= 256 else s
        entry = struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), offset)
        entries += entry
        offset += len(data)

    with open(output_path, "wb") as f:
        f.write(header)
        f.write(entries)
        for data in png_data:
            f.write(data)


def save_icns_with_images(images: list, output_path: Path):
    """Save multiple pre-resized images as a multi-frame ICNS file."""
    if not images:
        return
    
    # ICNS requires specific icon types, use Pillow's built-in with largest image
    # For simplicity, save the largest image as ICNS
    largest = max(images, key=lambda img: img.width)
    largest.save(str(output_path), format="ICNS")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert images to ICO/ICNS icon formats.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i app.png                              # Generate both .ico and .icns
  %(prog)s -i app.png -o app.ico                   # Generate only .ico
  %(prog)s -i app.png -o icons/app.icns            # Generate .icns to custom path
  %(prog)s -i logo.jpg -o favicon.ico --sizes 16 32
  %(prog)s -i icon.svg -o icon.ico --sizes 16 32 48 64 128 256
        """,
    )

    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input image file (PNG, JPG, BMP, GIF, TIFF, WEBP, SVG)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output icon file (.ico or .icns). If not specified, generates both formats in input directory.",
    )
    parser.add_argument(
        "-s", "--sizes",
        type=int,
        nargs="+",
        default=None,
        help="Icon sizes to generate (default: auto-detect based on output format)",
    )
    parser.add_argument(
        "-r", "--radius",
        type=float,
        default=None,
        help="Corner radius in pixels, or ratio (0-1) of size. 0 = square (no rounding). Default: 0.2 (20%% of size)",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress output messages",
    )

    return parser.parse_args()


def log(message, quiet=False):
    if not quiet:
        print(message)


def convert_to_ico(input_path: Path, output_path: Path, sizes: list, radius: float, quiet: bool = False):
    log(f"Loading source image: {input_path}", quiet)
    icon_base = Image.open(input_path).convert("RGBA")
    log(f"  Source size: {icon_base.size}", quiet)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    resized_images = []
    for s in sizes:
        resized = icon_base.resize((s, s), Image.LANCZOS)
        if radius > 0:
            actual_radius = int(s * radius) if radius <= 1 else int(radius)
            resized = apply_rounded_corners(resized, actual_radius)
        resized_images.append(resized)
    
    save_ico_with_images(resized_images, output_path)
    log(f"  Created: {output_path} ({len(sizes)} sizes: {', '.join(str(s) for s in sizes)})", quiet)
    log(f"  File size: {output_path.stat().st_size:,} bytes", quiet)


def convert_to_icns(input_path: Path, output_path: Path, sizes: list, radius: float, quiet: bool = False):
    log(f"Loading source image: {input_path}", quiet)
    icon_base = Image.open(input_path).convert("RGBA")
    log(f"  Source size: {icon_base.size}", quiet)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    resized_images = []
    for s in sizes:
        resized = icon_base.resize((s, s), Image.LANCZOS)
        if radius > 0:
            actual_radius = int(s * radius) if radius <= 1 else int(radius)
            resized = apply_rounded_corners(resized, actual_radius)
        resized_images.append(resized)
    
    save_icns_with_images(resized_images, output_path)
    log(f"  Created: {output_path} ({len(sizes)} sizes: {', '.join(str(s) for s in sizes)})", quiet)
    log(f"  File size: {output_path.stat().st_size:,} bytes", quiet)


def main():
    args = parse_args()

    input_path = Path(args.input)
    quiet = args.quiet

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    input_ext = input_path.suffix.lower()
    if input_ext not in SUPPORTED_INPUT_FORMATS:
        print(f"Error: Unsupported input format '{input_ext}'. Supported: {', '.join(sorted(SUPPORTED_INPUT_FORMATS))}")
        sys.exit(1)

    # Determine output paths and formats
    if args.output:
        output_path = Path(args.output)
        output_ext = output_path.suffix.lower()
        if output_ext not in SUPPORTED_OUTPUT_FORMATS:
            print(f"Error: Unsupported output format '{output_ext}'. Supported: {', '.join(sorted(SUPPORTED_OUTPUT_FORMATS))}")
            sys.exit(1)
        outputs = [(output_ext, output_path)]
    else:
        # Default: generate both .ico and .icns in input directory
        base_name = input_path.stem
        output_dir = input_path.parent
        outputs = [
            (".ico", output_dir / f"{base_name}.ico"),
            (".icns", output_dir / f"{base_name}.icns"),
        ]

    # Determine sizes
    if args.sizes:
        sizes_map = {ext: sorted(args.sizes) for ext, _ in outputs}
    else:
        sizes_map = {}
        for ext, _ in outputs:
            sizes_map[ext] = DEFAULT_ICO_SIZES if ext == ".ico" else DEFAULT_ICNS_SIZES

    # Determine radius
    radius = args.radius if args.radius is not None else DEFAULT_RADIUS_RATIO
    if radius < 0:
        print("Error: Radius cannot be negative.")
        sys.exit(1)

    # Print summary
    log(f"Input:  {input_path}", quiet)
    log(f"Radius: {radius}{' (ratio)' if radius <= 1 else ' (pixels)'}", quiet)
    for ext, out_path in outputs:
        log(f"Output: {out_path} (sizes: {', '.join(str(s) for s in sizes_map[ext])})", quiet)
    log("", quiet)

    try:
        for ext, out_path in outputs:
            sizes = sizes_map[ext]
            if ext == ".ico":
                convert_to_ico(input_path, out_path, sizes, radius, quiet)
            elif ext == ".icns":
                convert_to_icns(input_path, out_path, sizes, radius, quiet)

        log(f"\nIcon generation completed! ({len(outputs)} file(s) created)", quiet)
    except Exception as e:
        print(f"Error: Failed to generate icon: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
