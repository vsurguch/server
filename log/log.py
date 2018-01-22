
log_enabled = False

def log(filename):
    def log_wrap(func):
        if log_enabled:
            def wrap(*args, **kwargs):
                if log_enabled:
                    with open(filename, 'a') as log_file:
                        log_file.write("Function {} called with parameters: {} {}.\n".format(
                            func.__name__,
                            args,
                            kwargs))
                return func(*args, **kwargs)
            return wrap
        else:
            return func
    return log_wrap
