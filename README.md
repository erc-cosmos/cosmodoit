
## COSMOS Analysis Toolbox

Functions in different programming languages to help with data analysis.

Create your own folders and upload code with their respective filetypes.

* Matlab
* Python
* R
* JavaScript

# Setting up the analysis pipeline
1. Clone the repository into a local folder.
2. Ensure [Python](https://www.python.org/downloads/) and [Musescore](https://musescore.org/fr/download) are installed.
3. [Optional] [Create a virtual environment and activate it](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/).
4. Install Python dependencies: `python -m pip install -r requirements.txt` (Python3 is required, replace with `python3` if the default installation is Python 2)
5. [Not needed on MacOS] Compile [Nakamura's alignment software](https://midialignment.github.io/demo.html) (beyond the scope of this ReadMe) and copy the executables to `music_features/bin` (all files should be overwritten)


# Running the analysis pipeline
**TL;DR: Just `doit`!** The pipeline should figure out what to do.

NB: If the `doit` command is not on the `PATH`, the `python -m doit` command is equivalent.

Computed files will be put in a `tmp` folder at the root of the repository (this is temporary—make sure it exists!).

The pipeline will look for pieces in the `tests/test_data/piece_directory_structure` folder (this is temporary). Each piece should be in its own folder, and requires :
* a performance in `.mid` format;
* a score in `.mscz` format (Musescore);
* a recording in `.wav` format.

The files don't need to have the same name before the extension, but it is recommended anyway.

It is possible to run only a given feature and/or a given piece by using `doit <feature>[:<piece>]`. Either can accept wildcards `*`, e.g. `doit loudness` or `doit loudness:*` to compute loudness for all detected pieces or `doit *:*Mazurka\ 17-4` to compute all features on Mazurka 17-4.

Type `doit list` to list all valid feature tasks, or `doit list --all` to list all subtasks — one per feature/piece pair.