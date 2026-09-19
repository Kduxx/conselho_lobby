#!/usr/bin/env python3

from pathlib import Path
from PIL import Image

# Folder containing the original CozyTown_AssetPack directory
SOURCE_DIR = Path("CozyTown_AssetPack")

# Output directory
OUTPUT_DIR = SOURCE_DIR.parent / f"{SOURCE_DIR.name}_2x"

# Scale factor
SCALE = 2

# Image formats we want to process
IMAGE_EXTENSIONS = {
    ".png",
    ".gif",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}


def resize_image(image: Image.Image) -> Image.Image:
    """Resize an image using nearest-neighbor scaling."""
    new_size = (
        image.width * SCALE,
        image.height * SCALE,
    )

    return image.resize(
        new_size,
        resample=Image.Resampling.NEAREST,
    )


def process_static_image(source: Path, destination: Path) -> None:
    """Process a normal non-animated image."""
    with Image.open(source) as img:
        resized = resize_image(img)

        destination.parent.mkdir(parents=True, exist_ok=True)

        # Preserve PNG transparency and generally sensible output settings.
        save_kwargs = {}

        if destination.suffix.lower() == ".png":
            save_kwargs["optimize"] = True

        resized.save(destination, **save_kwargs)


def process_gif(source: Path, destination: Path) -> None:
    """Resize every frame of an animated GIF."""
    with Image.open(source) as img:
        frames = []
        durations = []
        disposals = []

        try:
            frame_count = img.n_frames
        except EOFError:
            frame_count = 1

        for frame_index in range(frame_count):
            img.seek(frame_index)

            # Convert to RGBA so transparency is handled correctly.
            frame = img.convert("RGBA")
            resized_frame = resize_image(frame)

            frames.append(resized_frame)
            durations.append(img.info.get("duration", 100))
            disposals.append(img.info.get("disposal", 0))

        destination.parent.mkdir(parents=True, exist_ok=True)

        if len(frames) == 1:
            frames[0].save(
                destination,
                format="GIF",
                optimize=True,
            )
            return

        # GIF requires palette-based frames.
        palette_frames = [
            frame.convert("P", palette=Image.Palette.ADAPTIVE)
            for frame in frames
        ]

        palette_frames[0].save(
            destination,
            format="GIF",
            save_all=True,
            append_images=palette_frames[1:],
            duration=durations,
            loop=img.info.get("loop", 0),
            disposal=disposals,
            optimize=False,
        )


def main() -> None:
    if not SOURCE_DIR.exists():
        raise SystemExit(
            f"ERROR: Source directory does not exist:\n{SOURCE_DIR.resolve()}"
        )

    print(f"Source : {SOURCE_DIR.resolve()}")
    print(f"Output : {OUTPUT_DIR.resolve()}")
    print(f"Scale  : {SCALE}x")
    print()

    processed = 0
    skipped = 0
    failed = 0

    for source in SOURCE_DIR.rglob("*"):
        if not source.is_file():
            continue

        # Skip anything that isn't an image.
        if source.suffix.lower() not in IMAGE_EXTENSIONS:
            skipped += 1
            continue

        # Preserve the complete directory structure.
        relative_path = source.relative_to(SOURCE_DIR)
        destination = OUTPUT_DIR / relative_path

        try:
            print(f"Scaling: {relative_path}")

            if source.suffix.lower() == ".gif":
                process_gif(source, destination)
            else:
                process_static_image(source, destination)

            processed += 1

        except Exception as exc:
            failed += 1
            print(f"  FAILED: {exc}")

    print()
    print("Done.")
    print(f"Processed: {processed}")
    print(f"Skipped  : {skipped}")
    print(f"Failed   : {failed}")
    print()
    print(f"Output directory:")
    print(OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
