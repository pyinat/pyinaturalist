_run_validators = True


def get_run_validators() -> bool:
    """
    Check whether validators are enabled.
    :returns: whether or not validators are run.
    """
    return _run_validators


def set_run_validators(run: bool) -> None:
    """
    Set whether or not validators are enabled.
    :param run: whether the validators are run
    """
    # pylint: disable=W0603, global-statement
    if not isinstance(run, bool):
        raise TypeError("'run' must be bool.")
    global _run_validators
    _run_validators = run
