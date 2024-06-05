import os
import tempfile
import traceback

from pydub import AudioSegment
import librosa
import soundfile as sf
from typing import List, Tuple

def log_error(output_folder: str, message: str) -> None:
    """
    Log an error message to the error log file in the output folder.
    """
    error_log_path = os.path.join(output_folder, "error_log.txt")
    with open(error_log_path, "a") as log_file:
        log_file.write(message + "\n")

def preprocess_audio_to_temp(file_path: str, target_sample_rate: int = 44100) -> str:
    """
    Preprocess the audio file by converting to mono, normalizing sample rate,
    and saving it to a temporary file.
    """
    audio = AudioSegment.from_file(file_path)
    audio = audio.set_frame_rate(target_sample_rate)
    audio = audio.set_channels(1)  # Ensure mono

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio.export(temp_file.name, format="wav")
    return temp_file.name

def change_speed_without_pitch(file_path: str, speed_factor: float) -> str:
    """
    Change the speed of the audio file without altering the pitch.
    """
    y, sr = librosa.load(file_path, sr=None)
    y_fast = librosa.effects.time_stretch(y, rate=speed_factor)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    sf.write(temp_file.name, y_fast, sr)
    return temp_file.name

def find_matching_prefix_pairs(folder: str, prefix_left: str, prefix_right: str) -> List[Tuple[str, str]]:
    """
    Find matching pairs of files in a folder with given prefixes for left and right channels.
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

def combine_stereo_files(pairs: List[Tuple[str, str]], output_folder: str, prefix: str = "", suffix: str = "", speed_factor: float = 1.0, bitrate: str = "192k") -> None:
    """
    Combine pairs of MP3 files into stereo files with specified output folder.
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

                left_temp_speed = change_speed_without_pitch(left_temp, speed_factor)
                right_temp_speed = change_speed_without_pitch(right_temp, speed_factor)
                temp_files.extend([left_temp_speed, right_temp_speed])

                left_audio = AudioSegment.from_file(left_temp_speed)
                right_audio = AudioSegment.from_file(right_temp_speed)

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
                    output_file = os.path.join(output_folder, f"{prefix}{suffix}{speed_factor}-{base_filename}")
                else:
                    base_filename = os.path.basename(left_file)[:-len(suffix_left)]  # Remove suffix
                    output_file = os.path.join(output_folder, f"{base_filename}{suffix}-{speed_factor}.mp3")

                combined_audio.export(output_file, format="mp3", bitrate=bitrate)
                print(f"Combined {left_file} and {right_file} into {output_file}")
            except Exception as e:
                print(f"Error processing files {left_file} and {right_file}: {e}")
                log_error(output_folder, str(e))
                log_error(output_folder, traceback.format_exc())
    finally:
        for temp_file in temp_files:
            os.remove(temp_file)

if __name__ == "__main__":
    folder_path = r"C:\path_to_your_folder"
    output_folder_path = r"C:\path_to_output_folder"

    prefix_left = "RU-"
    prefix_right = "HR-"
    suffix_left = "-RU.mp3"
    suffix_right = "-HR.mp3"
    speed_factor = 1  # Change this to adjust the speed
    bitrate = "128k"  # Adjust the bitrate as needed

    try:
        # Handle prefix-based pairing
        prefix_pairs = find_matching_prefix_pairs(folder_path, prefix_left, prefix_right)
        combine_stereo_files(prefix_pairs, output_folder_path, prefix=f"{prefix_left[:-1]}-{prefix_right[:-1]}-", suffix="", speed_factor=speed_factor, bitrate=bitrate)

        # Handle suffix-based pairing
        suffix_pairs = find_matching_suffix_pairs(folder_path, suffix_left, suffix_right)
        combine_stereo_files(suffix_pairs, output_folder_path, prefix="", suffix=f"-{suffix_right[:-4]}-{suffix_left[:-4]}", speed_factor=speed_factor, bitrate=bitrate)
    except FileNotFoundError as e:
        print(e)
        log_error(output_folder_path, str(e))
        log_error(output_folder_path, traceback.format_exc())
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        log_error(output_folder_path, str(e))
        log_error(output_folder_path, traceback.format_exc())
