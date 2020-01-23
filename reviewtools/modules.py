import reviewtools
import imp
import inspect
import os
import pkgutil

IRRELEVANT_MODULES = ["sr_common", "sr_tests", "sr_skeleton", "common"]


def narrow_down_modules(modules):
    """
    Get a list of file names or module names and filter out
    the ones we know are irrelevant.
    """
    relevant_modules = []
    for module in modules:
        module_name = os.path.basename(module).replace(".py", "")
        if module_name not in IRRELEVANT_MODULES and module_name.startswith("sr_"):
            relevant_modules += [module]
    return relevant_modules


def get_modules():
    """
    Here we have a look at all the modules in the
    reviewtools package and filter out a few which
    are not relevant.

    Basically we look at all the ones which are
    derived from sr_common, where we can later on
    instantiate a *Review* object and run the
    necessary checks.
    """
    # Append 'RT_EXTRAS_PATH' to reviewtools.__path__ (append since below we
    # will depend on reviewtools.__path__ order for search order. For now
    # support only one extra path. In the future, could consider a
    # colon-separated list and adding each in order.
    if "RT_EXTRAS_PATH" in os.environ and os.path.isdir(os.environ["RT_EXTRAS_PATH"]):
        reviewtools.__path__.append(os.environ["RT_EXTRAS_PATH"])

    all_modules = [name for _, name, _ in pkgutil.iter_modules(reviewtools.__path__)]
    return narrow_down_modules(all_modules)


def find_main_class(module_name):
    """
    This function will find the Snap*Review class in
    the specified module.
    """
    module = None
    # Search the different reviewtools.__path__ directories, loading the first
    # match (get_modules(), above, appends to reviewtools.__path__ so we can
    # use its order for our search order. This allows utilizing RT_EXTRAS_PATH
    # when it is defined, but not in a way that allows it to override an
    # existing main (ie, non-extras) module.
    for dir in reviewtools.__path__:
        fullpath = "%s/%s.py" % (dir, module_name)
        if os.path.isfile(fullpath):
            module = imp.load_source(module_name, fullpath)
            break

    if module is None:
        raise FileNotFoundError(
            "could not find '%s' in: %s" % (module_name, reviewtools.__path__)
        )

    classes = inspect.getmembers(module, inspect.isclass)

    def find_test_class(a):
        return (
            (a[0].startswith("Click") or a[0].startswith("Snap"))
            and not a[0].endswith("Exception")
            and a[1].__module__ == module_name
        )

    test_class = list(filter(find_test_class, classes))
    if not test_class:
        return None
    init_object = getattr(module, test_class[0][0])
    return init_object


def init_main_class(module_name, pkg_file, overrides=None, report_type=None):
    """
    This function will instantiate the main Snap*Review
    class of a given module and instantiate it with the
    location of the file we want to inspect.
    """

    init_object = find_main_class(module_name)
    if not init_object:
        return None
    try:
        ob = init_object(pkg_file, overrides)
        # set the report_type separately since it is in the common class
        ob.set_report_type(report_type)
    except TypeError as e:
        print("Could not init %s: %s" % (init_object, str(e)))
        raise
    return ob
