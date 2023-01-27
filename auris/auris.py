from enum import Enum
from time import perf_counter

from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio

class Side(Enum):
    LEFT = "left"
    RIGHT = "right"

    @classmethod
    def _missing_(cls, value):
        if value == "l":
            return Side.LEFT
        if value == "r":
            return Side.RIGHT
        return super()._missing_(value)

    def opposite(self):
        return Side.LEFT if self is Side.RIGHT else Side.RIGHT

class Auris:
    def __init__(self, song_path):
        self.song = AudioSegment.from_mp3(song_path)

        # convert to mono, we'll play this on only the left or only the right
        # channels later
        mono_song = self.song. set_channels(1)
        silent = AudioSegment.silent(
            duration=self.song.duration_seconds * 1000,
            frame_rate=self.song.frame_rate
        )
        self.left_stereo = AudioSegment.from_mono_audiosegments(
            mono_song, silent)
        self.right_stereo = AudioSegment.from_mono_audiosegments(
            silent, mono_song)

    def play(self, side, *, ms=0):
        side = Side(side)
        song = self.left_stereo if side is Side.LEFT else self.right_stereo
        song = song[ms:]
        # simpleaudio handles threading for us and allows us to stop playback at
        # any time, which is why I chose it
        return _play_with_simpleaudio(song)

    def alternate_sides(self):
        # default to right side first, no particular reason why
        side = Side.RIGHT
        # track elapsed time so we can seamlessly switch between left and right
        # segments
        start = perf_counter()
        while True:
            # perf_counter is in seconds, convert to ms
            elapsed = (perf_counter() - start) * 1000
            playback = self.play(side, ms=elapsed)
            input("press enter to switch sides ")
            playback.stop()
            side = side.opposite()

song_path = input("enter song path: ")
# drag and dropped files include leading and trailing quotes in their path in
# the vscode terminal, so strip if present
song_path = song_path.strip("'")
auris = Auris(song_path)
auris.alternate_sides()
