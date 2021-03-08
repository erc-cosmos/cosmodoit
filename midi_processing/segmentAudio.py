#!/usr/bin/python3

import csv
import os.path
import argparse
from pydub import AudioSegment

def readMetafile(filename):
    with open(filename) as metafile:
        reader = csv.reader(metafile)
        next(reader) #Skip header
        return list(reader)

def extractPieceName(filename):
    base = os.path.basename(filename)
    name,_ext = os.path.splitext(base)
    return name

def splitAudio(audiofile, metafile, outDir, offset):
    meta = readMetafile(metafile)
    audio = AudioSegment.from_wav(audiofile)
    for (filename, start, end) in meta:
        start=1000*float(start) + offset
        end=1000*float(end) + offset
        print(f"split at [{start}:{end}] ms")
        audio_chunk=audio[start:end]
        pieceName = extractPieceName(filename)
        audio_chunk.export( f"{outDir}/{pieceName}.wav", format="wav")


if __name__== "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta")
    parser.add_argument("--audio")
    parser.add_argument("--output", default="./")
    parser.add_argument("--offset", default=513, type=int)
    args = parser.parse_args()

    splitAudio(args.audio,args.meta,args.output, args.offset)