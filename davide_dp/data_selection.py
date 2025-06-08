import os
import sys
import pandas as pd
import numpy as np
from tqdm import tqdm
import argparse

from pytransform3d import transformations
from pytransform3d import trajectories

from configs import read_config
from davide_dp.utils import (
    is_step_complete,
    log_step_event,
    update_summary_for_video,
    read_txt_data
)


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Generates camera poses, intrinsics, and imu data for video id')
    parser.add_argument("--config", type=str, default='./configs/config.yaml', help='Path to config file')
    parser.add_argument("--id", type=int, required=True, help='Video id')
    parser.add_argument("--mono_depth", action='store_true', help='Export mono depth folder')

    args = parser.parse_args(argv)
    return args


def get_frame_ids(start, end, input_video_dir, config):
    """Get frame ids from start and end annotations."""
    blur_dir = os.listdir(os.path.join(input_video_dir, config['DAVIDE-tmp']['blur_folder']))
    blur_dir.sort()
    frame_ids = np.asarray([int(os.path.splitext(file)[0]) for file in blur_dir])

    # Check if start and end are not zero
    if start == 0.0 and end == 0.0:
        return int(0), int(0)

    # Get start id
    if start == 0.0 or start == None:
        start_id = int(frame_ids[0])
    else:
        start = int(start)
        start_id = (frame_ids - start)[(frame_ids - start)>=0][0] + start

    # Get end id
    if end == None:
        end_id = frame_ids[-1]
    else:
        end = int(end)
        end_id = (frame_ids - end)[(frame_ids - end)<=0][-1] + end

    return int(start_id), int(end_id)


def convert_recording_name(recording, annotations):
    """Convert recording name based on tag"""
    # Get tag
    tag = annotations[annotations['recording'] == recording]['tag'].values[0]
    # Filter annotations with tag
    annotations = annotations[annotations['tag'] == tag]
    # Filter out annotations with start and end equal to zero
    annotations = annotations.query('start != 0.0 | end != 0.0')
    # Reset index
    annotations = annotations.reset_index()

    # Get index of recording
    idx = annotations[annotations['recording'] == recording].index[0]
    # Get recording name
    recording_name = "{}{:02d}".format(tag, int(idx)+1)
    return recording_name


def export_blur_folder(start_id, end_id, input_video_dir, output_root_dir, recording_name, config):
    """Export blur folder based on start and end ids."""
    # Get input blur folder
    blur_folder = os.path.join(input_video_dir, config['DAVIDE-tmp']['blur_folder'])
    # Get blur files
    blur_files = os.listdir(blur_folder)
    blur_files.sort()
    # Get start file
    start_file = "{:08d}.png".format(start_id)
    # Get end file
    end_file = "{:08d}.png".format(end_id)
    # Get start and end file ids
    start_file_id = [i for i, file in enumerate(blur_files) if file == start_file][0]
    end_file_id = [i for i, file in enumerate(blur_files) if file == end_file][0]
    # Select blur files
    blur_files = blur_files[start_file_id:end_file_id+1]
    # Export blur files
    for blur_file in tqdm(blur_files, desc='Exporting blur files'):
        output_parent_dir = os.path.join(output_root_dir, config['DAVIDE']['blur_folder'], recording_name)
        os.makedirs(output_parent_dir, exist_ok=True)
        os.system('cp {} {}'.format(os.path.join(blur_folder, blur_file), os.path.join(output_parent_dir, blur_file)))


def export_sharp_folder(start_id, end_id, input_video_dir, output_root_dir, recording_name, config):
    """Export sharp folder based on start and end ids."""
    # Get sharp folder
    sharp_folder = os.path.join(input_video_dir, config['DAVIDE-tmp']['sharp_folder'])
    # Get sharp files
    sharp_files = os.listdir(sharp_folder)
    sharp_files.sort()
    # Get start file
    start_file = "{:08d}.png".format(start_id)
    # Get end file
    end_file = "{:08d}.png".format(end_id)
    # Get start and end file ids
    start_file_id = [i for i, file in enumerate(sharp_files) if file == start_file][0]
    end_file_id = [i for i, file in enumerate(sharp_files) if file == end_file][0]
    # Select sharp files
    sharp_files = sharp_files[start_file_id:end_file_id+1]
    # Export sharp files
    for sharp_file in tqdm(sharp_files, desc='Exporting sharp files'):
        output_parent_dir = os.path.join(output_root_dir, config['DAVIDE']['sharp_folder'], recording_name)
        os.makedirs(output_parent_dir, exist_ok=True)
        os.system('cp {} {}'.format(os.path.join(sharp_folder, sharp_file), os.path.join(output_parent_dir, sharp_file)))


