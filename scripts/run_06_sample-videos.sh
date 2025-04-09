#!/bin/bash
cd ..

CONFIG=./configs/config.yaml

VIDEOS_PATH_LIST=( )
ROOT=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'ROOT')")
VIDEO_LIST=( $(ls $ROOT) )
VIDEO=${VIDEO_LIST[$SLURM_ARRAY_TASK_ID]}
samples_folder=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'sample_videos', 'folder')")
mkdir -p "$(dirname "$ROOT/$VIDEO/$samples_folder")"
num_frames=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DATA-GEN-PARAMS', 'num_frames')")

# -------------------- Check dp log --------------------
DP_LOG=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DATA-GEN-PARAMS', 'dp_log')")
step_1=$(python -c "from utils import *;print(check_log_step('$DP_LOG', '$VIDEO', 1))")
step_2=$(python -c "from utils import *;print(check_log_step('$DP_LOG', '$VIDEO', 2))")
step_3=$(python -c "from utils import *;print(check_log_step('$DP_LOG', '$VIDEO', 3))")
step_4=$(python -c "from utils import *;print(check_log_step('$DP_LOG', '$VIDEO', 4))")
step_5=$(python -c "from utils import *;print(check_log_step('$DP_LOG', '$VIDEO', 5))")


if [ $step_1 == 'False' ] || [ $step_2 == 'False' ] || [ $step_3 == 'False' ] || [ $step_4 == 'False' ] || [ $step_5 == 'False' ]; then
    echo "Error: $VIDEO has not been processed yet"
    exit 1
fi
# -------------------- Temporary videos --------------------

# Depth for visualization
depth_folder=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'depth_folder')")
colored_depth_folder="tmp_depth-c" 

python -m utils.color_depth \
    --input_dir "$ROOT/$VIDEO/$depth_folder" \
    --output_dir "$ROOT/$VIDEO/$samples_folder/$colored_depth_folder"

INPUT="$ROOT/$VIDEO/$samples_folder/$colored_depth_folder/*.png"
tmp_depth_video="tmp_depth.mp4"

ffmpeg -framerate 20 -pattern_type glob -i "$INPUT" -c:v libx264 -crf 5 -pix_fmt yuv420p "$ROOT/$VIDEO/$samples_folder/$tmp_depth_video"

# IMU animations
imu_file=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'imu_data')")
tmp_imu_acc_animation="tmp_imu_acc_animation.mp4"
tmp_imu_gyro_animation="tmp_imu_gyro_animation.mp4"

python -m utils.animate_imu \
    --imu_file "$ROOT/$VIDEO/$imu_file" \
    --save "$ROOT/$VIDEO/$samples_folder/$tmp_imu_acc_animation" \
    --comp "acc" \
    --interval $num_frames

python -m utils.animate_imu \
    --imu_file "$ROOT/$VIDEO/$imu_file" \
    --save "$ROOT/$VIDEO/$samples_folder/$tmp_imu_gyro_animation" \
    --comp "rr" \
    --interval $num_frames

# Poses animation
poses_file=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'camera_poses')")
intrinsics_file=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'camera_intrinsics')")
tmp_poses_animation="tmp_poses_animation.mp4"

python -m utils.animate_poses \
    --poses_file "$ROOT/$VIDEO/$poses_file" \
    --intrinsics_file "$ROOT/$VIDEO/$intrinsics_file" \
    --save "$ROOT/$VIDEO/$samples_folder/$tmp_poses_animation"

# Sharp rgb video
sharp_folder=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'sharp_folder')")
INPUT="$ROOT/$VIDEO/$sharp_folder/*.png"
tmp_sharp_video="tmp_sharp.mp4"

ffmpeg -framerate 20 -pattern_type glob -i "$INPUT" -c:v libx264 -crf 5 -pix_fmt yuv420p "$ROOT/$VIDEO/$samples_folder/$tmp_sharp_video"

# Blur rgb video
blur_folder=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'blur_folder')")
INPUT="$ROOT/$VIDEO/$blur_folder/*.png"
tmp_blur_video="tmp_blur.mp4"

ffmpeg -framerate 20 -pattern_type glob -i "$INPUT" -c:v libx264 -crf 5 -pix_fmt yuv420p "$ROOT/$VIDEO/$samples_folder/$tmp_blur_video"

# -------------------- Sample videos --------------------

# Sample VFI
VFI_folder=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'VFI_folder')")
INPUT_PATH="$ROOT/$VIDEO/$VFI_folder/*.png"

sample_VFI=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'sample_videos', 'sample_vfi')")
OUTPUT_VIDEO="$ROOT/$VIDEO/$samples_folder/$sample_VFI"

ffmpeg -y -framerate 60 -pattern_type glob -i "$INPUT_PATH" -vf scale=960:720 -c:v libx264 -crf 15 -pix_fmt yuv420p $OUTPUT_VIDEO 

