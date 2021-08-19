# MIDI Scrambler
# Takes .mid files as input, changes the pitches of their notes
# and exports .mid files as output

import os
import re
import math
import mido
import random
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy

def printMessages(midi):
    for i, track in enumerate(midi.tracks):
        print('Track {}: {}'.format(i, track.name))
        for msg in track:
            print(msg)
    return

def parseMsgStr(strMsg, metaBool):
    """ Generate a dictionary from a string MIDI message """

    attributes_dict = {'changed': False, 'meta':metaBool, 'type':strMsg[0]}    
    for item in strMsg[1:]:
        key, val = item.split("=")
        val = str2num(val)
        attributes_dict[key] = val
    return attributes_dict

def str2num(s):
    """ Convert string to number """

    try:
        if int(s) == float(s):
            num = int(s)
        else:
            num = float(s)
        return num
    except:
        return s

def genMsgList(midi):
    """ Create a list of dictionaries from MIDI messages """

    trackList = []
    for track in midi.tracks:
        msgList = []
        for msg in track:
            strMsg = str(msg)
            strMsg = strMsg.replace('<', '')
            strMsg = strMsg.replace('>', '') 
            splitMsg = strMsg.split(" ")
            if msg.is_meta:
                splitMsg = splitMsg[2:]
                msgDict = parseMsgStr(splitMsg, msg.is_meta)
                msgList.append(msgDict)
            else:
                msgDict = parseMsgStr(splitMsg, msg.is_meta)
                msgList.append(msgDict)
        trackList.append(msgList)
    return trackList

def genNewMsgList(trackList, lowNote=21, highNote=108):
    """ Parse a list with MIDI messages
    and replace the pitch of each note randomly"""

    newTrackList = []
    for msgList in trackList:
        newMsgList = deepcopy(msgList)
        N = len(newMsgList)
        for i, msg in enumerate(newMsgList):
            if msg['type'] == 'note_on' and msg['changed'] == False:
                currentNote = msg['note']
                # TO DO: Exclude the changed note from random list
                newNote = random.randint(lowNote, highNote)
                msg['note'] = newNote
                msg['changed'] = True
                for j in range(i+1,N):
                    if newMsgList[j]['type'] == 'note_on' and newMsgList[j]['note'] == currentNote:
                        if  newMsgList[j]['velocity'] == 0 and newMsgList[j]['changed'] == False:
                            newMsgList[j]['note'] = newNote
                            newMsgList[j]['changed'] = True
                            break # Find only the first value that matches
        newTrackList.append(newMsgList)
    return newTrackList

def writeNewMidi(midi, trackList, newFileName):
    """ Take a message list and write a new MIDI file """

    newMid   = mido.MidiFile()
    for i, track in enumerate(midi.tracks):
        newTrack = mido.MidiTrack()
        newMid.tracks.append(newTrack)
        msgList = trackList[i]
        for j, msg in enumerate(msgList):
            if msg['meta']:
                # TO DO: unpack dictionary values **dict
                newMsg = midi.tracks[i][j]
                newTrack.append(newMsg)
            else:
                current = msg.copy()
                current.pop('meta')
                current.pop('changed')
                newMsg = mido.Message.from_dict(current)
                newTrack.append(newMsg)
    newMid.save(newFileName)
    return

def changeNotePitch(inputFile, lowNote, highNote, exportMIDI):
    """ Take MIDI as input and  """
    midi = mido.MidiFile(inputFile)
    msgList = genMsgList(midi)
    newMsgList = genNewMsgList(msgList, lowNote, highNote)
    if exportMIDI:
        fullNewName = genExportName(inputFile)
        writeNewMidi(midi, newMsgList, fullNewName)
        print('exported to: {}'.format(fullNewName))
    return newMsgList

def genExportName(inputFile):
    """ Append '_modified' tag to new MIDI file """

    dirName      = os.path.dirname(inputFile)
    newFileName  = os.path.basename(inputFile).replace(".mid", "_modified.mid")
    fullNewName = os.path.join(dirName, newFileName)
    return fullNewName

def main(inputPath, lowNote, highNote, exportMIDI):
    """
    Randomly change pitch of MIDI file notes

     -inputPath,--var <arg>   Input path: .mid file or folder
     -l, lowNote. Integer number of lowest MIDI note to generate
     -h, highNote. Integer number of highest MIDI note to generate
     -exportMIDI,--var <arg>   bool, default True
    """

    if os.path.isfile(inputPath):
        newMIDI = changeNotePitch(inputPath, lowNote, highNote, exportMIDI)
        return newMIDI
    if os.path.isdir(inputPath):
        import glob
        fileList = glob.glob(os.path.join(inputPath, '*.mid'))
        for inputFile in fileList:
            newMIDI = changeNotePitch(inputPath, lowNote, highNote, exportMIDI)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('inputPath', type=str,
                        help="input MIDI file name or folder path with .mid files")
    parser.add_argument('-lo', '--lowNote', default=20, type=int,
                        help="MIDI number of the lowest note to generate")
    parser.add_argument('-hi', '--highNote', default=108, type=int,
                        help="MIDI number of the highest note to generate")
    parser.add_argument("-exp", "--exportMIDI", action='store_true', help="Export new MIDI file, default True", default=True)
    parser.add_argument("-noExp", "--dontExport", action='store_false', help="Do not export MIDI file", dest='exportMIDI')
    
    args = parser.parse_args()

    main(args.inputPath, lowNote=args.lowNote, highNote=args.highNote, exportMIDI=args.exportMIDI)