def export_depth_folder(start_id, end_id, input_video_dir, output_root_dir, recording_name, config):
    """Export depth folder based on start and end ids."""
    # Get depth folder
    depth_folder = os.path.join(input_video_dir, config['DAVIDE-tmp']['depth_folder'])
    # Get depth files
    depth_files = os.listdir(depth_folder)
    depth_files.sort()
    # Get start file
    start_file = "{:08d}.png".format(start_id)
    # Get end file
    end_file = "{:08d}.png".format(end_id)
    # Get start and end file ids
    start_file_id = [i for i, file in enumerate(depth_files) if file == start_file][0]
    end_file_id = [i for i, file in enumerate(depth_files) if file == end_file][0]
    # Select depth files
    depth_files = depth_files[start_file_id:end_file_id+1]
    # Export depth files
    for depth_file in tqdm(depth_files, desc='Exporting depth maps'):
        output_parent_dir = os.path.join(output_root_dir, config['DAVIDE']['depth_folder'], recording_name)
        os.makedirs(output_parent_dir, exist_ok=True)
        os.system('cp {} {}'.format(os.path.join(depth_folder, depth_file), os.path.join(output_parent_dir, depth_file)))


def export_mono_depth_folder(start_id, end_id, input_video_dir, output_root_dir, recording_name, config, rgb_dir):
    """Export depth folder based on start and end ids."""
    # Get depth folder
    mono_depth_folder = os.path.join(input_video_dir, '{}_{}'.format(config['DAVIDE-tmp']['mono_depth_folder'], rgb_dir))
    # Get depth files
    mono_depth_files = os.listdir(mono_depth_folder)
    mono_depth_files.sort()
    # Get start file
    start_file = "{:08d}.png".format(start_id)
    # Get end file
    end_file = "{:08d}.png".format(end_id)
    # Get start and end file ids
    start_file_id = [i for i, file in enumerate(mono_depth_files) if file == start_file][0]
    end_file_id = [i for i, file in enumerate(mono_depth_files) if file == end_file][0]
    # Select depth files
    mono_depth_files = mono_depth_files[start_file_id:end_file_id+1]
    # Export depth files
    for depth_file in tqdm(mono_depth_files, desc='Exporting mono-depth files'):
        mono_depth_out_dirname = '{}_{}'.format(config['DAVIDE']['mono_depth_folder'], rgb_dir)
        output_parent_dir = os.path.join(output_root_dir, mono_depth_out_dirname, recording_name)
        os.makedirs(output_parent_dir, exist_ok=True)
        os.system('cp {} {}'.format(os.path.join(mono_depth_folder, depth_file), os.path.join(output_parent_dir, depth_file)))


def export_confidence_folder(start_id, end_id, input_video_dir, output_root_dir, recording_name, config):
    """Export confidence folder based on start and end ids."""
    # Get confidence folder
    confidence_folder = os.path.join(input_video_dir, config['DAVIDE-tmp']['confidence_folder'])
    # Get confidence files
    confidence_files = os.listdir(confidence_folder)
    confidence_files.sort()
    # Get start file
    start_file = "{:08d}.png".format(start_id)
    # Get end file
    end_file = "{:08d}.png".format(end_id)
    # Get start and end file ids
    start_file_id = [i for i, file in enumerate(confidence_files) if file == start_file][0]
    end_file_id = [i for i, file in enumerate(confidence_files) if file == end_file][0]
    # Select confidence files
    confidence_files = confidence_files[start_file_id:end_file_id+1]
    # Export confidence files
    for confidence_file in tqdm(confidence_files, desc='Exporting confidence maps'):
        output_parent_dir = os.path.join(output_root_dir, config['DAVIDE']['confidence_folder'], recording_name)
        os.makedirs(output_parent_dir, exist_ok=True)
        os.system('cp {} {}'.format(os.path.join(confidence_folder, confidence_file), os.path.join(output_parent_dir, confidence_file)))


