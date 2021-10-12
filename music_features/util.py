"""Miscellaneous functions for music_features."""
import csv
import functools
import os
import json

def readJson(filePath):
	with open(filePath, 'r') as openfile:
		json_object = json.load(openfile)
	return json_object

def writeJson(jsonObject, filePath):
	with open(filePath, "w") as outfile:
		outfile.write(jsonObject)
		return

def modifyJson(jsonObject, fileName):
	for i in jsonObject:
		i['file'] = fileName
		if 'linkedData' in i:
			i['linkedData'][0]['file'] = fileName
	return json.dumps(jsonObject, indent = 4)

def createTensionJson(tensionFile):
	jsonObject = readJson('tension_template.json')
	exportName = tensionFile.replace(".csv", ".json")
	newObject = modifyJson(jsonObject, os.path.basename(tensionFile))
	writeJson(newObject, exportName)
	return


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
