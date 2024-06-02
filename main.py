import os
from pydub import AudioSegment
from typing import List, Tuple


def find_matching_pairs(folder: str, prefix_left: str, prefix_right: str) -> List[Tuple[str, str]]:
    """
    Find matching pairs of files in a folder with given prefixes for left and right channels.

    Args:
        folder (str): Path to the folder containing the files.
        prefix_left (str): Prefix for the left channel files.
        prefix_right (str): Prefix for the right channel files.

    Returns:
        List[Tuple[str, str]]: List of tuples containing pairs of matching files (left_file, right_file).
    """
    if not os.path.exists(folder):
        raise FileNotFoundError(f"The folder {folder} does not exist.")

    files = os.listdir(folder)
    left_files = {f[len(prefix_left):]: f for f in files if f.startswith(prefix_left)}
    right_files = {f[len(prefix_right):]: f for f in files if f.startswith(prefix_right)}

    matching_pairs = [
        (os.path.join(folder, left_files[key]), os.path.join(folder, right_files[key]))
        for key in left_files if key in right_files
    ]

    if not matching_pairs:
        print("No matching pairs found.")

    return matching_pairs


def combine_stereo_files(pairs: List[Tuple[str, str]], output_folder: str, prefix_left: str, prefix_right: str) -> None:
    """
    Combine pairs of MP3 files into stereo files with specified output folder.

    Args:
        pairs (List[Tuple[str, str]]): List of tuples containing pairs of matching files (left_file, right_file).
        output_folder (str): Path to the folder where the combined output files will be saved.
        prefix_left (str): Prefix for the left channel files.
        prefix_right (str): Prefix for the right channel files.

    Returns:
        None
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder {output_folder}.")

    for left_file, right_file in pairs:
        try:
            left_audio = AudioSegment.from_file(left_file).set_channels(1)
            right_audio = AudioSegment.from_file(right_file).set_channels(1)
        except Exception as e:
            print(f"Error processing files {left_file} and {right_file}: {e}")
            continue

        combined_audio = AudioSegment.from_mono_audiosegments(left_audio, right_audio)

        base_filename = os.path.basename(left_file)[len(prefix_left):]  # Remove left prefix
        output_file = os.path.join(output_folder, f"{prefix_left}{prefix_right}{base_filename}")

        try:
            combined_audio.export(output_file, format="mp3")
            print(f"Combined {left_file} and {right_file} into {output_file}")
        except Exception as e:
            print(f"Error exporting combined file {output_file}: {e}")


if __name__ == "__main__":
    folder_path = r"c:\e"
    output_folder_path = r"c:\audacityExport"
    prefix_left = "ES-"
    prefix_right = "HR-"

    try:
        pairs = find_matching_pairs(folder_path, prefix_left, prefix_right)
        combine_stereo_files(pairs, output_folder_path, prefix_left, prefix_right)
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
