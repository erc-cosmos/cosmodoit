
def string_escape_concat(strings, sep=' '):
    """Concatenate strings after wrapping them in quotes."""
    return sep.join(f'"{s}"' for s in strings)


def run_doit(task_set, commands=None):
    """Run doit with on the specified task creators with the given command."""
    commands = commands if commands is not None else []
    import doit
    doit.doit_cmd.DoitMain(doit.cmd_base.ModuleTaskLoader(task_set)).run(commands)