#!/usr/bin/python3
import argparse
from get_alignment import get_alignment
from util import write_file


def extract_itempo_forwards(alignment):
    data = []

    average_tatum_time = alignment[-1]['time']/alignment[-1]['tatum']

    last_tatum = alignment[0]['tatum'] # Last valid tatum (inferior to current)
    last_time = alignment[0]['time'] # 
    current_tatum = last_tatum
    current_time = last_time
    for next_item in alignment[1:]:
        next_tatum = next_item['tatum']
        next_time = next_item['time']
        if next_tatum < current_tatum:
            continue # Alignment crosses itself
        elif next_tatum == current_tatum:
            current_time = next_time
            if current_tatum == last_tatum: # Should only happen in the first iterations
                continue
        else:
            last_tatum = current_tatum
            last_time = current_time
            current_tatum = next_tatum
            current_time = next_time
        datum = next_item.copy()
        datum['itempo'] = (next_tatum-last_tatum)/(next_time-last_time)*average_tatum_time
        data.append(datum)
    return data

def extract_itempo_backwards(alignment):
    data = []

    average_tatum_time = alignment[-1]['time']/alignment[-1]['tatum']

    last_tatum = alignment[-1]['tatum'] # Last valid tatum (inferior to current)
    last_time = alignment[-1]['time'] # 
    current_tatum = last_tatum
    current_time = last_time
    for next_item in reversed(alignment[1:]):
        next_tatum = next_item['tatum']
        next_time = next_item['time']
        if next_tatum > current_tatum:
            continue # Alignment crosses itself
        elif next_tatum == current_tatum:
            current_time = next_time
            if current_tatum == last_tatum: # Should only happen in the first iterations
                continue
        else:
            last_tatum = current_tatum
            last_time = current_time
            current_tatum = next_tatum
            current_time = next_time
        datum = next_item.copy()
        datum['itempo'] = (next_tatum-last_tatum)/(next_time-last_time)*average_tatum_time
        data.append(datum)
    return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', default='test_midi/Chopin_Ballade_No._2_Piano_solo.mscz')
    parser.add_argument('--perf', default='test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')
    parser.add_argument('--quarter', default=None)
    parser.add_argument('--offset', default=None)
    args = parser.parse_args()
    
    alignment = get_alignment(ref_path=args.ref, perf_path=args.perf,cleanup=False)

    data_backwards = extract_itempo_backwards(alignment)[:]
    data_forwards = extract_itempo_forwards(alignment)

    write_file("itempoForward.csv",data_forwards)
    write_file("itempoBackward.csv",data_backwards)
