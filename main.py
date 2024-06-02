import os
from pydub import AudioSegment
from typing import List, Tuple


def preprocess_audio(file_path: str, target_sample_rate: int = 44100) -> AudioSegment:
    """
    Preprocess the audio file by converting to mono, normalizing sample rate,
    and setting the target sample rate.

    Args:
        file_path (str): Path to the audio file.
        target_sample_rate (int): Target sample rate for the audio file.

    Returns:
        AudioSegment: Preprocessed audio segment.
    """
    audio = AudioSegment.from_file(file_path)
    audio = audio.set_frame_rate(target_sample_rate)
    audio = audio.set_channels(1)  # Ensure mono
    return audio


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
            left_audio = preprocess_audio(left_file)
            right_audio = preprocess_audio(right_file)

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
            left_audio = left_audio[:min_frames * left_audio.frame_rate // 1000]
            right_audio = right_audio[:min_frames * right_audio.frame_rate // 1000]

            # Verify final lengths and frame counts after trimming
            len_left = len(left_audio)
            len_right = len(right_audio)
            frames_left = left_audio.frame_count()
            frames_right = right_audio.frame_count()
            print(f"Final lengths after trimming - Left: {len_left}, Right: {len_right}")
            print(f"Final frame counts after trimming - Left: {frames_left}, Right: {frames_right}")

            combined_audio = AudioSegment.from_mono_audiosegments(left_audio, right_audio)

            base_filename = os.path.basename(left_file)[len(prefix_left):]  # Remove left prefix
            output_file = os.path.join(output_folder, f"{prefix_left}{prefix_right}{base_filename}")

            combined_audio.export(output_file, format="mp3")
            print(f"Combined {left_file} and {right_file} into {output_file}")
        except Exception as e:
            print(f"Error processing files {left_file} and {right_file}: {e}")


if __name__ == "__main__":
    folder_path = r"c:\path_to_your_folder"
    output_folder_path = r"c:\path_to_output_folder"
    prefix_left = "ES-"
    prefix_right = "HR-"

    try:
        pairs = find_matching_pairs(folder_path, prefix_left, prefix_right)
        combine_stereo_files(pairs, output_folder_path, prefix_left, prefix_right)
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
