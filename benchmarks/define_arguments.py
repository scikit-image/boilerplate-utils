from skimage import restoration, data
import numpy as np

l1 = 1000

img = np.random.randint(256, size=(l1, l1), dtype=np.uint8)
img_rgb = np.random.randint(256, size=(l1, l1, 3), dtype=np.uint8)
img_binary = data.binary_blobs(length=l1, volume_fraction=0.3).astype(np.uint8)
img2 = data.binary_blobs(length=l1, volume_fraction=0.3, seed=10).astype(np.uint8)


parameters = {
        'match_histograms': dict(reference=img2),
        'cycle_spin': dict(func=restoration.denoise_wavelet, max_shifts=4),
        'gabor': dict(frequency=0.5),
        'denoise_tv_bregman': dict(weight=1.0),
        'apply_hysteresis_threshold': dict(low=0.4, high=0.6),
        'hough_circle': dict(radius=10),
        'rescale': dict(scale=1.1),
        'rotate': dict(angle=10),
        'block_reduce': dict(block_size=(2, 2)),
        'flood': dict(seed_point=(0, 0)),
        'flood_fill': dict(seed_point=(0, 0), new_value=2),
        'join_segmentations': dict(s2=img2),
        'inpaint_biharmonic': dict(mask=img2),
        'contingency_table': dict(im_test=img2),
        'hausdorff_distance': dict(image1=img2),
        'compare_images': dict(image2=img2),
        'mean_squared_error': dict(image1=img2),
        'normalized_root_mse': dict(image_test=img2),
        'peak_signal_noise_ratio': dict(image_test=img2),
        'structural_similarity': dict(im2=img2),
        'variation_of_information': dict(image1=img2),
        'optical_flow_tvl1': dict(moving_image=img2),
        'phase_cross_correlation': dict(moving_image=img2),
        'threshold_local': dict(block_size=l1 // 8 if (l1 //8) % 2 == 1 else l1 // 8 + 1),
        'downscale_local_mean': dict(factors=(2,)*img.ndim),
        'difference_of_gaussians': dict(low_sigma=1),
        'find_contours': dict(level=0.5),
        'h_maxima': dict(h=10),
        'h_minima': dict(h=10),
    }

need_binary_image = [
        'convex_hull_object',
        'convex_hull_image',
        'hausdorff_distance',
        'remove_small_holes',
        'remove_small_objects',
        ]

need_rgb_image = ['quickshift']

skip_functions = [
        'integrate',
        'hough_circle_peaks',
        'hough_line_peaks',
        'ransac',
        'window',
        'hough_ellipse',
        'view_as_blocks',
        'view_as_windows',
        'apply_parallel',
        'regular_grid',
        'regular_seeds',
        'estimate_transform',
        'matrix_transform',
        'draw_haar_like_feature',
        'corner_subpix',
        'calibrate_denoiser',
        'ball',
        'cube',
        'diamond',
        'disk',
        'octagon',
        'octahedron',
        'rectangle',
        'square',
        'star'
        ]

slow_functions = [
        'iradon_sart',
        'chan_vese',
        'inpaint_biharmonic',
        ]
