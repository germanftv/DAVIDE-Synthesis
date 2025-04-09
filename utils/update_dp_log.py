import sys
import pandas as pd
import argparse

MAX_ITER = 50000

def _parse_args(argv):
    parser = argparse.ArgumentParser(description='Updates dp log with new step status')
    parser.add_argument("--info_log", type=str, required=True, help='Path to info log')
    parser.add_argument("--recording", type=str, required=True, help='recording name')
    parser.add_argument("--step", type=int, required=True, help='step number')
    args = parser.parse_args(argv)
    return args

def update(info_log, recording, step):
    for _ in range(MAX_ITER):
        try:
            info = pd.read_csv(info_log)
            break
        except Exception:
            continue
    info.loc[info['recording'] == recording, 'step_{}'.format(step)] = True
    total = 0
    for i in range(1, 9):
        if info.loc[info['recording'] == recording, 'step_{}'.format(i)].values[0]:
            total += 1
    info.loc[info['recording'] == recording, 'total'] = int(total)
    info.to_csv(info_log, index=False)

def check_step(info_log, recording, step):
    for _ in range(MAX_ITER):
        try:
            info = pd.read_csv(info_log)
            break
        except Exception:
            continue
    return info.loc[info['recording'] == recording, 'step_{}'.format(step)].values[0]

def main(argv=None):
    args = _parse_args(argv)
    info_log = args.info_log
    recording = args.recording
    step = args.step
    update(info_log, recording, step)

if __name__ == '__main__':
    main(sys.argv[1:])