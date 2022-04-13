"""Installation script for music_features/COSMOS_Analysis."""
import os
import shutil
import subprocess

from setuptools import setup


def build_alignment(build_dir="build",
                    bin_dir="build/lib/music_features/bin",
                    src_dir="redist/AlignmentTool/Code"):

    # TODO: Handle missing cmake gracefully
    os.makedirs(build_dir, exist_ok=True)
    subprocess.run(["cmake", "-S", src_dir, "-B", build_dir])
    subprocess.run(["cmake", "--build", build_dir])

    os.makedirs(bin_dir, exist_ok=True)
    exe_list = ("ErrorDetection", "RealignmentMOHMM", "ScorePerfmMatcher", "midi2pianoroll",
                "MusicXMLToFmt3x", "MusicXMLToHMM", "SprToFmt3x", "Fmt3xToHmm", "MatchToCorresp")

    for exe in exe_list:
        shutil.move(os.path.join(build_dir, exe), os.path.join(bin_dir, exe))


build_alignment()


setup()
