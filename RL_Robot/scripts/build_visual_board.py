from __future__ import annotations

import argparse
import json
from pathlib import Path

import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a static and HTML visual board.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--comparison-dir", required=True)
    parser.add_argument("--curriculum-dir", required=True)
    parser.add_argument("--scenario-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir)
    comparison_dir = Path(args.comparison_dir)
    curriculum_dir = Path(args.curriculum_dir)
    scenario_dir = Path(args.scenario_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = _load_json(run_dir / "eval" / "summary.json")
    metadata = _load_json(run_dir / "metadata.json")

    poster_path = output_dir / "visual_board.png"
    _build_poster(
        poster_path,
        summary=summary,
        metadata=metadata,
        comparison_dir=comparison_dir,
        curriculum_dir=curriculum_dir,
        scenario_dir=scenario_dir,
    )
    _build_html(
        output_dir / "index.html",
        poster_path=poster_path,
        summary=summary,
        metadata=metadata,
        comparison_dir=comparison_dir,
        curriculum_dir=curriculum_dir,
        scenario_dir=scenario_dir,
    )
    print(poster_path)
    print(output_dir / "index.html")


def _build_poster(
    output_path: Path,
    *,
    summary: dict,
    metadata: dict,
    comparison_dir: Path,
    curriculum_dir: Path,
    scenario_dir: Path,
) -> None:
    canvas = Image.new("RGB", (2400, 3200), "#f7f8fb")
    draw = ImageDraw.Draw(canvas)
    title_font = _font(64)
    header_font = _font(36)
    body_font = _font(28)
    small_font = _font(22)

    draw.text((80, 60), "Robot Arm RL: SAC Curriculum Results", fill="#132238", font=title_font)
    draw.text(
        (80, 145),
        "Reward shaping fix: capped lift reward + height overshoot penalty",
        fill="#41516a",
        font=body_font,
    )

    metric_cards = [
        ("Eval pick success", f"{summary.get('pick_success_rate', 0.0) * 100:.0f}%"),
        ("Goal success", f"{summary.get('goal_success_rate', 0.0) * 100:.0f}%"),
        ("Collisions", f"{summary.get('total_collision_count', 0)}"),
        ("Actual steps", f"{metadata.get('total_timesteps', 0):,}"),
        ("Requested steps", f"{metadata.get('requested_total_timesteps', 0):,}"),
        ("Mean reward", f"{summary.get('mean_reward', 0.0):.1f}"),
    ]
    x = 80
    y = 230
    for index, (label, value) in enumerate(metric_cards):
        card_x = x + (index % 3) * 760
        card_y = y + (index // 3) * 170
        _rounded_rect(draw, (card_x, card_y, card_x + 700, card_y + 130), "#ffffff", "#dde3ee")
        draw.text((card_x + 28, card_y + 20), label, fill="#526174", font=small_font)
        draw.text((card_x + 28, card_y + 58), value, fill="#0d1b2f", font=header_font)

    graph_specs = [
        ("Learning Progress", curriculum_dir / "progress_eval_snapshots.png"),
        ("Reward vs Steps", comparison_dir / "timestep_reward.png"),
        ("Reward Components", comparison_dir / "entity_reward_components.png"),
        ("Algorithm/Reward Comparison", comparison_dir / "algorithm_reward_comparison.png"),
        ("Success and Collisions", comparison_dir / "success_collision_over_time.png"),
        ("Step Trace Diagnostics", curriculum_dir / "step_trace_diagnostics.png"),
    ]
    positions = [
        (80, 600),
        (1240, 600),
        (80, 1260),
        (1240, 1260),
        (80, 1920),
        (1240, 1920),
    ]
    for (title, path), position in zip(graph_specs, positions):
        _draw_panel(canvas, title, path, position, (1080, 560), header_font, small_font)

    draw.text((80, 2580), "Video Evidence", fill="#132238", font=header_font)
    video_specs = [
        ("training progress", curriculum_dir / "videos" / "training_progress_sequence.mp4"),
        ("air goal grid", scenario_dir / "final_model_air_goals_grid.mp4"),
        ("six fixed goals", scenario_dir / "final_model_goal_scenarios_sequence.mp4"),
    ]
    for index, (label, path) in enumerate(video_specs):
        frame = _video_frame(path)
        box_x = 80 + index * 760
        box_y = 2640
        _rounded_rect(draw, (box_x, box_y, box_x + 700, box_y + 430), "#ffffff", "#dde3ee")
        if frame is not None:
            thumb = _fit(frame, (660, 350))
            canvas.paste(thumb, (box_x + 20, box_y + 20))
        draw.text((box_x + 20, box_y + 382), label, fill="#132238", font=body_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, quality=95)


def _build_html(
    output_path: Path,
    *,
    poster_path: Path,
    summary: dict,
    metadata: dict,
    comparison_dir: Path,
    curriculum_dir: Path,
    scenario_dir: Path,
) -> None:
    rel = lambda path: Path(path).resolve().as_uri()
    graphs = [
        ("Learning progress", curriculum_dir / "progress_eval_snapshots.png"),
        ("Reward over timesteps", comparison_dir / "timestep_reward.png"),
        ("Entity reward components", comparison_dir / "entity_reward_components.png"),
        ("Algorithm/reward comparison", comparison_dir / "algorithm_reward_comparison.png"),
        ("Success and collisions", comparison_dir / "success_collision_over_time.png"),
        ("Step trace diagnostics", curriculum_dir / "step_trace_diagnostics.png"),
    ]
    videos = [
        ("Training progress sequence", curriculum_dir / "videos" / "training_progress_sequence.mp4"),
        ("Four air-goal final model grid", scenario_dir / "final_model_air_goals_grid.mp4"),
        ("Four air goals + two table goals", scenario_dir / "final_model_goal_scenarios_sequence.mp4"),
        ("GIF version", scenario_dir / "final_model_goal_scenarios_sequence.gif"),
    ]

    graph_html = "\n".join(
        f"<section><h2>{title}</h2><img src=\"{rel(path)}\" /></section>" for title, path in graphs
    )
    video_html = "\n".join(
        _media_block(title, path, rel(path)) for title, path in videos
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Robot Arm RL Visual Board</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f7f8fb; color: #132238; }}
    main {{ max-width: 1400px; margin: 0 auto; padding: 36px; }}
    header {{ margin-bottom: 24px; }}
    h1 {{ margin: 0 0 8px; font-size: 42px; }}
    h2 {{ margin: 0 0 14px; font-size: 24px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 22px 0; }}
    .card, section {{ background: white; border: 1px solid #dde3ee; border-radius: 8px; padding: 16px; }}
    .card strong {{ display: block; font-size: 28px; margin-top: 6px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; }}
    img, video {{ width: 100%; border-radius: 6px; }}
    .videos {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; margin-top: 18px; }}
    .poster {{ margin: 18px 0; }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>Robot Arm RL Visual Board</h1>
    <p>SAC curriculum with capped lift reward and height overshoot penalty.</p>
  </header>
  <div class="metrics">
    <div class="card">Pick success<strong>{summary.get('pick_success_rate', 0) * 100:.0f}%</strong></div>
    <div class="card">Goal success<strong>{summary.get('goal_success_rate', 0) * 100:.0f}%</strong></div>
    <div class="card">Collisions<strong>{summary.get('total_collision_count', 0)}</strong></div>
    <div class="card">Steps used<strong>{metadata.get('total_timesteps', 0):,}</strong></div>
  </div>
  <section class="poster"><h2>Static overview board</h2><img src="{rel(poster_path)}" /></section>
  <div class="grid">{graph_html}</div>
  <div class="videos">{video_html}</div>
</main>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


def _media_block(title: str, path: Path, src: str) -> str:
    if path.suffix.lower() == ".gif":
        return f"<section><h2>{title}</h2><img src=\"{src}\" /></section>"
    return f"<section><h2>{title}</h2><video src=\"{src}\" controls muted loop></video></section>"


def _draw_panel(
    canvas: Image.Image,
    title: str,
    path: Path,
    xy: tuple[int, int],
    size: tuple[int, int],
    header_font,
    small_font,
) -> None:
    draw = ImageDraw.Draw(canvas)
    x, y = xy
    w, h = size
    _rounded_rect(draw, (x, y, x + w, y + h), "#ffffff", "#dde3ee")
    draw.text((x + 24, y + 20), title, fill="#132238", font=header_font)
    if path.exists():
        image = Image.open(path).convert("RGB")
        fitted = _fit(image, (w - 48, h - 92))
        canvas.paste(fitted, (x + 24, y + 74))
    else:
        draw.text((x + 24, y + 86), f"Missing: {path}", fill="#9b1c31", font=small_font)


def _fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    result = image.copy()
    result.thumbnail(size, Image.Resampling.LANCZOS)
    return result


def _video_frame(path: Path) -> Image.Image | None:
    if not path.exists():
        return None
    reader = imageio.get_reader(path)
    try:
        candidate = None
        for index, frame in enumerate(reader):
            if index > 160:
                break
            image = Image.fromarray(frame[:, :, :3]).convert("RGB")
            if candidate is None:
                candidate = image
            gray = image.convert("L")
            extrema = gray.getextrema()
            mean_signal = sum(gray.resize((1, 1)).getpixel((0, 0)) for _ in range(1))
            if extrema[1] - extrema[0] > 35 and mean_signal < 238:
                return image
        return candidate
    except Exception:
        return None
    finally:
        reader.close()


def _rounded_rect(draw: ImageDraw.ImageDraw, box, fill: str, outline: str) -> None:
    draw.rounded_rectangle(box, radius=18, fill=fill, outline=outline, width=2)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _font(size: int):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


if __name__ == "__main__":
    main()