# Sample Blur + Sharp
sample_blur_sharp=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'sample_videos', 'sample_blur_sharp')")

echo "$ROOT/$VIDEO/$samples_folder/$sample_blur_sharp"
ffmpeg -y\
   -i "$ROOT/$VIDEO/$samples_folder/$tmp_blur_video" \
   -i "$ROOT/$VIDEO/$samples_folder/$tmp_sharp_video" \
  -filter_complex " \
      [0:v] setpts=PTS-STARTPTS, scale=960:720 [a0]; \
      [1:v] setpts=PTS-STARTPTS, scale=960:720 [a1]; \
      [a0][a1]xstack=inputs=2:layout=0_0|w0_0[out] \
      " \
    -map "[out]" \
    -c:v libx264 -crf 12 -pix_fmt yuv420p -f matroska $ROOT/$VIDEO/$samples_folder/$sample_blur_sharp

# Sample RGB + Depth
sample_rgb_depth=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'sample_videos', 'sample_rgb_depth')")

echo "$ROOT/$VIDEO/$samples_folder/$sample_rgb_depth"
ffmpeg -y\
   -i "$ROOT/$VIDEO/$samples_folder/$tmp_sharp_video" \
   -i "$ROOT/$VIDEO/$samples_folder/$tmp_depth_video" \
  -filter_complex " \
      [0:v] setpts=PTS-STARTPTS, scale=960:720 [a0]; \
      [1:v] setpts=PTS-STARTPTS, scale=960:720 [a1]; \
      [a0][a1]xstack=inputs=2:layout=0_0|w0_0[out] \
      " \
    -map "[out]" \
    -c:v libx264 -crf 12 -pix_fmt yuv420p -f matroska $ROOT/$VIDEO/$samples_folder/$sample_rgb_depth

# Sample RGB + Depth + IMU + Poses
sample_sync_summary=$(python -c "from configs import *;retrieve_attribute('$CONFIG', 'DAVIDE-tmp', 'sample_videos', 'sample_sync_summary')")

echo "$ROOT/$VIDEO/$samples_folder/$sample_sync_summary"
ffmpeg -y\
    -i "$ROOT/$VIDEO/$samples_folder/$tmp_blur_video" \
    -i "$ROOT/$VIDEO/$samples_folder/$tmp_sharp_video" \
    -i "$ROOT/$VIDEO/$samples_folder/$tmp_depth_video" \
    -i "$ROOT/$VIDEO/$samples_folder/$tmp_imu_acc_animation" \
    -i "$ROOT/$VIDEO/$samples_folder/$tmp_imu_gyro_animation" \
    -i "$ROOT/$VIDEO/$samples_folder/$tmp_poses_animation" \
    -filter_complex " \
        [0:v] setpts=PTS-STARTPTS, scale=720:540, drawtext=text='Blur':fontcolor=yellow:fontsize=28:x=5:y=5 [a0]; \
        [1:v] setpts=PTS-STARTPTS, scale=720:540, drawtext=text='Sharp':fontcolor=yellow:fontsize=28:x=5:y=5 [a1]; \
        [2:v] setpts=PTS-STARTPTS, scale=720:540, drawtext=text='Depth':fontcolor=yellow:fontsize=28:x=5:y=5 [a2]; \
        [3:v] setpts=PTS-STARTPTS, scale=720:540, drawtext=text='Acceleration':fontcolor=yellow:fontsize=28:x=5:y=5 [a3]; \
        [4:v] setpts=PTS-STARTPTS, scale=720:540, drawtext=text='Gyroscope':fontcolor=yellow:fontsize=28:x=5:y=5 [a4]; \
        [5:v] setpts=PTS-STARTPTS, scale=720:540, drawtext=text='Camera Poses':fontcolor=yellow:fontsize=28:x=5:y=5 [a5]; \
        [a0][a1][a2][a3][a4][a5]xstack=inputs=6:layout=0_0|w0_0|w0+w1_0|0_h0|w0_h0|w0+w1_h0[out] \
        " \
    -map "[out]" \
    -c:v libx264 -crf 12 -pix_fmt yuv420p -f matroska $ROOT/$VIDEO/$samples_folder/$sample_sync_summary

rm "$ROOT/$VIDEO/$samples_folder/$tmp_blur_video"
rm "$ROOT/$VIDEO/$samples_folder/$tmp_sharp_video"
rm "$ROOT/$VIDEO/$samples_folder/$tmp_depth_video"
rm "$ROOT/$VIDEO/$samples_folder/$tmp_imu_acc_animation"
rm "$ROOT/$VIDEO/$samples_folder/$tmp_imu_gyro_animation"
rm "$ROOT/$VIDEO/$samples_folder/$tmp_poses_animation"
rm -r "$ROOT/$VIDEO/$samples_folder/$colored_depth_folder"

# -------------------- Update dp log --------------------
STEP=6
python -m utils.update_dp_log --info_log $DP_LOG --recording $VIDEO --step $STEP
