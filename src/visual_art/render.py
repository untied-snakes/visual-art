"""Audio file in, MP4 out. Drives a Show frame by frame, with no window."""
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import pygame
import soundfile

from visual_art.audio import BLOCK_SIZE, analyze
from visual_art.show import Show


def render(
    audio_path: Path,
    out_path: Path,
    show: Show,
    width: int,
    height: int,
    fps: int = 30,
    include_audio: bool = True,
) -> None:
    samples, samplerate = soundfile.read(audio_path, dtype="float32", always_2d=True)
    mono = samples.mean(axis=1)
    total_frames = int(len(mono) / samplerate * fps)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = subprocess.Popen(
        _ffmpeg_command(audio_path, out_path, width, height, fps, include_audio),
        stdin=subprocess.PIPE,
    )

    surface = pygame.Surface((width, height))
    dt = 1 / fps
    try:
        for i in range(total_frames):
            # The block of samples ending at this frame's time.
            end = int(i * dt * samplerate)
            block = mono[max(0, end - BLOCK_SIZE):end]
            block = np.pad(block, (BLOCK_SIZE - len(block), 0))
            show.step(analyze(block, samplerate), dt, surface)
            ffmpeg.stdin.write(pygame.image.tobytes(surface, "RGB"))
            if i % fps == 0:
                print(f"\r  {i // fps}s / {total_frames // fps}s", end="", flush=True)
    finally:
        ffmpeg.stdin.close()
        ffmpeg.wait()
    print()
    if ffmpeg.returncode != 0:
        raise RuntimeError(f"ffmpeg failed with exit code {ffmpeg.returncode}")


def _ffmpeg_command(audio_path, out_path, width, height, fps, include_audio) -> list[str]:
    """H.264 + AAC in MP4, with settings every projector and TV can play. See PLAN.md."""
    command = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
    ]
    if include_audio:
        command += ["-i", str(audio_path), "-map", "0:v", "-map", "1:a", "-shortest"]
    command += [
        "-c:v", "libx264", "-profile:v", "high", "-level", "4.1", "-preset", "slow",
        "-crf", "18", "-maxrate", "12M", "-bufsize", "24M", "-g", str(fps * 2),
        # Convert RGB with HD (bt709) colour maths, and label the file to match.
        "-vf", "scale=out_color_matrix=bt709:out_range=tv", "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-x264-params", "colorprim=bt709:transfer=bt709:colormatrix=bt709",
    ]
    if include_audio:
        command += ["-c:a", "aac", "-ar", "48000", "-b:a", "192k"]
    command += ["-movflags", "+faststart", str(out_path)]
    return command