def export_intrinsics(start_id, end_id, input_video_dir, output_root_dir, recording_name, config):
    """Export intrinsics based on start and end ids."""
    # Get intrinsics file
    intrinsics_file = os.path.join(input_video_dir, config['DAVIDE-tmp']['camera_intrinsics'])
    # Read intrinsics
    intrinsics = pd.read_csv(intrinsics_file, sep=',')

    num_frames = config['DATA-GEN-PARAMS']['num_frames']
    middle_frame_num = num_frames // 2 if num_frames % 2 == 0 else num_frames // 2 + 1

    # Get start and end intrinsics
    intrinsics = intrinsics.iloc[start_id - middle_frame_num:end_id + (num_frames-middle_frame_num)+1]

    # Reset frame_stamps
    tN = len(intrinsics)//num_frames * num_frames
    frame_stamp = (np.linspace(0, tN , tN +1) - middle_frame_num)/num_frames
    intrinsics['frame-stamp'] = frame_stamp

    # Export intrinsics
    intrinsics_file = os.path.join(output_root_dir, config['DAVIDE']['intrinsics_folder'], "{}.csv".format(recording_name))
    print('Exporting intrinsics to: ', intrinsics_file)
    os.makedirs(os.path.dirname(intrinsics_file), exist_ok=True)
    intrinsics.to_csv(intrinsics_file, sep=',', header=True, index=False)


def export_poses(start_id, end_id, input_video_dir, output_root_dir, recording_name, config):
    """Export poses based on start and end ids."""
    # Get poses file
    poses_file = os.path.join(input_video_dir, config['DAVIDE-tmp']['camera_poses'])
    # Read poses
    poses = pd.read_csv(poses_file, sep=',')

    num_frames = config['DATA-GEN-PARAMS']['num_frames']
    middle_frame_num = num_frames // 2 if num_frames % 2 == 0 else num_frames // 2 + 1

    # Get start and end poses
    poses = poses.iloc[start_id - middle_frame_num:end_id + (num_frames-middle_frame_num)+1]

    # Reset frame_stamps
    tN = len(poses)//num_frames * num_frames
    frame_stamp = (np.linspace(0, tN , tN +1) - middle_frame_num)/num_frames
    poses['frame-stamp'] = frame_stamp


    # ------------ Change reference pose to identity --------------
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
    # ---------------------------------------------------------------

    # Poses file
    poses_file = os.path.join(output_root_dir, config['DAVIDE']['poses_folder'], "{}.csv".format(recording_name))
    print('Exporting poses to: ', poses_file)
    os.makedirs(os.path.dirname(poses_file), exist_ok=True)
    poses.to_csv(poses_file, sep=',', header=True, index=False)


def export_imu_data(start_id, end_id, input_video_dir, output_root_dir, recording_name, config):
    """Export imu data based on start and end ids."""
    # Get imu file
    imu_file = os.path.join(input_video_dir, config['DAVIDE-tmp']['imu_data'])
    # Read imu data
    imu_data = pd.read_csv(imu_file, sep=',')

    num_frames = config['DATA-GEN-PARAMS']['num_frames']
    middle_frame_num = num_frames // 2 if num_frames % 2 == 0 else num_frames // 2 + 1

    # Get start and end imu data
    imu_data = imu_data.iloc[start_id - middle_frame_num:end_id + (num_frames-middle_frame_num)+1]

    # Reset frame_stamps
    tN = len(imu_data)//num_frames * num_frames
    frame_stamp = (np.linspace(0, tN , tN +1) - middle_frame_num)/num_frames
    imu_data['frame-stamp'] = frame_stamp

    # Export imu data
    imu_file = os.path.join(output_root_dir, config['DAVIDE']['imu_folder'], "{}.csv".format(recording_name))
    print('Exporting imu data to: ', imu_file)
    os.makedirs(os.path.dirname(imu_file), exist_ok=True)
    imu_data.to_csv(imu_file, sep=',', header=True, index=False)


