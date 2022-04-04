"""Miscellaneous functions for music_features."""
import csv
import functools
import os
import json
from typing import Any, Callable, Dict, List


def read_json(filePath):
    """Read a json file."""
    with open(filePath, 'r') as openfile:
        json_object = json.load(openfile)
    return json_object


def write_json(json_object, file_path):
    """Write a json object to disk.

    Args:
        json_object (json Object): The object to save
        filePath (str | pathLike): Path at which to save
    """
    with open(file_path, "w") as outfile:
        outfile.write(json_object)
        return


def set_json_file(json_object: Any, file_name: str) -> str:
    """Set the 'file' items in a json-serializable to file_name.

    Args:
        json_object (Any): JSON-Serializable object to set
        file_name (str): Value to set

    Returns:
        str: Updated and serialized object
    """
    for i in json_object:
        i['file'] = file_name
        if 'linkedData' in i:
            i['linkedData'][0]['file'] = file_name
    return json.dumps(json_object, indent=4)


def string_escape_concat(strings, sep=' '):
    """Concatenate strings after wrapping them in quotes."""
    return sep.join(f'"{s}"' for s in strings)


def run_doit(task_set, commands=None):
    """Run doit with on the specified task creators with the given command."""
    commands = commands if commands is not None else []
    import doit
    doit.doit_cmd.DoitMain(doit.cmd_base.ModuleTaskLoader(task_set)).run(commands)


def write_file(filename, data):
    """Write a list of dictionaries with identical keys to disk."""
    fields = data[0].keys()
    with open(filename, mode='w') as csvFile:
        writer = csv.DictWriter(csvFile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)


def generate_target_path(original_path: str, working_folder: str, extension: str):
    """Generate a target path."""
    path_noext, _ = os.path.splitext(os.path.basename(original_path))
    return os.path.join(working_folder, path_noext + extension)


class NameSchemeError(LookupError):
    """Exceptions related to the naming of files."""

    pass


def target_finder(name_scheme, piece_id, paths, working_folder, file_type):
    """Find the correct path for a computed file."""
    try:
        # If the file type is an input file, return as is
        return getattr(paths, file_type)
    except:
        pass
    # Otherwise, use the naming scheme to generate the target
    try:
        original_type, extension = name_scheme[file_type]
    except KeyError as e:
        raise NameSchemeError("Attempt to use an unknown destination file type") from e
    try:
        original_path: str = getattr(paths, original_type) or piece_id
    except AttributeError as e:
        raise NameSchemeError("Attempt to use an unknown source file type") from e
    return generate_target_path(original_path, working_folder, extension)


def targets_factory(original_path, working_folder):
    """Create a target path factory for a given original and working folder."""
    # TODO Rework to ensure consistent naming scheme
    return functools.partial(generate_target_path, original_path, working_folder) if original_path is not None else None


def targets_factory_new(name_scheme, piece_id, paths, working_folder):
    """Create a target path factory for a given set of original paths, working folder and name_scheme."""
    return functools.partial(target_finder, name_scheme, piece_id, paths, working_folder)


def gen_default_tasks(task_docs):
    """Generate default tasks for docs."""
    for task, doc in task_docs.items():
        yield {
            'basename': task,
            'doc': doc,
            'name': None
        }


def collect_kw_parameters(*funcs: Callable) -> List[Dict[str, Any]]:
    """Collect keyword-only arguments from a list of functions and return them as doit task params.

    Args:
        funcs (Tuple[Callable]): functions whose keyword argument are to be bound to a task

    Returns:
        List[Dict[str, Any]]: doit-formatted list of parameters
    """
    # TODO: Collect type as well so it can be used in command line if not a string
    return [{'name': param, 'default': default, 'long': param}
            for func in funcs
            for (param, default) in func.__kwdefaults__.items()]

default_naming_scheme = {
    # Structure: <type_id>: (<source>, <extension>)
    "beats": ("perfmidi", "_beats.csv"),
    "manual_beats": ("perfmidi", "_beats_manual.csv"),
    "ref_midi": ("score", "_ref.mid"),
    "match": ("perfmidi", "_match.txt"),
    "bars": ("perfmidi", "_bars.csv"),
    "loudness": ("perfmidi", "_loudness_all.csv"),
    "loudness_simple": ("perfmidi", "_loudness.csv"),
    "loudness_resampled": ("perfmidi", "_loudness_resampled.csv"),
    "velocity": ("perfmidi", "_velocity.csv"),
    "sustain": ("perfmidi", "_sustain.csv"),
    "tempo": ("perfmidi", "_tempo.csv"),
    # Alignment related files
    "ref_copy_noext": ("score", "_ref"),
    "ref_midi": ("score", "_ref.mid"),
    "ref_pianoroll": ("score", "_ref_spr.txt"),
    "ref_HMM": ("score", "_hmm.txt"),
    "ref_FMT3X": ("score", "_fmt3x.txt"),
    "perf_copy_noext": ("perfmidi", "_perf"),
    "perf_pianoroll": ("perfmidi", "_perf_spr.txt"),
    "perf_prematch": ("perfmidi", "_pre_match.txt"),
    "perf_errmatch": ("perfmidi", "_err_match.txt"),
    "perf_realigned": ("perfmidi", "_match.txt"),
    # Tension related files
    "tension": ("perfmidi", "_tension.csv"),
    "tension_bar": ("perfmidi", "_tension_bar.csv"),
    "tension_json": ("perfmidi", "_tension.json"),
    "tension_bar_json": ("perfmidi", "_tension_bar.json")
}
