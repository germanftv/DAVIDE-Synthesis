import os
import sys
import pandas as pd
import numpy as np
from tqdm import tqdm
import argparse

from pytransform3d import transformations
from pytransform3d import trajectories

from davide_dp.configs import read_config
from davide_dp.utils import read_txt_data, is_step_complete, log_step_event, update_summary_for_video


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Generates camera poses, intrinsics, and imu data for video id')
    parser.add_argument("--config", type=str, default='./configs/config.yaml', help='Path to config file')
    parser.add_argument("--id", type=int, required=True, help='Video id')

    args = parser.parse_args(argv)
    return args


def export_poses(camera_data:pd.DataFrame, poses_file:str):
    """Export camera poses and intrinsics to txt files."""

    # Camera poses
    poses = camera_data[['frame-stamp', 'tx', 'ty', 'tz', 'qw', 'qx', 'qy', 'qz']]
    poses = poses.set_index('frame-stamp')

    frame_stamp = poses.index.values
    ref_pose = poses.loc[0.0]
    # Convert pq to matrix
    T_ref = transformations.transform_from_pq(ref_pose.values)

    # Convert poses to matrix transformations
    tmp = poses.to_numpy()
    T_n = trajectories.transforms_from_pqs(tmp)

    # Set reference pose as identity
    T_n2 = np.matmul(T_n, np.linalg.inv(T_ref))

    # Convert back to pq
    poses_values_2 = trajectories.pqs_from_transforms(T_n2)

    # Convert to dataframe
    poses = pd.DataFrame(poses_values_2, columns=['tx', 'ty', 'tz', 'qw', 'qx', 'qy', 'qz'])
    poses['frame-stamp'] = frame_stamp
    poses = poses[['frame-stamp', 'tx', 'ty', 'tz', 'qw', 'qx', 'qy', 'qz']]


    pd.DataFrame(poses).to_csv(poses_file, sep=',', header=True, index=False)


def export_intrinsics(intrinsics_data:pd.DataFrame, intrinsics_file:str):
    """Export camera intrinsics to txt file."""

    # Camera intrinsics
    intrinsics = intrinsics_data[['frame-stamp', 'fx', 'fy', 'cx', 'cy']]
    pd.DataFrame(intrinsics).to_csv(intrinsics_file, sep=',', header=True, index=False)


def export_imu(camera_data:pd.DataFrame, imu_file:str):
    """Export imu data to txt file."""

    # IMU data
    imu = camera_data[['frame-stamp', 'accx', 'accy', 'accz', 'gx', 'gy', 'gz', 'attqw', 'attqx', 'attqy', 'attqz', 'rrx', 'rry', 'rrz']]
    # Data columns:
    # User acceleration (gravity removed): 'accx', 'accy', 'accz'
    # Gravity component: 'gx', 'gy', 'gz'
    # Attitude quaternion: 'attw', 'attx', 'atty', 'attz'
    # Rotation rate: 'rrx', 'rry', 'rrz'
    pd.DataFrame(imu).to_csv(imu_file, sep=',', header=True, index=False)


def main(argv):
    # Parse arguments and read config
    args = parse_args(argv)
    config = read_config(args.config)
    idx = args.id

    # Get root directory and video list
    root_dir = config['DAVIDE-raw']['ROOT']
    data_annotations_path = config['DATA-GEN-PARAMS']['annotations']
    annotations = pd.read_csv(data_annotations_path)
    video_list = annotations['recording'].values.tolist()
    input_video_dir = os.path.join(root_dir, video_list[idx])
    print('Input video dir: ', input_video_dir)

    # Check if step 1 is done
    if not is_step_complete(dp_step='step_1', videos=video_list[idx], db_path=config['DATA-GEN-PARAMS']['dp_log']):
        raise ValueError(f"Step 1 is not done yet for video {video_list[idx]}. Check dp log.")

    # Input and output paths
    input_intrinsics_file = os.path.join(input_video_dir, config['DAVIDE-raw']['intrinsics'])
    input_camera_file = os.path.join(input_video_dir, config['DAVIDE-raw']['camera_info'])
    output_intrinsics_file = os.path.join(config['DAVIDE-tmp']['ROOT'], video_list[idx], config['DAVIDE-tmp']['camera_intrinsics'])
    output_poses_file = os.path.join(config['DAVIDE-tmp']['ROOT'], video_list[idx], config['DAVIDE-tmp']['camera_poses'])
    output_imu_file = os.path.join(config['DAVIDE-tmp']['ROOT'], video_list[idx], config['DAVIDE-tmp']['imu_data'])
    os.makedirs(os.path.join(config['DAVIDE-tmp']['ROOT'], video_list[idx]), exist_ok=True)

    # Read input files
    intrinsics_data = read_txt_data(input_intrinsics_file)
    camera_data = read_txt_data(input_camera_file)

    # Define frame-stamp
    num_frames = config['DATA-GEN-PARAMS']['num_frames']
    middle_frame_num = num_frames // 2 if num_frames % 2 == 0 else num_frames // 2 + 1
    tN = (len(camera_data)-1)//num_frames * num_frames
    frame_stamp = (np.linspace(0, tN , tN +1) - middle_frame_num)/num_frames

    # Concatenate frame-stamp to camera data and intrinsics data
    camera_data = camera_data[:len(frame_stamp)]
    intrinsics_data = intrinsics_data[:len(frame_stamp)]
    camera_data['frame-stamp'] = frame_stamp
    intrinsics_data['frame-stamp'] = frame_stamp

    # Export camera poses, intrinsics, and imu data
    export_poses(camera_data, output_poses_file)
    export_intrinsics(intrinsics_data, output_intrinsics_file)
    export_imu(camera_data, output_imu_file)

    print('--'*30)
    print('Poses data exported to: ', output_poses_file)
    print('Intrinsics data exported to: ', output_intrinsics_file)
    print('IMU data exported to: ', output_imu_file)

    # Update dp log
    log_step_event(video_name=video_list[idx], dp_step='step_5', new_status=1, db_path=config['DATA-GEN-PARAMS']['dp_log'])
    update_summary_for_video(video_name=video_list[idx], db_path=config['DATA-GEN-PARAMS']['dp_log'])
    print(f"Step 4 completed for video {video_list[idx]}.")


if __name__ == '__main__':
    main(sys.argv[1:])

