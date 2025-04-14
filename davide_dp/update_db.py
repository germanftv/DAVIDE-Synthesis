import sys
import pandas as pd
import argparse

from davide_dp.utils import log_step_event, update_summary_for_video, NUMBER_OF_STEPS


def arg_parser(argv):
    parser = argparse.ArgumentParser(description='Updates dp log with new step status')
    parser.add_argument("--dp_log", type=str, required=True, help='Path to data processing log file')
    parser.add_argument("--recording", type=str, required=True, help='recording name')
    parser.add_argument("--step", type=int, required=True, help='step number')
    args = parser.parse_args(argv)
    return args


def main(argv):
    args = arg_parser(argv)
    dp_log = args.dp_log
    recording = args.recording
    step = args.step
    new_status = 1
    
    # Check if step and new_status are valid
    assert 1 <= step <= NUMBER_OF_STEPS, f"Step {step} is out of range. Must be between 1 and {NUMBER_OF_STEPS}."
    assert new_status in [0, 1], "New status must be either 0 or 1."
    dp_step = f'step_{step}'

    log_step_event(recording, dp_step, new_status, dp_log)
    update_summary_for_video(recording, dp_log)
    print(f"Updated {dp_step} status to {new_status} for recording {recording} in {dp_log}")


if __name__ == "__main__":
    main(sys.argv[1:])
