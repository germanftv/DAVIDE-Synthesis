import os
import sys
import pandas as pd
import numpy as np
from tqdm import tqdm
import argparse
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import matplotlib as mpl

import pytransform3d.transformations as pt
import pytransform3d.trajectories as ptr
import pytransform3d.camera as pc

from .utils import CameraIntrinsics

mpl.rcParams["font.family"] = "serif"
mpl.rcParams["font.size"] = "22"
mpl.rcParams["font.sans-serif"] = "Helvetica"
# plt.rcParams['text.usetex'] = True


FIG_SIZE = (10, 7.5)
DPI = 96
FS = 60
IMG_SIZE = (1920, 1440)
PX_size = 1.9e-6


def _parse_args(argv):
    parser = argparse.ArgumentParser(description='Generates an animation of camera poses')
    parser.add_argument("--poses_file", type=str, required=True, help='Path to poses file')
    parser.add_argument("--intrinsics_file", type=str, required=True, help='Path to intrinsics file')
    parser.add_argument("--fps", type=int, default=20, help='Frames per second')
    parser.add_argument("--save", type=str, required=True, help='Path to save animation')
    args = parser.parse_args(argv)
    return args


def animate(poses: np.ndarray, intrinsics:CameraIntrinsics, fps:int, factor:int, save:str):
    """Animate camera poses."""
    # Create figure
    fig = plt.figure(figsize=FIG_SIZE, dpi=DPI)
    ax = fig.add_subplot(111)
    # ax.grid(True)
    cam2world0 = pt.transform_from_pq(poses[0])
    print('cam2world0: ', cam2world0)
    ax = pt.plot_transform(A2B=cam2world0,
                           s=0.3)
    # ax.xaxis._axinfo['label']['space_factor'] = 4.8
    # ax.yaxis._axinfo['label']['space_factor'] = 4.8
    # ax.zaxis._axinfo['label']['space_factor'] = 4.8

    # Get intrinsics matrix
    intrinsics_matrix = intrinsics.to_matrix()
    
    # Axis limits
    pos_min = poses[:, :3].min(axis=0)
    pos_max = poses[:, :3].max(axis=0)
    center = (pos_max + pos_min) / 2.0
    max_half_extent = 0.8 * np.mean(pos_max - pos_min)
    print("min pos x: {:.2f}, max pos x: {:.2f}".format(pos_min[0], pos_max[0]))
    print("min pos y: {:.2f}, max pos y: {:.2f}".format(pos_min[1], pos_max[1]))
    print("min pos z: {:.2f}, max pos z: {:.2f}".format(pos_min[2], pos_max[2]))

    # Update function
    def update(i):
        ax.cla()
        ax.grid(True)
        # Plot camera
        cam2world = pt.transform_from_pq(poses[i])
        # virtual_distance to pixel units

        pc.plot_camera(ax=ax, M=intrinsics_matrix, cam2world=cam2world,
                              virtual_image_distance=0.3, sensor_size=IMG_SIZE, color='tab:orange')
        # Plot trajectory
        ptr.plot_trajectory(ax=ax, P=poses[:i+1], n_frames=np.minimum(1, i//4), show_direction=False, color='tab:blue')

        ax.set_title(r"Time: {:.2f} s".format(i * factor / FS), y=-0.1)

        ax.set_xlim((center[0] - max_half_extent, center[0] + max_half_extent))
        ax.set_ylim((center[1] - max_half_extent, center[1] + max_half_extent))
        ax.set_zlim((center[2] - max_half_extent, center[2] + max_half_extent))
        ax.set_xlabel(r'$x$ (m)', labelpad=20)
        ax.set_ylabel(r'$y$ (m)', labelpad=20)
        ax.set_zlabel(r'$z$ (m)', labelpad=20)
        ax.view_init(vertical_axis='x', azim=-135 ) #, elev=30)

    # Save animation
    ani = animation.FuncAnimation(fig, update, frames=len(poses), interval=int(1000/FS), save_count=len(poses))
    writervideo = animation.FFMpegWriter(fps=fps)
    N = len(poses)
    print('--'*40)
    print('Saving animation to {} ...'.format(save))
    pbar = tqdm(total=N)
    ani.save(save, writer=writervideo, dpi=DPI, progress_callback=lambda i, n: pbar.update(1))
    pbar.close()


def main(argv=None):
    args = _parse_args(argv)
    poses_file = args.poses_file
    fps = args.fps
    save = args.save
    intrinsics_file = args.intrinsics_file

    # Read camera poses
    print('Reading camera poses from {} ...'.format(poses_file))
    poses = pd.read_csv(poses_file, sep=',')

    # Read intrinsics
    print('Reading intrinsics from {} ...'.format(args.intrinsics_file))
    intrinsics_data = pd.read_csv(intrinsics_file, sep=',')
    
    # set frame-stamp as index
    poses.set_index('frame-stamp', inplace=True)
    factor = 1/ (poses.index[1] - poses.index[0])
    intrinsics_data.set_index('frame-stamp', inplace=True)
    int_frame_stamps = poses.index.astype(int)
    int_frame_stamps = np.unique(int_frame_stamps)

    poses = poses.loc[int_frame_stamps].to_numpy()
    A2Bs = ptr.transforms_from_pqs(poses)
    #invert z projection
    T_ref = np.eye(4)
    T_ref[2, 2] = -1
    A2Bs = np.matmul(T_ref, A2Bs)
    poses = ptr.pqs_from_transforms(A2Bs)


    intrinsics_data = intrinsics_data.loc[int_frame_stamps].to_dict('list')

    # Create camera intrinsics
    intrinsics = CameraIntrinsics(**intrinsics_data)
    intrinsics.average()

    # Animate
    animate(poses, intrinsics, fps, factor, save)


if __name__ == '__main__':
    main(sys.argv[1:])
