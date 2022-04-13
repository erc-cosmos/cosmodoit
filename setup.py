"""Installation script for music_features/COSMOS_Analysis."""
import os
import shutil
import subprocess

from setuptools import setup


def build_alignment(build_dir="build",
                    bin_dir="build/lib/music_features/bin",
                    src_dir="redist/AlignmentTool/Code"):

    os.makedirs(build_dir, exist_ok=True)
    subprocess.run(["cmake", "-S", src_dir, "-B", build_dir])
    subprocess.run(["cmake", "--build", build_dir])

    os.makedirs(bin_dir, exist_ok=True)
    exe_list = ("ErrorDetection", "RealignmentMOHMM", "ScorePerfmMatcher", "midi2pianoroll",
                "MusicXMLToFmt3x", "MusicXMLToHMM", "SprToFmt3x", "Fmt3xToHmm", "MatchToCorresp")

    for exe in exe_list:
        shutil.move(os.path.join(build_dir, exe), os.path.join(bin_dir, exe))


build_alignment()


setup(
    name='COSMOS_Analysis',
    version='0.1.0',
    description='Tools suite for music perfomance analysis',
    # url='https://github.com/shuds13/pyexample',
    author='Corentin Guichaoua',
    author_email='corentin.guichaoau@ircam.fr',
    license='GNU GPLv3',
    packages=['music_features'],
    install_requires=[
        "doit>=0.35.0",
        "lowess>=1.0.3",
        "numpy>=1.22.3",
        "pandas>=1.4.2",
        "pretty_midi",
        "scipy",
        "matplotlib",
        "soundfile",
        "coloredlogs",
    ],
    entry_points={
        'console_scripts': ['cosmodoit = music_features.dodo:main']
    },
    package_data={'': ['*.json']},
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3.9',
    ],
)
