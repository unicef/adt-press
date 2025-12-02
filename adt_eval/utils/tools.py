


def is_running_in_jupyter():
    try:
        from IPython import get_ipython
        if 'IPKernelApp' in get_ipython().config:
            return True
        return False
    except:
        return False