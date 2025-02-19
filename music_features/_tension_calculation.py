"""
Compute tension using the spiral array model.

Original code by R. Guo. Modified by D. Bedoya and C. Guichaoua.
"""

import copy
import itertools
import os

import matplotlib.pyplot as plt
import numpy as np
import pretty_midi

octave = 12

pitch_index_to_sharp_names = np.array(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G',
                                       'G#', 'A', 'A#', 'B'])


pitch_index_to_flat_names = np.array(['C', 'D-', 'D', 'E-', 'E', 'F', 'G-', 'G',
                                      'A-', 'A', 'B-', 'B'])


pitch_name_to_pitch_index = {"G-": -6, "D-": -5, "A-": -4, "E-": -3,
                             "B-": -2, "F": -1, "C": 0, "G": 1, "D": 2, "A": 3,
                             "E": 4, "B": 5, "F#": 6, "C#": 7, "G#": 8, "D#": 9,
                             "A#": 10}

pitch_index_to_pitch_name = {v: k for k, v in pitch_name_to_pitch_index.items()}

valid_major = ["G-", "D-", "A-", "E-", "B-", "F", "C", "G", "D", "A", "E", "B"]

valid_minor = ["E-", "B-", "F", "C", "G", "D", "A", "E", "B", "F#", "C#", "G#"]

enharmonic_dict = {"F#": "G-", "C#": "D-", "G#": "A-", "D#": "E-", "A#": "B-"}
enharmonic_reverse_dict = {v: k for k, v in enharmonic_dict.items()}

all_key_names = ['C major', 'G major', 'D major', 'A major',
                 'E major', 'B major', 'F major', 'B- major',
                 'E- major', 'A- major', 'D- major', 'G- major',
                 'A minor', 'E minor', 'B minor', 'F# minor',
                 'C# minor', 'G# minor', 'D minor', 'G minor',
                 'C minor', 'F minor', 'B- minor', 'E- minor',
                 ]


# use ['C','D-','D','E-','E','F','F#','G','A-','A','B-','B'] to map the midi to pitch name
note_index_to_pitch_index = [0, -5, 2, -3, 4, -1, -6, 1, -4, 3, -2, 5]

weight = np.array([0.536, 0.274, 0.19])
alpha = 0.75
beta = 0.75
verticalStep = np.sqrt(2/15)  # 0.4
radius = 1.0


def cal_diameter(piano_roll, key_index, key_change_beat=-1, changed_key_index=-1):

    diameters = []

    for i in range(0, piano_roll.shape[1]):
        indices = []
        for index, j in enumerate(piano_roll[:, i]):
            if j > 0:
                if i / 4 > key_change_beat and key_change_beat != -1:
                    shifted_index = index % 12 - changed_key_index
                    if shifted_index < 0:
                        shifted_index += 12
                else:
                    shifted_index = index % 12 - key_index
                    if shifted_index < 0:
                        shifted_index += 12

                indices.append(note_index_to_pitch_index[shifted_index])
        diameters.append(largest_distance(indices))

    return diameters


def largest_distance(pitches):
    if len(pitches) < 2:
        return 0
    diameter = 0
    pitch_pairs = itertools.combinations(pitches, 2)
    for pitch1, pitch2 in pitch_pairs:
        distance = np.linalg.norm(pitch_index_to_position(pitch1) - pitch_index_to_position(pitch2))
        if distance > diameter:
            diameter = distance
    return diameter


def piano_roll_to_ce(piano_roll, shift):

    pitch_index = []
    for i in range(0, piano_roll.shape[1]):
        indices = []
        for index, j in enumerate(piano_roll[:, i]):
            if j > 0:
                shifted_index = index % 12 - shift
                if shifted_index < 0:
                    shifted_index += 12

                indices.append(note_index_to_pitch_index[shifted_index])

        pitch_index.append(indices)

    ce_pos = ce_sum(pitch_index)
    return ce_pos


