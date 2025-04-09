# DAVIDE: Depth-Aware Video Deblurring (Dataset Synthesis)

This project contains the source code to synthesize the Depth-Aware VIdeo DEblurring (DAVIDE) dataset from raw captured videos, which is introduced in the technical report "DAVIDE: Depth-Aware Video Deblurring".

## Getting started
1. Install XVFI submodule, which is used for video interpolation:
    ```
    git submodule update --init
    ```
2. Install conda environments:

    * **DAVIDE-DP**: Used for data processing in general (steps 1,3,4,5,6,8).
        ```
        conda env create -n DAVIDE-DP -f dp_env.yml
        conda activate DAVIDE-DP
        pip install -r dp_requirements.txt
        ```
    * **XVFI**: Used for video interpolation (step 2). 
    
        Follow the steps in the [README](./XVFI/README.md).
    * **DAVIDE-MONO**: Used for monocular depth data (step 7).
        ```
        conda env create -n DAVIDE-MONO -f mono_env.yml
        conda activate DAVIDE-MONO
        pip install -r mono_requirements.txt
        ```
3. Update root directories in [config](./configs/config.yaml):
    * [`config['DAVIDE-raw']['ROOT']`](./configs/config.yaml#L2): Path to raw dataset.
    * [`config['DAVIDE-tmp']['ROOT']`](./configs/config.yaml#L9): Path to temporary processing folder.
    * [`config['DAVIDE']['ROOT']`](./configs/config.yaml#L28): Path to final dataset.
4. Create Dataset Processing log file ([`config['DATA-GEN-PARAMS']['dp_log']`](./configs/config.yaml#L41)):
    ```
    conda activate DAVIDE-DP
    cd misc
    python create_dp_log.py
    ```
## Dataset Synthesis
The dataset processing is performed sequentially for each of the 93 synchronized videos in the raw dataset. We use the environment variable SLURM_ARRAY_TASK_ID to index each video. The following example demonstrates the data processing steps for the first video clip (SLURM_ARRAY_TASK_ID=0).

1. RGB extraction:
    ```
    conda activate DAVIDE-DP
    cd scripts
    export SLURM_ARRAY_TASK_ID=0
    bash run_01_extract_rgb.sh
    ```
2. RGB video interpolation:
    ```
    conda activate XVFI
    cd scripts
    export SLURM_ARRAY_TASK_ID=0
    bash run_02_VFI.sh
    ```
3. Blur synthesis:
    ```
    conda activate DAVIDE-DP
    cd scripts
    export SLURM_ARRAY_TASK_ID=0
    bash run_03_rgb_blur.sh
    ```
4. Synchronized depth (Real depth captured by iPhone):
    ```
    conda activate DAVIDE-DP
    cd scripts
    export SLURM_ARRAY_TASK_ID=0
    bash run_03_rgb_blur.sh
    ```
5. Export camera data:
    ```
    conda activate DAVIDE-DP
    cd scripts
    export SLURM_ARRAY_TASK_ID=0
    bash run_05_camera_data.sh
    ```
6. Generate video samples for preliminary examination:
    ```
    conda activate DAVIDE-DP
    cd scripts
    export SLURM_ARRAY_TASK_ID=0
    bash run_06_sample-videos.sh
    ```
7. Compute monocular depth estimates:
    ```
    conda activate DAVIDE-MONO
    cd scripts
    export SLURM_ARRAY_TASK_ID=0
    bash run_07_mono_depth.sh
    ```
8. Select annotated data:
    ```
    conda activate DAVIDE-MONO
    cd scripts
    export SLURM_ARRAY_TASK_ID=0
    bash bash run_08_data_selection.sh
    ```
Alternatively, we provide SLURM scripts to generate the DAVIDE dataset for all the videos [here](./scripts/slurm/).

## License and Acknowledgements

This project is released under the [MIT license](LICENSE.txt). A big thanks to the original contributors of [XVFI](https://github.com/JihyongOh/XVFI).
        