"""Miscellaneous functions for music_features."""
import csv
import functools
import os
import json
from typing import Any


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


def generate_target_path(original_path, working_folder, extension):
    """Generate a target path."""
    path_noext, _ = os.path.splitext(os.path.basename(original_path))
    return os.path.join(working_folder, path_noext + extension)


def targets_factory(original_path, working_folder):
    """Create a target path factory for a given original and working folder."""
    return functools.partial(generate_target_path, original_path, working_folder) if original_path is not None else None


def gen_default_tasks(task_docs):
    """Generate default tasks for docs."""
    for task, doc in task_docs.items():
        yield {
            'basename': task,
            'doc': doc,
            'name': None
        }