def notes_to_ce(notes, shift):
    indices = []

    for index, j in enumerate(notes):
        if j > 0:

            shifted_index = index % 12 - shift
            if shifted_index < 0:
                shifted_index += 12

            indices.append(note_index_to_pitch_index[shifted_index])

    total = np.zeros(3)
    count = 0
    for index in indices:
        total += pitch_index_to_position(index)
        count += 1

    if count != 0:
        total /= count
    return total


def pitch_index_to_position(pitch_index):

    c = pitch_index - (4 * (pitch_index // 4))

    pos = np.array([0.0, 0.0, 0.0])

    if c == 0:
        pos[1] = radius
    if c == 1:
        pos[0] = radius
    if c == 2:
        pos[1] = -1*radius
    if c == 3:
        pos[0] = -1*radius

    pos[2] = pitch_index * verticalStep
    return np.array(pos)


def ce_sum(indices, start=None, end=None):
    if not start:
        start = 0
    if not end:
        end = len(indices)

    indices = indices[start:end]
    total = np.zeros(3)
    count = 0
    for timestep, data in enumerate(indices):
        for pitch in data:
            total += pitch_index_to_position(pitch)
            count += 1
    return total/count


def major_triad_position(root_index):
    root_pos = pitch_index_to_position(root_index)

    fifth_index = root_index + 1
    third_index = root_index + 4

    fifth_pos = pitch_index_to_position(fifth_index)
    third_pos = pitch_index_to_position(third_index)

    centre_pos = weight[0] * root_pos + weight[1] * fifth_pos + weight[2] * third_pos
    return centre_pos


def minor_triad_position(root_index):
    root_pos = pitch_index_to_position(root_index)

    fifth_index = root_index + 1
    third_index = root_index - 3

    fifth_pos = pitch_index_to_position(fifth_index)
    third_pos = pitch_index_to_position(third_index)

    centre_pos = weight[0] * root_pos + weight[1] * fifth_pos + weight[2] * third_pos

    return centre_pos


def major_key_position(key_index):
    root_triad_pos = major_triad_position(key_index)
    fifth_index = key_index + 1

    fourth_index = key_index - 1

    fifth_triad_pos = major_triad_position(fifth_index)
    fourth_triad_pos = major_triad_position(fourth_index)

    key_pos = weight[0] * root_triad_pos + weight[1] * fifth_triad_pos + weight[2] * fourth_triad_pos

    return key_pos


def minor_key_position(key_index):

    root_triad_pos = minor_triad_position(key_index)
    fifth_index = key_index + 1
    fourth_index = key_index - 1
    major_fourth_triad_pos = major_triad_position(fourth_index)
    minor_fourth_triad_pos = minor_triad_position(fourth_index)

    major_fifth_triad_pos = major_triad_position(fifth_index)
    minor_fifth_triad_pos = minor_triad_position(fifth_index)

    key_pos = weight[0] * root_triad_pos + \
        weight[1] * (alpha * major_fifth_triad_pos +
                     (1-alpha) * minor_fifth_triad_pos) + \
        weight[2] * (beta * minor_fourth_triad_pos +
                     (1 - beta) * major_fourth_triad_pos)

    return key_pos


def cal_key(piano_roll, key_names, end_ratio=0.5):
    # use the song to the place of end_ratio to find the key
    # for classical it should be less than 0.2
    end = int(piano_roll.shape[1] * end_ratio)
    distances = []
    key_positions = []
    key_indices = []
    key_shifts = []
    for name in key_names:
        key, mode = name.split()

        def check_key(key, valid_for_mode):
            if key not in valid_for_mode:
                if key in enharmonic_dict:
                    key = enharmonic_dict[key]
                elif key in enharmonic_reverse_dict:
                    key = enharmonic_reverse_dict[key]
            if key not in valid_for_mode:
                raise KeyError(f'no such key: {name}')
            return key

        key = check_key(key, valid_minor if mode == 'minor' else valid_major)

        key_index = pitch_name_to_pitch_index[key]

        if mode == 'minor':
            # all the minor key_pos is a minor
            key_pos = minor_key_position(3)
        else:
            # all the major key_pos is C major
            key_pos = major_key_position(0)
        key_positions.append(key_pos)

        if mode == 'minor':
            key_index -= 3
        key_shift_name = pitch_index_to_pitch_name[key_index]

        if key_shift_name in pitch_index_to_sharp_names:
            key_shift_for_ce = np.argwhere(pitch_index_to_sharp_names == key_shift_name)[0][0]
        else:
            key_shift_for_ce = np.argwhere(pitch_index_to_flat_names == key_shift_name)[0][0]
        key_shifts.append(key_shift_for_ce)
        ce = piano_roll_to_ce(piano_roll[:, :end], key_shift_for_ce)
        distance = np.linalg.norm(ce - key_pos)
        distances.append(distance)
        key_indices.append(key_index)

    index = np.argmin(np.array(distances))
    key_name = key_names[index]
    key_pos = key_positions[index]
    key_shift_for_ce = key_shifts[index]
    # key_index = key_indices[index]
    return key_name, key_pos, key_shift_for_ce


def pianoroll_to_pitch(pianoroll):
    pitch_roll = np.zeros((12, pianoroll.shape[1]))
    for i in range(0, pianoroll.shape[0]-12+1, 12):
        pitch_roll = np.add(pitch_roll, pianoroll[i:i+octave])
    return np.transpose(pitch_roll)


def note_to_index(pianoroll):
    note_ind = np.zeros((128, pianoroll.shape[1]))
    for i in range(0, pianoroll.shape[1]):
        step = []
        for j, note in enumerate(pianoroll[:, i]):
            if note != 0:
                step.append(j)
        if len(step) > 0:
            note_ind[step[-1], i] = 1
    return np.transpose(note_ind)


def merge_tension(metric, beat_indices, down_beat_indices, window_size=-1):

    # every bar window
    if window_size == -1:

        new_metric = []

        for i in range(len(down_beat_indices)-1):
            new_metric.append(np.mean(metric[down_beat_indices[i]:down_beat_indices[i+1]], axis=0))

    else:
        new_metric = []

        for i in range(0, len(beat_indices) - window_size, window_size):
            new_metric.append(np.mean(metric[beat_indices[i]:beat_indices[i + window_size]], axis=0))

    return np.array(new_metric)


def moving_average(tension, window=4):

    # size moving window, the output size is the same
    outputs = []
    zeros = np.zeros((window,), dtype=tension.dtype)

    tension = np.concatenate([tension, zeros], axis=0)
    for i in range(0, tension.shape[0]-window+1):
        outputs.append(np.mean(tension[i:i+window]))
    return np.array(outputs)


def cal_tension(pm, piano_roll, beat_data, window_size=1, *,
                key_name=None, key_changed=False, end_ratio=0.5, **kwargs):
    # try:
    key_name = key_name or all_key_names
    # all the major key pos is C major pos, all the minor key pos is a minor pos
    key_name, key_pos, note_shift = cal_key(piano_roll, key_name, end_ratio)
    # bar_step = downbeat_indices[1] - downbeat_indices[0]
    centroids = cal_centroid(piano_roll, note_shift, -1, -1)

    kc = windowDetectKey(beat_data, centroids, key_pos, piano_roll, note_shift, end_ratio, pm, key_name, key_changed)

    centroids = cal_centroid(piano_roll, note_shift, kc['key_change_beat'], kc['changed_note_shift'])

    merged_centroids = merge_tension(
        centroids, beat_data['beat_indices'], beat_data['down_beat_indices'], window_size=window_size)
    merged_centroids = np.array(merged_centroids)

    window_time, total_tension = cal_key_diff(beat_data, window_size, merged_centroids, key_pos, kc)
    tension_time = window_time[:len(total_tension)]

    diameters = cal_diameter(piano_roll, note_shift, kc['key_change_beat'], kc['changed_note_shift'])
    diameters = merge_tension(diameters, beat_data['beat_indices'], beat_data['down_beat_indices'], window_size)

    centroid_diff = np.diff(merged_centroids, axis=0)
    np.nan_to_num(centroid_diff, copy=False)

    centroid_diff = np.linalg.norm(centroid_diff, axis=-1)
    centroid_diff = np.insert(centroid_diff, 0, 0)

    return (tension_time, total_tension, diameters, centroid_diff, key_name, kc)

    # except (ValueError, EOFError, IndexError, OSError, KeyError, ZeroDivisionError) as e:
    #     exception_str = 'Unexpected error in ' + file_name + ':\n', e, sys.exc_info()[0]
    #     logger.info(exception_str)


def cal_key_diff(beat_data, window_size, merged_centroids, key_pos, kc):

    if window_size == -1:
        window_time = beat_data['down_beat_time']
    else:
        beat_time = beat_data['beat_time']
        window_time = beat_time[::window_size]
    silent = np.where(np.linalg.norm(merged_centroids, axis=-1) == 0)

    if kc['key_change_beat'] != -1:
        key_diff = np.zeros(merged_centroids.shape[0])
        changed_step = int(kc['key_change_beat'] / abs(window_size))
        for step in range(merged_centroids.shape[0]):
            if step < changed_step:
                key_diff[step] = np.linalg.norm(merged_centroids[step] - key_pos)
            else:
                key_diff[step] = np.linalg.norm(merged_centroids[step] - kc['changed_key_pos'])
    else:
        key_diff = np.linalg.norm(merged_centroids - key_pos, axis=-1)

    key_diff[silent] = 0
    return window_time, key_diff


def windowDetectKey(beat_data, centroids, key_pos, piano_roll, note_shift, end_ratio, pm, key_name, key_changed):
    beat_indices = beat_data['beat_indices']
    down_beat_indices = beat_data['down_beat_indices']
    beat_time = beat_data['beat_time']
    down_beat_time = beat_data['down_beat_time']
    sixteenth_time = beat_data['sixteenth_time']

    if key_changed:
        # use a bar window to detect key change
        merged_centroids = merge_tension(centroids, beat_indices, down_beat_indices, window_size=-1)

        silent = np.where(np.linalg.norm(merged_centroids, axis=-1) == 0)
        merged_centroids = np.array(merged_centroids)

        key_diff = merged_centroids - key_pos
        key_diff = np.linalg.norm(key_diff, axis=-1)

        key_diff[silent] = 0

        diameters = cal_diameter(piano_roll, note_shift, -1, -1)
        diameters = merge_tension(diameters, beat_indices, down_beat_indices, window_size=-1)

        key_change_bar = detect_key_change(key_diff, diameters, start_ratio=end_ratio)
        if key_change_bar != -1:
            key_change_beat = np.argwhere(beat_time == down_beat_time[key_change_bar])[0][0]
            change_time = down_beat_time[key_change_bar]
            changed_key_name, changed_key_pos, changed_note_shift = get_key_index_change(
                pm, change_time, sixteenth_time)
            if changed_key_name == key_name:
                changed_note_shift = -1
                changed_key_name = ''
                key_change_beat = -1
                change_time = -1
                key_change_bar = -1

        else:
            changed_note_shift = -1
            changed_key_pos = ''
            changed_key_name = ''
            key_change_beat = -1
            change_time = -1
            # diameters = diameter(chord, key_index, key_change_bar, key_index)
    else:
        changed_note_shift = -1
        changed_key_pos = ''
        changed_key_name = ''
        key_change_beat = -1
        change_time = -1
        key_change_bar = -1
    key_change_params = {'changed_note_shift': changed_note_shift,
                         'changed_key_pos': changed_key_pos,
                         'changed_key_name': changed_key_name,
                         'key_change_beat': key_change_beat,
                         'change_time': change_time,
                         'key_change_bar': key_change_bar}
    return key_change_params


def export_plots(new_output_folder, file_name, total_tension, diameters, centroid_diff):
    base_name = os.path.basename(file_name)
    draw_tension(total_tension, os.path.join(new_output_folder,
                                             base_name[:-4]+'_tensile_strain.png'))
    draw_tension(diameters, os.path.join(new_output_folder,
                                         base_name[:-4] + '_diameter.png'))
    draw_tension(centroid_diff, os.path.join(new_output_folder,
                                             base_name[:-4] + '_centroid_diff.png'))


def get_key_index_change(pm, start_time, sixteenth_time):

    new_pm = copy.deepcopy(pm)
    for instrument in new_pm.instruments:
        for i, note in enumerate(instrument.notes):
            if note.start > start_time:
                instrument.notes = instrument.notes[i:]
                break

    piano_roll = get_piano_roll(new_pm, sixteenth_time)
    key_name = all_key_names

    key_name, key_pos, note_shift = cal_key(piano_roll, key_name, end_ratio=1)

    return key_name, key_pos, note_shift


def note_pitch(melody_track):

    pitch_sum = []
    for i in range(0, melody_track.shape[1]):
        indices = []
        for index, j in enumerate(melody_track[:, i]):
            if j > 0:
                indices.append(index-24)

        pitch_sum.append(np.mean(indices))
    return pitch_sum


def get_piano_roll(pm, beat_times):
    piano_roll = pm.get_piano_roll(times=beat_times)
    np.nan_to_num(piano_roll, copy=False)
    piano_roll = piano_roll > 0
    piano_roll = piano_roll.astype(int)

    return piano_roll


def cal_centroid(piano_roll, key_index, key_change_beat=-1, changed_key_index=-1):

    centroids = []
    for time_step in range(0, piano_roll.shape[1]):

        roll = piano_roll[:, time_step]

        if key_change_beat != -1:
            if time_step / 4 > key_change_beat:
                centroids.append(notes_to_ce(roll, changed_key_index))
            else:
                centroids.append(notes_to_ce(roll, key_index))
        else:
            centroids.append(notes_to_ce(roll, key_index))
    return centroids


def detect_key_change(key_diff, diameter, start_ratio=0.5):

    # 8 bar window
    key_diff_ratios = []
    # diameter_ratios = []
    fill_one = False
    steps = 0
    for i in range(8, key_diff.shape[0]-8):
        if fill_one and steps > 0:
            key_diff_ratios.append(1)
            steps -= 1
            if steps == 0:
                fill_one = False
            continue

        if np.any(key_diff[i-4:i]) and np.any(key_diff[i:i+4]):
            previous = np.mean(key_diff[i-4:i])
            current = np.mean(key_diff[i:i+4])
            key_diff_ratios.append(current / previous)
        else:
            fill_one = True
            steps = 4

    # for i in range(8,diameter.shape[0] - 8):
    #
    #     if np.any(diameter[i - 8:i]) and np.any(diameter[i:i + 8]):
    #         previous = np.mean(diameter[i - 8:i])
    #         current = np.mean(diameter[i:i + 8])
    #         diameter_ratios.append(current / previous)
    #     else:
    #         diameter_ratios.append(1)

    for i in range(int(len(key_diff_ratios) * start_ratio), len(key_diff_ratios)-2):

        if np.mean(key_diff_ratios[i:i+4]) > 2:
            key_diff_change_bar = i
            break
    else:
        key_diff_change_bar = -1

    # for i in range(int(len(diameter_ratios) * start_ratio), len(diameter_ratios) - 2):
    #
    #     if np.mean(diameter_ratios[i:i + 2]) > 2:
    #         diameter_change_bar = i
    #         break
    # else:
    #     diameter_change_bar = -1

    # return key_diff_change_bar + int(diameter.shape[0] * start_ratio) \
    #       if key_diff_change_bar < diameter_change_bar and key_diff_change_bar > 0 \
    #       else diameter_change_bar + int(diameter.shape[0] * start_ratio)
    return key_diff_change_bar + 12 if key_diff_change_bar != -1 else key_diff_change_bar


def draw_tension(values, file_name):
    plt.style.use('ggplot')
    plt.rcParams['xtick.labelsize'] = 6
    plt.figure()
    F = plt.gcf()
    F.set_size_inches(len(values)/7+5, 5)
    xtick = range(1, len(values) + 1)
    if isinstance(values, list):
        values = np.array(values)

    plt.xticks(xtick)

    # plt.ylim(0, 1)
    plt.plot(xtick, values, marker='o')
    plt.savefig(file_name)
    plt.close('all')


def remove_drum_track(pm):

    for instrument in pm.instruments:
        if instrument.is_drum:
            pm.instruments.remove(instrument)
    return pm


def get_beat_time(pm, beat_division=4):
    beats = pm.get_beats()

    beats = np.unique(beats, axis=0)

    divided_beats = []
    for i in range(len(beats) - 1):
        for j in range(beat_division):
            divided_beats.append((beats[i + 1] - beats[i]) / beat_division * j + beats[i])
    divided_beats.append(beats[-1])
    divided_beats = np.unique(divided_beats, axis=0)

    beat_indices = []
    for beat in beats:
        beat_indices.append(np.argwhere(divided_beats == beat)[0][0])

    down_beats = pm.get_downbeats()
    if divided_beats[-1] > down_beats[-1]:
        down_beats = np.append(down_beats, down_beats[-1] - down_beats[-2] + down_beats[-1])

    down_beats = np.unique(down_beats, axis=0)

    down_beat_indices = []
    for down_beat in down_beats:

        down_beat_indices.append(np.argmin(np.abs(down_beat - divided_beats)))

    return np.array(divided_beats), np.array(beats), np.array(down_beats), beat_indices, down_beat_indices


def extract_notes(file_name, track_num):
    pm = pretty_midi.PrettyMIDI(file_name)
    pm = remove_drum_track(pm)

    # if len(pm.time_signature_changes) > 1:
    #     logger.info(f'multiple time signature, skip {file_name}')
    #     return None
    # if not(pm.time_signature_changes[0].denominator == 4 and \
    #         (pm.time_signature_changes[0].numerator == 4 or
    #          pm.time_signature_changes[0].numerator == 2)):
    #     logger.info(f'not supported time signature, skip {file_name}')
    #     return None

    if track_num != 0:
        # if len(pm.instruments) < track_num:
        #     logger.warning(f'the file {file_name} has {len(pm.instruments)} tracks,'
        #                    f'less than the required track num {track_num}. Use all the tracks')
        pm.instruments = pm.instruments[:track_num]

    sixteenth_time, beat_time, down_beat_time, beat_indices, down_beat_indices = get_beat_time(pm, beat_division=4)

    piano_roll = get_piano_roll(pm, sixteenth_time)
    beat_data = {'sixteenth_time': sixteenth_time,
                 'beat_time': beat_time,
                 'down_beat_time': down_beat_time,
                 'beat_indices': beat_indices,
                 'down_beat_indices': down_beat_indices
                 }

    return [pm, piano_roll, beat_data]


def note_to_key_pos(note_indices, key_pos):
    note_positions = []
    for note_index in note_indices:
        note_positions.append(pitch_index_to_position(note_index_to_pitch_index[note_index]))
    diffs = np.linalg.norm(np.array(note_positions)-key_pos, axis=1)
    return diffs


def note_to_note_pos(note_indices, note_pos):
    note_positions = []
    for note_index in note_indices:
        note_positions.append(pitch_index_to_position(note_index_to_pitch_index[note_index]))
    diffs = np.linalg.norm(np.array(note_positions)-note_pos, axis=1)
    return diffs


def chord_to_key_pos(chord_indices, key_pos):
    chord_positions = []
    for chord_index in chord_indices:
        chord_positions.append(major_triad_position(note_index_to_pitch_index[chord_index]))

    for chord_index in chord_indices:
        chord_positions.append(minor_triad_position(note_index_to_pitch_index[chord_index]))
    diffs = np.linalg.norm(np.array(chord_positions)-key_pos, axis=1)
    return diffs


def key_to_key_pos(key_indices, key_pos):
    key_positions = []
    for key_index in key_indices:
        key_positions.append(major_key_position(note_index_to_pitch_index[key_index]))

    for key_index in key_indices:
        key_positions.append(minor_key_position(note_index_to_pitch_index[key_index]))

    diffs = np.linalg.norm(np.array(key_positions)-key_pos, axis=1)
    return diffs
