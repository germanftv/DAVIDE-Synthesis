import cv2
import numpy as np
import os
import sys
import argparse
import torch
import matplotlib.pyplot as plt
from tqdm import tqdm
from configs import read_config


BORDER_CROP = 16
SAVE_PATH = './crf_calibration'


def cum_homography(H_list, ref_id):
    """Cumulates homography matrices."""
    # List of homography matrices
    H_cum_list = []

    # forward cumulation
    H_cum = np.eye(3)
    for i in range(ref_id-1, -1, -1):
        H_cum = np.dot(H_cum, H_list[i])
        H_cum_list.append(H_cum)
    # reverse list
    H_cum_list.reverse()
    
    # append identity matrix
    H_cum_list.append(np.eye(3))
    
    # backward cumulation
    H_cum = np.eye(3)
    for i in range(ref_id, len(H_list)):
        H_cum = np.dot(H_cum, np.linalg.inv(H_list[i]))
        H_cum_list.append(H_cum)
    
    return H_cum_list



def image_alignment(img_list, save_paths):
    """Aligns images using homography matrices."""

    print('Aligning images ...')
    # Ref image id
    ref_id = len(img_list) // 2 + 1
    print('Reference image id: ', ref_id)
    # List of homography matrices
    H_list = []
    # Read by pairs
    print('Computing homography matrices between consecutive ...')
    for i in tqdm(range(len(img_list)-1)):
        # Convert to gray
        img1 = cv2.cvtColor(img_list[i], cv2.COLOR_BGR2GRAY)
        img2 = cv2.cvtColor(img_list[i+1], cv2.COLOR_BGR2GRAY)

        # Initiate SIFT detector
        sift = cv2.SIFT_create()
        # find the keypoints and descriptors with SIFT
        kp1, des1 = sift.detectAndCompute(img1,None)
        kp2, des2 = sift.detectAndCompute(img2,None)

        # BFMatcher with default params
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1,des2,k=2)
        # Apply ratio test
        good = []
        for m,n in matches:
            if m.distance < (0.9-0.05*i)*n.distance:
                good.append([m])

        # Define empty matrices
        no_of_matches = len(good)
        p1 = np.zeros((no_of_matches, 2))
        p2 = np.zeros((no_of_matches, 2))
        
        for (i, match) in enumerate(good):
                p1[i, :] = kp1[match[0].queryIdx].pt
                p2[i, :] = kp2[match[0].trainIdx].pt
        
        # Find the homography matrix.
        Hi, Mi = cv2.findHomography(p1, p2, cv2.RANSAC)
        H_list.append(Hi)
    
    # Cumulate homography matrices
    H_cum_list = cum_homography(H_list, ref_id)
    print('Number of homography matrices: ', len(H_cum_list))
    print('Number of images: ', len(img_list))

    # Warp images
    img_list_aligned = []
    print('Warping images ...')
    for n, (img, H) in tqdm(enumerate(zip(img_list, H_cum_list))):
        if n == ref_id:
            img_list_aligned.append(img)
        else:
            img_aligned = cv2.warpPerspective(img, H, (img.shape[1], img.shape[0]))
            img_list_aligned.append(img_aligned)

        # Crop borders
        img_list_aligned[n] = img_list_aligned[n][BORDER_CROP:-BORDER_CROP, BORDER_CROP:-BORDER_CROP, :]
        # Save aligned images
        cv2.imwrite(save_paths[n], img_list_aligned[n])
    
    return img_list_aligned


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Estimates CRF from image bracket')
    parser.add_argument('-i', "--images", type=str, required=True, help='Directory of images for CRF estimation')
    parser.add_argument('-e', "--exposures", type=str, required=True, help='Path to file containing exposure times')
    parser.add_argument('-f', "--filename", type=str, required=True, help='Output crf file name')

    args = parser.parse_args(argv)
    return args


def main(argv=None):
    # Parse arguments
    args = parse_args(argv)
    plot_file = os.path.join(SAVE_PATH, args.filename + '.png')
    crf_file = os.path.join(SAVE_PATH, args.filename + '.pth')

    # Read images
    images_list = os.listdir(args.images)
    # check files are png  
    images_list = [img for img in images_list if (img.endswith('.png') or img.endswith('.jpg'))]
    # sort files
    images_list.sort()
    if len(images_list) == 0:
        print('No png files found in {}'.format(args.images))
        return
    img_list = [cv2.imread(os.path.join(args.images, img)) for img in images_list]

    # Image alignment
    save_paths = [os.path.join(args.images, 'aligned', img) for img in images_list]
    os.makedirs(os.path.join(args.images, 'aligned'), exist_ok=True)
    img_list_aligned = image_alignment(img_list, save_paths)


    # Read exposure times
    exposures_file = open(args.exposures, "r")
    exposures = exposures_file.readlines()
    exposures = np.array([float(eval(exposure.strip())) for exposure in exposures], dtype=np.float32)
    exposures_file.close()

    print('Computing CRF ...')

    # Debevec calibration
    cal = cv2.createCalibrateDebevec()
    crf_inv = cal.process(img_list_aligned, times=exposures)
    crf_inv = crf_inv.reshape(-1, 3)    # reshape to (N, 3)
    crf_inv = crf_inv[:, ::-1]          # reverse order of channels (BGR -> RGB)

    # 1st order approximation at RGB=250 to regularize extreme responses at RGB>251
    over_exposed_limit = 250
    diff = (crf_inv[over_exposed_limit+1] - crf_inv[over_exposed_limit-1])/2
    for i in range(over_exposed_limit+1, 256):
        crf_inv[i] = crf_inv[i-1] + diff

    # Save CRF
    torch.save(torch.from_numpy(crf_inv.copy()), crf_file)

    # Plot CRF
    crf_inv = crf_inv.transpose()
    fig, ax = plt.subplots()
    ax.plot(crf_inv[0], 'r')
    ax.plot(crf_inv[1], 'g')
    ax.plot(crf_inv[2], 'b')
    plt.grid()          # grid show
    plt.xlim([0, 255])
    plt.ylim([0, 30])
    plt.xlabel('Measured Intensity (8 bit)')
    plt.ylabel('Calibrated Relative Intensity (signal)')
    # save plot
    fig.savefig(plot_file)
    plt.close(fig)

    print('Estimated CRF saved to {}'.format(crf_file))


if __name__ == '__main__':
    sys.exit(main())
