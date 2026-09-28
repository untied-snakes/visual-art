"""Audio in, numbers out. Visuals only ever see an AudioFrame."""
from dataclasses import dataclass

import numpy as np
import sounddevice as sd

BLOCK_SIZE = 1024


@dataclass
class AudioFrame:
    samples: np.ndarray    # the raw audio block, mono, floats -1..1
    spectrum: np.ndarray   # FFT magnitudes, low -> high frequency
    volume: float          # overall loudness
    bass: float            # ~20-250 Hz
    mids: float            # ~250-4000 Hz
    highs: float           # ~4000 Hz and up


def silence() -> AudioFrame:
    """An AudioFrame with nothing in it."""
    return analyze(np.zeros(BLOCK_SIZE, dtype=np.float32), 44100)


# Loudness numbers are scaled so loud music reads about 1. Raw levels are much
# smaller than that, and highs carry far less energy than bass in most music.
VOLUME_SCALE = 3.0
BASS_SCALE = 3.0
MIDS_SCALE = 5.0
HIGHS_SCALE = 12.0


def analyze(samples: np.ndarray, samplerate: int) -> AudioFrame:
    """Turn one block of mono samples into an AudioFrame."""
    window = np.hanning(len(samples))
    fft = np.fft.rfft(samples * window)
    spectrum = np.abs(fft) / len(samples)
    freqs = np.fft.rfftfreq(len(samples), 1 / samplerate)
    power = np.abs(fft) ** 2 * 2 / (len(samples) * np.sum(window**2))

    def band(low: float, high: float, scale: float) -> float:
        """How loud the sound is between low and high Hz (RMS), scaled to ~0..1."""
        in_band = (freqs >= low) & (freqs < high)
        return min(1.0, float(np.sqrt(power[in_band].sum())) * scale)

    return AudioFrame(
        samples=samples,
        spectrum=spectrum,
        volume=min(1.0, float(np.sqrt(np.mean(samples**2))) * VOLUME_SCALE),
        bass=band(20, 250, BASS_SCALE),
        mids=band(250, 4000, MIDS_SCALE),
        highs=band(4000, samplerate / 2, HIGHS_SCALE),
    )


class AudioInput:
    """Live audio from a microphone or interface."""

    def __init__(self, device=None, gain: float = 1.0, samplerate: int = 44100) -> None:
        self.device = device
        self.gain = gain
        self.samplerate = samplerate
        self.latest = np.zeros(BLOCK_SIZE, dtype=np.float32)
        self.stream = None

    def start(self) -> None:
        self.stream = sd.InputStream(
            device=self.device,
            channels=1,
            samplerate=self.samplerate,
            blocksize=BLOCK_SIZE,
            callback=self._callback,
        )
        self.stream.start()

    def stop(self) -> None:
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def read(self) -> AudioFrame:
        return analyze(self.latest * self.gain, self.samplerate)

    def _callback(self, indata, frames, time, status) -> None:
        # Runs on sounddevice's thread. Only copy; do the math in read().
        self.latest = indata[:, 0].copy()