MAX_ITER = 50000


def main(argv):
    # Parse arguments and read config
    args = parse_args(argv)
    config = read_config(args.config)
    idx = args.id

    # Get root directory and video list
    input_root = config['DAVIDE-tmp']['ROOT']
    data_annotations_path = config['DATA-GEN-PARAMS']['annotations']
    annotations = pd.read_csv(data_annotations_path)
    video_list = annotations['recording'].values.tolist()
    input_video_dir = os.path.join(input_root, video_list[idx])
    print('Input video dir: ', input_video_dir)

    # Check previous steps are done
    for step in range(1, 8):
        if step == 6:
            # Step 6 is not required for this script
            continue
        if step == 7 and not args.mono_depth:
            # Step 7 is not required if mono depth is not required
            continue
        if not is_step_complete(dp_step='step_{}'.format(step), videos=video_list[idx], db_path=config['DATA-GEN-PARAMS']['dp_log']):
            raise ValueError(f"Step {step} is not done yet for video {video_list[idx]}. Check dp log.")

    # Read annotations
    annotations_file = config['DATA-GEN-PARAMS']['annotations']
    for _ in range(MAX_ITER):
        try:
            annotations = pd.read_csv(annotations_file)
            break
        except Exception:
            continue
    annotations = annotations.replace({np.nan: None})

    # Annotations for video id
    video_annotations = annotations[annotations['recording'] == video_list[idx]]

    # Start and end ids
    start_id, end_id = get_frame_ids(video_annotations['start'].values[0], video_annotations['end'].values[0], input_video_dir, config)

    if start_id == 0 and end_id == 0:
        print(f'No frames to export for video {video_list[idx]} according to annotations.')
        # Update log
        log_step_event(video_name=video_list[idx], dp_step='step_8', new_status=1, db_path=config['DATA-GEN-PARAMS']['dp_log'])
        update_summary_for_video(video_name=video_list[idx], db_path=config['DATA-GEN-PARAMS']['dp_log'])
        return

    # Recording name
    recording_name = convert_recording_name(video_list[idx], annotations)

    # Output video dir
    output_root_dir = os.path.join(config['DAVIDE']['ROOT'], video_annotations['split'].values[0])
    os.makedirs(output_root_dir, exist_ok=True)

    # Export blur folder
    export_blur_folder(start_id, end_id, input_video_dir, output_root_dir, recording_name, config)
    # Export sharp folder
    export_sharp_folder(start_id, end_id, input_video_dir, output_root_dir, recording_name, config)
    # Export depth folder
    export_depth_folder(start_id, end_id, input_video_dir, output_root_dir, recording_name, config)
    # Export confidence folder
    export_confidence_folder(start_id, end_id, input_video_dir, output_root_dir, recording_name, config)
    # Export intrinsics
    export_intrinsics(start_id, end_id, input_video_dir, output_root_dir, recording_name, config)
    # Export poses
    export_poses(start_id, end_id, input_video_dir, output_root_dir, recording_name, config)
    # Export imu data
    export_imu_data(start_id, end_id, input_video_dir, output_root_dir, recording_name, config)
    # Export mono depth folder if required
    if args.mono_depth:
        print('Exporting mono depth folders...')
        rgb_dir = 'sharp'
        export_mono_depth_folder(start_id, end_id, input_video_dir, output_root_dir, recording_name, config, rgb_dir)
        rgb_dir = 'blur'
        export_mono_depth_folder(start_id, end_id, input_video_dir, output_root_dir, recording_name, config, rgb_dir)

    # Update log
    log_step_event(video_name=video_list[idx], dp_step='step_8', new_status=1, db_path=config['DATA-GEN-PARAMS']['dp_log'])
    update_summary_for_video(video_name=video_list[idx], db_path=config['DATA-GEN-PARAMS']['dp_log'])
    print(f"Step 8 completed for video {video_list[idx]}.")


if __name__ == '__main__':
    main(sys.argv[1:])