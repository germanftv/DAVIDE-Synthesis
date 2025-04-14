import os
import numpy as np
import struct
from skimage.transform import resize
# from skimage import io
import torch.utils.data as data
import cv2
import json
import torch
import pandas as pd


# Valid image extensions
IMG_EXTENSIONS = ['.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG', '.ppm', '.PPM', '.bmp', '.BMP', '.tif']

# Valid figure extensions
FIG_EXTENSIONS = ['.pdf', '.ps', '.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG', '.ppm', '.PPM', '.bmp', '.BMP',
                  '.tif']


def is_image_file(path: str) -> bool:
    """Check file for valid image formats.

    Parameters
    ----------
    path: str
        Path to file.

    Returns
    -------
    bool
        True if valid image file. False otherwise.

    """

    return any(path.endswith(extension) for extension in IMG_EXTENSIONS)


def get_image_path_list(path: str) -> list:
    """Get image path list from image folder.

    Parameters
    ----------
    path: str
        Path to folder with images.

    Returns
    -------
    list
        Image files inside folder
    """

    assert os.path.isdir(path), '{:s} is not a valid directory'.format(path)
    images = []
    for fname in os.listdir(path):
        if is_image_file(fname):
            images.append(os.path.join(path, fname))
    assert images, '{:s} has no valid image file'.format(path)
    images.sort()
    return images


def load_depth_bin(depth_name):
    with open(depth_name, mode='rb') as file:
        file_content = file.read()
    file_content = struct.unpack('f'* ((len(file_content)) // 4), file_content)
    depth = np.reshape(file_content, (192,256)).astype(np.float32)
    return depth


def load_conf_bin(conf_name):
    with open(conf_name, mode='rb') as file:
        file_content = file.read()
    file_content = struct.unpack('B'* ((len(file_content))), file_content)
    conf = np.reshape(file_content, (192,256)).astype(np.float32)
    # normalize conf
    conf = conf / np.max(conf)
    return conf


def read_depth_bin(path, img_shape=(192,256)):
    depth = load_depth_bin(path)
    depth = resize(depth, img_shape, anti_aliasing=True)
    return depth


def read_conf_bin(path, img_shape=(192,256)):
    conf = load_conf_bin(path)
    conf = resize(conf, img_shape, anti_aliasing=True)
    return conf


def save_depth_16bits(depth:np.float32, path):
    # check single channel
    assert len(depth.shape) == 2
    depth = depth.astype(np.float32) * 1000
    depth = np.clip(depth, 0, 65535)
    depth = depth.astype(np.uint16)
    cv2.imwrite(path, depth)


def read_depth_16bits(path):
    depth = cv2.imread(path, cv2.IMREAD_ANYDEPTH)
    depth = depth.astype(np.float32) / 1000
    return depth


def save_conf_8bits(conf:np.float32, path):
    # check single channel
    assert len(conf.shape) == 2
    conf = conf.astype(np.float32) * 255
    conf = conf.astype(np.uint8)
    # save conf with cv2 (8bits)
    cv2.imwrite(path, conf)



def read_txt_data(path):
    with open(path, 'r') as f:
        # Find the first line starting with "#"
        header = ''
        for line in f:
            if line.startswith('#'):
                header = line.strip()
                break

        # Use the header to create a list of column names
        column_names = header[1:].split(', ')

    poses = pd.read_csv(path, sep=",", comment="#", header=None, names=column_names)
    return poses


def imread(path: str, image_range=(-1.0, 1.0)) -> np.ndarray:
    """Read image file.

    Parameters
    ----------
    path: str
        Path to image file
    image_space: {'RGB', 'GBR'}, optional
        Color space.
    image_range: :obj:`tuple` of :obj:`int`
        Color range.

    Returns
    -------
    img: ndarray
        [MxNx3] array with color image.
    """

    assert is_image_file(path)
    # img = io.imread(path,)
    img = cv2.imread(path)
    img = img[:,:, [2,1,0]] # reverse order of channels (BGR -> RGB)

    # Normalize input range
    max_value = np.iinfo(img.dtype).max
    img = img.astype(np.float64) / max_value
    a, b = image_range
    img = (b-a)*img + a
        
    return img


def read_log(filename: str) -> dict:
    """Read log file.

    Args:
    ----------
        filename(str): Path to log file with json extension.

    Returns
    -------
        log(dict): Dictionary with log data.
    """
    file = open(filename, "r")
    contents = file.read()
    log = json.loads(contents)
    file.close()
    return log


def imread2Tensor(path):
    img = imread(path)
    img = torch.Tensor(img.transpose((2,0,1)).astype(float)).mul_(1.0) # [C,H,W]
    return img


def imsaveTensor(path, tensor):
    def denorm255_np(x):
        # numpy
        out = (x + 1.0) / 2.0
        return out.clip(0.0, 1.0) * 255.0
    img = np.transpose(np.squeeze(denorm255_np(tensor.detach().cpu().numpy())),
                       [1, 2, 0]).astype(np.uint8)
    # reverse order of channels (RGB -> BGR)
    img = img[:, :, [2, 1, 0]]
    cv2.imwrite(path, img)


def imsave(path, img):
    # reverse order of channels (RGB -> BGR)
    img = img[:, :, [2, 1, 0]]
    cv2.imwrite(path, img)


def read_video_paths(dir):
    frames = os.listdir(dir)
    frames.sort()
    frames_path = [os.path.join(dir, x) for x in frames]
    return frames_path


class VideoDataset(data.Dataset):
    def __init__(self, video_path, config):
        self.video_path = video_path

        self.multiple = config['DATA-GEN-PARAMS']['sr_factor']
        self.num_frames = config['DATA-GEN-PARAMS']['num_frames']
        self.frames_path = read_video_paths(self.video_path)
        self.nIterations = (len(self.frames_path) - 1) // (self.num_frames*self.multiple) * self.num_frames*self.multiple

        # Raise error if no images found in test_data_path.
        if len(self.frames_path) == 0:
            raise (RuntimeError("Found 0 files in subfolders of: " + self.args.input_dir + "\n"))

    def __getitem__(self, idx):
        frame_path = self.frames_path[idx]

        frame = imread2Tensor(frame_path)
        # including "np2Tensor [-1,1] normalized"

        return frame, idx

    def __len__(self):
        return self.nIterations
    

class CameraIntrinsics:
    def __init__(self, fx, fy, cx, cy):
        self.fx = fx
        self.fy = fy
        self.cx = cx
        self.cy = cy

    def average(self):
        self.fx = np.mean(self.fx)
        self.fy = np.mean(self.fy)
        self.cx = np.mean(self.cx)
        self.cy = np.mean(self.cy)

    @staticmethod
    def _to_matrix(fx, fy, cx, cy):
        return np.array([[fx, 0, cx],
                         [0, fy, cy],
                         [0, 0, 1]])
    
    def to_matrix(self):
        if self.fx is np.ndarray:
            matricies = []
            for i in range(self.fx.shape[0]):
                matricies.append(self._to_matrix(self.fx[i], self.fy[i], self.cx[i], self.cy[i]))
            return np.stack(matricies)
        else:
            return self._to_matrix(self.fx, self.fy, self.cx, self.cy)
        