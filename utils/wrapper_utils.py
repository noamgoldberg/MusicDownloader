def wrapper(func, *args, call_callable_args: bool = True, **kwargs):
    """
    Returns a callable object that, when called, invokes func with the specified arguments and keyword arguments.

    :param func: The function to be called.
    :param args: Positional arguments to be passed to the function.
    :param kwargs: Keyword arguments to be passed to the function.
    :return: A callable that, when called, executes func(*args, **kwargs).
    """
    
    def _inner():
        if call_callable_args:
            args_called = tuple((arg() if callable(arg) else arg) for arg in args)
            return func(*args_called, **kwargs)
        return func(*args, **kwargs)
    return _inner