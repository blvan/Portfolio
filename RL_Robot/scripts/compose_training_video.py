from __future__ import annotations

import argparse
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose multiple policy clips into one video.")
    parser.add_argument("--clips", nargs="+", required=True, help="Input MP4/GIF clips.")
    parser.add_argument("--labels", nargs="*", default=None, help="Labels for clips.")
    parser.add_argument("--output", required=True, help="Output MP4/GIF path.")
    parser.add_argument("--layout", choices=["sequence", "grid"], default="sequence")
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--title-seconds", type=float, default=0.8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    clips = [Path(path) for path in args.clips]
    labels = args.labels or [path.stem for path in clips]
    if len(labels) != len(clips):
        raise SystemExit("--labels must have the same length as --clips.")

    frame_sets = [_load_clip(path) for path in clips]
    if not frame_sets or any(len(frames) == 0 for frames in frame_sets):
        raise SystemExit("At least one clip has no frames.")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.layout == "grid":
        frames = _compose_grid(frame_sets, labels)
    else:
        frames = _compose_sequence(frame_sets, labels, fps=args.fps, title_seconds=args.title_seconds)

    _save(frames, output_path, fps=args.fps)
    print(output_path)


def _load_clip(path: Path) -> list[np.ndarray]:
    reader = imageio.get_reader(path)
    try:
        return [np.asarray(frame[:, :, :3], dtype=np.uint8) for frame in reader]
    finally:
        reader.close()


def _compose_sequence(
    frame_sets: list[list[np.ndarray]],
    labels: list[str],
    *,
    fps: int,
    title_seconds: float,
) -> list[np.ndarray]:
    frames: list[np.ndarray] = []
    base_shape = frame_sets[0][0].shape
    for label, clip_frames in zip(labels, frame_sets):
        resized = [_resize_to(frame, base_shape) for frame in clip_frames]
        title_frame = _label_frame(np.zeros_like(resized[0]) + 245, label, dark_text=True)
        frames.extend([title_frame.copy() for _ in range(max(1, int(title_seconds * fps)))])
        frames.extend(_overlay_label(frame, label) for frame in resized)
    return frames


def _compose_grid(frame_sets: list[list[np.ndarray]], labels: list[str]) -> list[np.ndarray]:
    rows = 2
    cols = 2
    cell_shape = frame_sets[0][0].shape
    target_len = max(len(frames) for frames in frame_sets)
    padded_sets = []
    for frames in frame_sets[: rows * cols]:
        resized = [_resize_to(frame, cell_shape) for frame in frames]
        if len(resized) < target_len:
            resized.extend([resized[-1].copy() for _ in range(target_len - len(resized))])
        padded_sets.append(resized)

    while len(padded_sets) < rows * cols:
        padded_sets.append([np.zeros_like(padded_sets[0][0]) + 245 for _ in range(target_len)])

    composed = []
    h, w = cell_shape[:2]
    for frame_index in range(target_len):
        canvas = np.zeros((h * rows, w * cols, 3), dtype=np.uint8) + 245
        for clip_index, frames in enumerate(padded_sets):
            row = clip_index // cols
            col = clip_index % cols
            label = labels[clip_index] if clip_index < len(labels) else ""
            frame = _overlay_label(frames[frame_index], label)
            canvas[row * h : (row + 1) * h, col * w : (col + 1) * w] = frame
        composed.append(canvas)
    return composed


def _resize_to(frame: np.ndarray, shape: tuple[int, int, int]) -> np.ndarray:
    if frame.shape == shape:
        return frame
    image = Image.fromarray(frame)
    return np.asarray(image.resize((shape[1], shape[0]), Image.Resampling.LANCZOS), dtype=np.uint8)


def _overlay_label(frame: np.ndarray, label: str) -> np.ndarray:
    image = Image.fromarray(frame).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _font(max(18, image.width // 28))
    box_height = max(44, image.height // 13)
    draw.rectangle((0, 0, image.width, box_height), fill=(0, 0, 0, 150))
    draw.text((18, max(8, box_height // 4)), label, fill=(255, 255, 255, 255), font=font)
    return np.asarray(Image.alpha_composite(image, overlay).convert("RGB"), dtype=np.uint8)


def _label_frame(frame: np.ndarray, label: str, *, dark_text: bool) -> np.ndarray:
    image = Image.fromarray(frame).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = _font(max(24, image.width // 18))
    color = (17, 32, 51) if dark_text else (255, 255, 255)
    bbox = draw.textbbox((0, 0), label, font=font)
    x = (image.width - (bbox[2] - bbox[0])) // 2
    y = (image.height - (bbox[3] - bbox[1])) // 2
    draw.text((x, y), label, fill=color, font=font)
    return np.asarray(image, dtype=np.uint8)


def _font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def _save(frames: list[np.ndarray], output_path: Path, *, fps: int) -> None:
    if output_path.suffix.lower() == ".gif":
        imageio.mimsave(output_path, frames, fps=fps)
        return
    imageio.mimsave(
        output_path,
        frames,
        fps=fps,
        codec="libx264",
        quality=8,
        macro_block_size=16,
    )


if __name__ == "__main__":
    main()
