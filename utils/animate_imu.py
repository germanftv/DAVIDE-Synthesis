import os
import sys
import pandas as pd
import numpy as np
from tqdm import tqdm
import argparse
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import matplotlib as mpl


mpl.rcParams["font.family"] = "serif"
mpl.rcParams["font.size"] = "22"
mpl.rcParams["font.sans-serif"] = "Helvetica"
plt.rcParams['text.usetex'] = True


FIG_SIZE = (10, 7.5)
DPI = 96
FS = 60


def _parse_args(argv):
    parser = argparse.ArgumentParser(description='Generates an animation of imu data')
    parser.add_argument("--imu_file", type=str, required=True, help='Path to imu file')
    parser.add_argument("--comp", type=str, choices=['acc', 'rr'], required=True, help='Components to plot')
    parser.add_argument("--fps", type=int, default=20, help='Frames per second')
    parser.add_argument("--save", type=str, required=True, help='Path to save animation')
    parser.add_argument("--interval", type=int, default=4, help='Interval between time steps')
    args = parser.parse_args(argv)
    return args


def animate(imu_data, comp, fps, save, interval):
    """Animate imu data."""
    # Create figure
    fig = plt.figure(figsize=FIG_SIZE, dpi=DPI)
    ax = fig.add_subplot(111)
    # Set prop cycle
    ax.set_prop_cycle(color=['#44AA99', '#DDCC77', '#AA4499'])

    # Plot imu data
    if comp == 'acc':
        rng = (np.min(np.stack([imu_data["accx"], imu_data["accy"], imu_data["accz"]], axis=-1)), 
                   np.max(np.stack([imu_data["accx"], imu_data["accy"], imu_data["accz"]], axis=-1)))
        std = np.max(np.std(np.stack([imu_data["accx"], imu_data["accy"], imu_data["accz"]]), axis=-1))
        ax.set_ylabel(r'Acceleration (m/s$^2$)')   
    elif comp == 'rr':
        rng = (np.min(np.stack([imu_data["rrx"], imu_data["rry"], imu_data["rrz"]], axis=-1)), 
                   np.max(np.stack([imu_data["rrx"], imu_data["rry"], imu_data["rrz"]], axis=-1)))
        std = np.max(np.std(np.stack([imu_data["rrx"], imu_data["rry"], imu_data["rrz"]]), axis=-1))
        ax.set_ylabel(r'Rotation rate (rad/s)')
    rng = (rng[0] - std, rng[1] + std)

    ax.set_xlim(0, len(imu_data)* 1.0 / FS)
    ax.set_ylim(rng[0], rng[1])
    ax.set_xlabel(r'Time (s)')

    lx = ax.plot([], [], 'r-', label=r'$x$')[0]
    ly = ax.plot([], [], 'g-', label=r'$y$')[0]
    lz = ax.plot([], [], 'b-', label=r'$z$')[0]
    ax.legend(loc='upper right')

    ax.grid(True)
    # Update function
    def update(i):
        lx.set_data(1/ FS * np.arange(0, i*interval), imu_data[comp + 'x'][:i*interval])
        ly.set_data(1/ FS * np.arange(0, i*interval), imu_data[comp + 'y'][:i*interval])
        lz.set_data(1/ FS * np.arange(0, i*interval), imu_data[comp + 'z'][:i*interval])

    # Animate
    ani = animation.FuncAnimation(fig, update, frames=len(imu_data)//interval, interval=int(1000/FS), save_count=len(imu_data)//interval)
    writervideo = animation.FFMpegWriter(fps=fps)
    n = len(imu_data) // interval
    print('--'*40)
    print('Saving animation to {} ...'.format(save))
    pbar = tqdm(total=n)
    ani.save(save, writer=writervideo, dpi=DPI, progress_callback=lambda i, n: pbar.update(1))
    pbar.close()


def main(argv=None):
    args = _parse_args(argv)
    imu_file = args.imu_file
    comp = args.comp
    fps = args.fps
    save = args.save
    interval = args.interval

    # Read imu data
    print('Reading imu data from {} ...'.format(imu_file))
    imu_data = pd.read_csv(imu_file, sep=',')
    tN = len(imu_data) // interval * interval
    imu_data = imu_data.iloc[:tN]
    animate(imu_data, comp, fps, save, interval)


if __name__ == '__main__':
    main(sys.argv[1:])
