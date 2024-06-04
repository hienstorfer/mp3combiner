import os
import tempfile
import traceback

from pydub import AudioSegment
from typing import List, Tuple

def log_error(output_folder: str, message: str) -> None:
    """
    Log an error message to the error log file in the output folder.

    Args:
        output_folder (str): Path to the folder where the error log file will be saved.
        message (str): Error message to be logged.

    Returns:
        None
    """
    error_log_path = os.path.join(output_folder, "error_log.txt")
    with open(error_log_path, "a") as log_file:
        log_file.write(message + "\n")

def preprocess_audio_to_temp(file_path: str, target_sample_rate: int = 44100) -> str:
    """
    Preprocess the audio file by converting to mono, normalizing sample rate,
    and saving it to a temporary file.

    Args:
        file_path (str): Path to the audio file.
        target_sample_rate (int): Target sample rate for the audio file.

    Returns:
        str: Path to the preprocessed temporary audio file.
    """
    audio = AudioSegment.from_file(file_path)
    audio = audio.set_frame_rate(target_sample_rate)
    audio = audio.set_channels(1)  # Ensure mono

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio.export(temp_file.name, format="wav")
    return temp_file.name


def find_matching_prefix_pairs(folder: str, prefix_left: str, prefix_right: str) -> List[Tuple[str, str]]:
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
        print("No matching pairs found for prefixes.")

    return matching_pairs


def find_matching_suffix_pairs(folder: str, suffix_left: str, suffix_right: str) -> List[Tuple[str, str]]:
    """
    Find matching pairs of files in a folder with given suffixes for left and right channels.

    Args:
        folder (str): Path to the folder containing the files.
        suffix_left (str): Suffix for the left channel files.
        suffix_right (str): Suffix for the right channel files.

    Returns:
        List[Tuple[str, str]]: List of tuples containing pairs of matching files (left_file, right_file).
    """
    if not os.path.exists(folder):
        raise FileNotFoundError(f"The folder {folder} does not exist.")

    files = os.listdir(folder)
    left_files = {f[:-len(suffix_left)]: f for f in files if f.endswith(suffix_left)}
    right_files = {f[:-len(suffix_right)]: f for f in files if f.endswith(suffix_right)}

    matching_pairs = [
        (os.path.join(folder, left_files[key]), os.path.join(folder, right_files[key]))
        for key in left_files if key in right_files
    ]

    if not matching_pairs:
        print("No matching pairs found for suffixes.")

    return matching_pairs


def combine_stereo_files(pairs: List[Tuple[str, str]], output_folder: str, prefix: str = "", suffix: str = "") -> None:
    """
    Combine pairs of MP3 files into stereo files with specified output folder.

    Args:
        pairs (List[Tuple[str, str]]): List of tuples containing pairs of matching files (left_file, right_file).
        output_folder (str): Path to the folder where the combined output files will be saved.
        prefix (str): Prefix for the combined output file.
        suffix (str): Suffix for the combined output file.

    Returns:
        None
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder {output_folder}.")

    temp_files = []

    try:
        for left_file, right_file in pairs:
            try:
                left_temp = preprocess_audio_to_temp(left_file)
                right_temp = preprocess_audio_to_temp(right_file)
                temp_files.extend([left_temp, right_temp])

                left_audio = AudioSegment.from_file(left_temp)
                right_audio = AudioSegment.from_file(right_temp)

                # Ensure the lengths match by trimming or padding the shorter audio with silence
                len_left = len(left_audio)
                len_right = len(right_audio)
                print(f"Original lengths - Left: {len_left}, Right: {len_right}")

                if len_left < len_right:
                    left_audio += AudioSegment.silent(duration=(len_right - len_left))
                elif len_right < len_left:
                    right_audio += AudioSegment.silent(duration=(len_left - len_right))

                # Verify the lengths after adjustment
                len_left = len(left_audio)
                len_right = len(right_audio)
                print(f"Lengths after adjustment - Left: {len_left}, Right: {len_right}")

                # Ensure both audio segments have the same number of frames
                frames_left = left_audio.frame_count()
                frames_right = right_audio.frame_count()
                print(f"Frame counts after adjustment - Left: {frames_left}, Right: {frames_right}")

                # Ensure exact frame match by trimming
                min_frames = min(int(frames_left), int(frames_right))
                left_audio = left_audio[:min_frames]
                right_audio = right_audio[:min_frames]

                # Verify final lengths and frame counts after trimming
                len_left = len(left_audio)
                len_right = len(right_audio)
                frames_left = left_audio.frame_count()
                frames_right = right_audio.frame_count()
                print(f"Final lengths after trimming - Left: {len_left}, Right: {len_right}")
                print(f"Final frame counts after trimming - Left: {frames_left}, Right: {frames_right}")

                combined_audio = AudioSegment.from_mono_audiosegments(left_audio, right_audio)

                if prefix:
                    base_filename = os.path.basename(left_file)[len(prefix_left):]  # Remove prefix
                    output_file = os.path.join(output_folder, f"{prefix}{suffix}{base_filename}")
                else:
                    base_filename = os.path.basename(left_file)[:-len(suffix_left)]  # Remove suffix
                    output_file = os.path.join(output_folder, f"{base_filename}{suffix}.mp3")

                combined_audio.export(output_file, format="mp3")
                print(f"Combined {left_file} and {right_file} into {output_file}")
            except Exception as e:
                print(f"Error processing files {left_file} and {right_file}: {e}")
                log_error(output_folder, error_message)
                log_error(output_folder, traceback.format_exc())
    finally:
        for temp_file in temp_files:
            os.remove(temp_file)


if __name__ == "__main__":
    folder_path = r"C:\path_to_your_folder"
    output_folder_path = r"C:\path_to_output_folder"

    prefix_left = "ES-"
    prefix_right = "FR-"
    suffix_left = "-ES.mp3"
    suffix_right = "-FR.mp3"

    try:
        # Handle prefix-based pairing
        prefix_pairs = find_matching_prefix_pairs(folder_path, prefix_left, prefix_right)
        combine_stereo_files(prefix_pairs, output_folder_path, prefix=f"{prefix_left[:-1]}-{prefix_right[:-1]}-",
                             suffix="")

        # Handle suffix-based pairing
        suffix_pairs = find_matching_suffix_pairs(folder_path, suffix_left, suffix_right)
        combine_stereo_files(suffix_pairs, output_folder_path, prefix="",
                             suffix=f"-{suffix_right[:-4]}-{suffix_left[:-4]}")
    except FileNotFoundError as e:
        print(e)
        log_error(output_folder_path, str(e))
        log_error(output_folder_path, traceback.format_exc())
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        log_error(output_folder_path, str(e))
        log_error(output_folder_path, traceback.format_exc())