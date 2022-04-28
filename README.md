## COSMOS Analysis Toolbox

Toolbox for analysing music performance.

There are 2 main ways to use this toolbox:
* As a one-stop pipeline which computes all features, recomputing only what has changed
* As an importable package, accessible from any python code


# Setting up
1. Ensure [Python 3](https://www.python.org/downloads/) and [Musescore](https://musescore.org/fr/download) are installed.
2. Install the package through pip : `pip install cosmodoit` (or `pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ cosmodoit` until the package is on the main PyPI server). Depending on the python installation, replacing `pip` by `pip3`, `python -m pip` or `python3 -m pip` might be required.

<!-- (outdated)
# Setting up the analysis pipeline
1. [Clone the repository](https://forge-2.ircam.fr/help/gitlab-basics/start-using-git.md#clone-a-repository) into a local folder (links at the top of the page).
2. Ensure [Python](https://www.python.org/downloads/) and [Musescore](https://musescore.org/fr/download) are installed.
3. [Optional] [Create a virtual environment and activate it](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/).
4. Install Python dependencies: `python -m pip install -r requirements.txt` (Python3 is required, replace with `python3` if the default installation is Python 2)
5. [Not needed on MacOS] Compile [Nakamura's alignment software](https://midialignment.github.io/demo.html) (beyond the scope of this ReadMe) and copy the executables to `music_features/bin` (all files should be overwritten)
6. [Ongoing, recommended] Remember to `git pull` before running to ensure the code you are running is up to date. 
-->


# Running the analysis pipeline
**TL;DR: Just `cosmodoit`!** The pipeline should figure out what to do.

<!-- NB: If the `doit` command is not on the `PATH`, the `python -m doit` command is equivalent. -->

By default, the pipeline will look for pieces under the current folder, each in its own subfolder; use the `--dir <target_dir>` option to override that behavior (e.g., `cosmodoit --dir example_data`, where `example_data` contains piece subfolders). 
Each piece should be in its own folder, and requires :
* a performance in `.mid` format;
* a score in `.mscz` format (Musescore);
* a recording in `.wav` format.
* [Optional] a manual beats annotation, ending in `_beats_manual.csv` (will override the automatic beats extraction if present)

If one or more filetypes are missing, some features will not be computed, but those which can be derived from the existing data will still be computed. The files are not required to share the same base name, but it is recommended for tidyness. In case more than one file matches a type, a warning will be issued and an arbitrary one will be used for the computations.

Computed files will be outputted to the corresponding directory. An option to specify a target directory might be available in the future.

It is possible to run only a given feature and/or a given piece by using `cosmodoit <feature>[:<piece>]` (intermediate features will still get computed if needed). Either can accept wildcards `*`, e.g. `cosmodoit loudness` or `cosmodoit loudness:*` to compute loudness for all detected pieces or `cosmodoit *:Mazurka\ 17-4` to compute all features on Mazurka 17-4.

Type `cosmodoit list` to list all valid feature tasks, or `cosmodoit list --all` to list all subtasks — one per feature/piece pair.

To force a task to be recomputed, type `cosmodoit forget <task>` and it will be run on the next execution (`--all` to forget all tasks).

Running `cosmodoit clean` will remove the intermediary files, keeping only the final features.

If processing is long, using `cosmodoit -n <N> -P thread` will run tasks on N threads.

Some tasks can be configured, for example to set the window length for loudness. Parameters can be listed using `cosmodoit help <task>`, and are set through a `pyproject.toml` configuraion file (see `music_features/templates/pyproject.toml` for a sample of the format). Changes to the parameters will be picked up by the `doit` system and corresponding features (including dependent features) will be recomputed on the next run.
At the moment, parameters can only be supplied at the collection level: to apply parameters to a single piece, it must be put in a separate collection.


# Toolbox API convention
Each feature is handled by a different submodule, named `get_<feature>`. Submodules which do not abide by that convention are meant for internal use only.

Each submodule contains at least 3 functions for external use:
* a `get_<feature>` function which handles the computation of the feature. The exact signature differs for each (see individual documentation).
* a `write_<feature>` and a `read_<feature>` function to handle input and output.

To use them just import them into your code: `from cosmodoit.get_<feature> import get_<feature> write_<feature>` (or any other valid import statement)


# Extending the toolbox
The toolbox is meant to be easily extendable. To add a new feature, add a new submodule named `get_<feature>`. To be picked up by the pipeline, it must be added to the `submodules` variable in `dodo.py` and include in the module's namespace:
* [required] a `gen_tasks(piece_id, targets, **kwargs)` function to generate `doit` tasks (see the [documentation](https://pydoit.org/tasks.html)). See existing functions for the usage of the parameters;
* [recommended] a `task_docs` dictionary, which maps the (sub)tasks' names to description strings;
* [optional] a `param_sources` iterable, which lists the functions that provide keyword-only parameters that should be exposed through the config file.

If a new input type is required, it can be added as an `InputDescriptor` in the `discover_files_by_piece` function of the `dodo.py` module, which describes the patterns (positive and negative) to match when scanning for the file.

It is recommended, but not strictly required, to provide the functions of the API convention if you add a new feature.