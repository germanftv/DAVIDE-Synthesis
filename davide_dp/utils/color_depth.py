import os
import sys
import matplotlib as mpl
import matplotlib.cm as cm
import numpy as np
import argparse
from tqdm import tqdm


from .utils import imsave, read_depth_16bits


def _parse_args(argv):
    parser = argparse.ArgumentParser(description='Converts depth frames to color')
    parser.add_argument("--input_dir", type=str, required=True, help='Path to depth frames directory')
    parser.add_argument("--output_dir", type=str, required=True, help='Path to output directory')
    args = parser.parse_args(argv)
    return args


def get_color_map(depth):
    """Get color map for depth images."""

    # Color map
    cmap = cm.get_cmap('inferno')
    depth = depth
    # print("depth range: ", np.min(depth), np.max(depth))
    # Normalize color map
    norm = mpl.colors.LogNorm(vmin=0.1, vmax=40.0)
    # Color map with normalization
    m = cm.ScalarMappable(norm=norm, cmap=cmap)
    # Convert color map to numpy array
    rgb = m.to_rgba(depth, norm=True)[:, :, :3]
    # Convert to 8 bits
    rgb = (rgb * 255).astype(np.uint8)

    return rgb


def main(argv=None):
    args = _parse_args(argv)
    input_dir = args.input_dir
    output_dir = args.output_dir

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # List depth frames
    depth_frames = os.listdir(input_dir)
    depth_frames.sort()

    # Convert depth frames to color
    for frame in tqdm(depth_frames):
        # Read depth frame
        depth = read_depth_16bits(os.path.join(input_dir, frame))
        # Get color map
        rgb = get_color_map(depth)
        # Save color map
        imsave(os.path.join(output_dir, frame), rgb)


if __name__ == '__main__':
    main(sys.argv[1:])
