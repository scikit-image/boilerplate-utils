import numpy as np
import inspect
from skimage import (
    draw,
    exposure,
    feature,
    filters,
    measure,
    metrics,
    morphology,
    registration,
    restoration,
    segmentation,
    transform,
    util,
    data,
    color,
)
from timeit import default_timer
from define_arguments import (
    parameters,
    skip_functions,
    slow_functions,
    need_binary_image,
    need_rgb_image,
)
from define_arguments import img, img_binary, img_rgb


def only_one_nondefault(args):
    """
    Returns True if the function has only one non-keyword parameter,
    False otherwise.
    """
    defaults = 0 if args.defaults is None else len(args.defaults)
    if len(args.args) >= 1 and (len(args.args) - defaults <= 1):
        return True
    else:
        return False


def run_benchmark(
    img,
    img_binary,
    img_rgb,
    module_list=[
        exposure,
        feature,
        filters,
        measure,
        metrics,
        morphology,
        registration,
        restoration,
        segmentation,
        transform,
        util,
    ],
    skip_functions=[],
):
    times = {}

    functions = []
    for submodule in module_list:
        functions += inspect.getmembers(submodule, inspect.isfunction)
    non_tested_functions = []

    for function in functions:
        args = inspect.getfullargspec(function[1])
        only_one_argument = only_one_nondefault(args)
        if function[0] in skip_functions:
            continue
        if only_one_argument or function[0] in parameters:
            params = parameters[function[0]] if function[0] in parameters else {}
            try:
                start = default_timer()
                if function[0] in need_binary_image:
                    im = img_binary
                elif function[0] in need_rgb_image:
                    im = img_rgb
                else:
                    im = img
                function[1](im, **params)
                end = default_timer()
                times[function[0]] = end - start
            except:
                non_tested_functions.append(function[0])
        else:
            non_tested_functions.append(function[0])
    return times, non_tested_functions


# ----------------------- Run benchmark -------------------------

module_list = [
    exposure,
    feature,
    filters,
    measure,
    metrics,
    morphology,
    registration,
    restoration,
    segmentation,
    transform,
    util,
]

# use skip_functions=skip_functions + slow_functions for a first test
# since slow functions are really slow
times, non_tested_functions = run_benchmark(
    img, img_binary, img_rgb, skip_functions=skip_functions
)
function_names = sorted(times, key=times.get)
sorted_times = sorted(times.values())

# ----------------------- Print results -------------------------

print("Functions which could not be tested")
print("=" * 70)

for func in non_tested_functions:
    print(func)

print("\n")
print("Sorted by increasing execution time")
print("=" * 70)

for func_name, t in zip(function_names, sorted_times):
    print(func_name, t)

print("\n")
print("Sorted by subpackage")
print("=" * 70)

for submodule in module_list:
    print("\n")
    print(submodule.__name__)
    print("-" * 70)
    for func in inspect.getmembers(submodule, inspect.isfunction):
        if func[0] in times:
            print(func[0], times[func[0]])
