import inspect
from timeit import default_timer
import numpy as np
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
    data,
    color,
)
import pandas as pd
import plotly.express as px
from line_profiler import LineProfiler, show_func
import io
import re

profile = LineProfiler()


l1 = 1000

img = np.random.randint(256, size=(l1, l1), dtype=np.uint8)
img_rgb = np.random.randint(256, size=(l1, l1, 3), dtype=np.uint8)
img_binary = data.binary_blobs(length=l1, volume_fraction=0.3).astype(np.uint8)
img2 = data.binary_blobs(length=l1, volume_fraction=0.3, seed=10).astype(np.uint8)


parameters = {
    "match_histograms": dict(reference=img2),
    "cycle_spin": dict(func=restoration.denoise_wavelet, max_shifts=4),
    "gabor": dict(frequency=0.5),
    "denoise_tv_bregman": dict(weight=1.0),
    "apply_hysteresis_threshold": dict(low=0.4, high=0.6),
    "hough_circle": dict(radius=10),
    "rescale": dict(scale=1.1),
    "rotate": dict(angle=10),
    "block_reduce": dict(block_size=(2, 2)),
    "flood": dict(seed_point=(0, 0)),
    "flood_fill": dict(seed_point=(0, 0), new_value=2),
    "join_segmentations": dict(s2=img2),
    "inpaint_biharmonic": dict(mask=img2),
    "contingency_table": dict(im_test=img2),
    "hausdorff_distance": dict(image1=img2),
    "compare_images": dict(image2=img2),
    "mean_squared_error": dict(image1=img2),
    "normalized_root_mse": dict(image_test=img2),
    "peak_signal_noise_ratio": dict(image_test=img2),
    "structural_similarity": dict(im2=img2),
    "variation_of_information": dict(image1=img2),
    "optical_flow_tvl1": dict(moving_image=img2),
    "phase_cross_correlation": dict(moving_image=img2),
    "threshold_local": dict(block_size=l1 // 8 if (l1 // 8) % 2 == 1 else l1 // 8 + 1),
    "downscale_local_mean": dict(factors=(2,) * img.ndim),
    "difference_of_gaussians": dict(low_sigma=1),
    "find_contours": dict(level=0.5),
    "h_maxima": dict(h=10),
    "h_minima": dict(h=10),
}

need_binary_image = [
    "convex_hull_object",
    "convex_hull_image",
    "hausdorff_distance",
    "remove_small_holes",
    "remove_small_objects",
]

need_rgb_image = ["quickshift", "rgb2lab", "rgb2xyz", "xyz2lab"]

skip_functions = [
    "integrate",
    "hough_circle_peaks",
    "hough_line_peaks",
    "ransac",
    "window",
    "hough_ellipse",
    "view_as_blocks",
    "view_as_windows",
    "apply_parallel",
    "regular_grid",
    "regular_seeds",
    "estimate_transform",
    "matrix_transform",
    "draw_haar_like_feature",
    "corner_subpix",
    "calibrate_denoiser",
    "ball",
    "cube",
    "diamond",
    "disk",
    "octagon",
    "octahedron",
    "rectangle",
    "square",
    "star",
    "hessian_matrix_eigvals",
    "hessian_matrix_det",
    "structure_tensor_eigvals",
]

slow_functions = ["iradon_sart", "chan_vese", "inpaint_biharmonic", "quickshift"]


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


def _strip_docstring(func_str, max_len=60):
    """remove docstring from code block so that is does not overflow the plotly
    hover.
    """
    line_number = len([m.start() for m in re.finditer("\n", func_str)])
    if line_number < max_len:
        res = func_str
    else:
        try:
            open_docstring, end_docstring = [
                m.start() for m in re.finditer('"""', func_str)
            ]
            res = func_str[:open_docstring] + func_str[end_docstring + 3 :]
        except ValueError:
            res = func_str
    return res


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
        color,
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
                if function[0] in need_binary_image:
                    im = img_binary
                elif function[0] in need_rgb_image:
                    im = img_rgb
                else:
                    im = img
                profile.add_function(function[1])
                start = default_timer()
                profile.runcall(function[1], im, **params)
                end = default_timer()
                times[function[0]] = end - start
            except:
                non_tested_functions.append(function[0])
        else:
            non_tested_functions.append(function[0])
    return times, non_tested_functions


# ----------------------- Run benchmark -------------------------
if __name__ == "__main__":

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
        color,
    ]

    # use skip_functions=skip_functions + slow_functions for a first test
    # since slow functions are really slow
    times, non_tested_functions = run_benchmark(
        img, img_binary, img_rgb, skip_functions=skip_functions
    )
    function_names = sorted(times, key=times.get)
    sorted_times = sorted(times.values())

    # ----------------------- Print results -------------------------
    df = []

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
                df.append(
                    {
                        "module": submodule.__name__,
                        "function": func[0],
                        "time": times[func[0]],
                    }
                )

    # ------------------- Retrieve results from line profiler --------
    line_stats = profile.get_stats()
    df = pd.DataFrame(df)
    df = df.sort_values(by=["time"])
    df["timings"] = ""
    for (fn, lineno, name), timings in line_stats.timings.items():
        output = io.StringIO()
        show_func(
            fn,
            lineno,
            name,
            line_stats.timings[fn, lineno, name],
            line_stats.unit,
            stream=output,
        )
        dump = _strip_docstring(output.getvalue(), max_len=20).replace("\n", "<br>")
        df.loc[df.function == name, "timings"] = dump

    # ----------------------- Display results -------------------------
    # threshold = np.quantile(df['time'], 0.85)
    # df['text'] = df['function']
    # df['text'][df['time'] < threshold] = ''
    fig = px.scatter(
        df,
        x="function",
        y="time",
        color="module",
        log_y=True,
        hover_data=["timings"],
        template="presentation",
    )
    fig.update_xaxes(tickfont_size=8)
    fig.update_traces(textposition="top left")
    fig.update_layout(
        title_text=f"Execution time for a {l1}x{l1} image",
        hoverlabel_align="left",
        hovermode="closest",
    )
    config = {"toImageButtonOptions": {"height": None, "width": None,}}
    fig.show(config=config)
