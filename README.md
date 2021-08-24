
## COSMOS Analysis Toolbox

Functions in different programming languages to help with data analysis.

Create your own folders and upload code with their respective filetypes.

* Matlab
* Python
* R
* JavaScript

# Setting up the analysis pipeline
*TODO*

# Running the analysis pipeline
**TL;DR: Just `doit`!** The pipeline should figure out what to do.

NB: If the `doit` command is not on the `PATH`, the `python -m doit` command is equivalent.

Computed files will be put in a `tmp` folder at the root of the repository (this is temporary).

The pipeline will look for pieces in the `tests/test_data/piece_directory_structure` folder (this is temporary). Each piece should be in its own folder, and requires :
* a performance in `.mid` format;
* a score in `.mscz` format (Musescore);
* a recording in `.wav` format.

The files don't need to have the same name before the extension, but it is recommended anyway.

It is possible to run only a given feature and/or a given piece by using `doit <feature>[:<piece>]`. Either can accept wildcards `*`, e.g. `doit loudness` or `doit loudness:*` to compute loudness for all detected pieces or `doit *:*Mazurka\ 17-4` to compute all features on Mazurka 17-4.

Type `doit list` to list all valid feature tasks, or `doit list --all` to list all subtasks — one per feature/piece pair.