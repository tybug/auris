import threading
from pathlib import Path

import pyaudio
from pyaudio import PyAudio
import numpy as np
from pydub import AudioSegment


class Audio:
    def __init__(self, path: Path, mod):
        self.track = 0
        self.audio = AudioSegment.from_file(path)
        self.mod = mod

        self._pyaudio = PyAudio()
        self._pyaudio_stream = None

        self.increment_track_flag = threading.Event()

    def prepare_audio(self):
        samples = np.array(self.audio.get_array_of_samples())

        if self.audio.channels == 2:
            left = samples[::2]
            right = samples[1::2]
        else:
            # mono audio (probably?)
            left = samples
            right = samples

        return (
            np.column_stack((left, right)).astype(np.float32)
            / np.iinfo(samples.dtype).max
        )

    def audio_callback(self, in_data, frame_count, time_info, status):
        if self.increment_track_flag.is_set():
            self.track = (self.track + 1) % 2
            self.increment_track_flag.clear()

        chunk = self.stereo[:frame_count]
        self.stereo = self.stereo[frame_count:]

        if len(chunk) < frame_count:
            # replay from beginning
            self.stereo = self.original_stereo.copy()
            chunk = np.pad(
                chunk, ((0, frame_count - len(chunk)), (0, 0)), mode="constant"
            )

        chunk = self.mod(chunk.copy(), track=self.track)
        return (chunk.tobytes(), pyaudio.paContinue)

    def start_playback(self):
        self.original_stereo = self.prepare_audio()
        self.stereo = self.original_stereo.copy()

        pyaudio_stream = self._pyaudio.open(
            format=pyaudio.paFloat32,
            channels=2,
            rate=self.audio.frame_rate,
            output=True,
            stream_callback=self.audio_callback,
        )

        pyaudio_stream.start_stream()

    def stop(self):
        if self._pyaudio_stream is not None:
            self._pyaudio_stream.stop_stream()
            self._pyaudio_stream.close()
            self._pyaudio_stream = None
        self._pyaudio.terminate()

    def run(self):
        self.start_playback()
        try:
            while True:
                input("press enter to increment track")
                self.increment_track_flag.set()
        finally:
            self.stop()


class Auris:
    def __init__(self, path):
        def lr(chunk, *, track):
            chunk[:, track] = 0
            return chunk

        def pan(chunk, *, track):
            if track == 0:
                return chunk

            pan = -0.1
            chunk[:, 0] *= 1 - max(0, pan)
            chunk[:, 1] *= 1 + min(0, pan)
            return chunk

        self.audio = Audio(path, mod=lr)

    def run(self):
        self.audio.run()

    def run_tournament(self):
        min_pan = -1
        max_pan = 1


song_path = input("enter song path: ")
# drag and dropped files include leading and trailing quotes in their path in
# the vscode terminal, so strip if present
song_path = song_path.strip("'")
auris = Auris(song_path)
auris.run()
