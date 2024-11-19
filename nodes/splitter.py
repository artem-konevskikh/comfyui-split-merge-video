import os
from moviepy.editor import VideoFileClip

# Try to import ComfyUI's folder_paths
try:
    import sys

    comfy_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sys.path.append(comfy_path)
    import folder_paths # type: ignore
except ImportError:
    print("Warning: ComfyUI's folder_paths module not found, using default paths")

    class FolderPaths:
        def get_output_directory():
            return os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

    folder_paths = FolderPaths


class VideoSplitterNode:
    """
    ComfyUI node for splitting videos into overlapping segments with progress reporting
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": "", "multiline": False}),
                "prefix": ("STRING", {"default": "split/segment_", "multiline": False}),
                "segment_length": (
                    "FLOAT",
                    {"default": 10.0, "min": 3.0, "max": 60.0, "step": 1.0},
                ),
                "overlap": (
                    "FLOAT",
                    {"default": 2.0, "min": 0.0, "max": 10.0, "step": 0.5},
                ),
            },
            "optional": {
                "video_codec": (["libx264", "hevc"], {"default": "libx264"}),
                "video_bitrate": ("STRING", {"default": "8000k", "multiline": False}),
                "audio_codec": (["aac", "libmp3lame", "copy"], {"default": "aac"}),
                "audio_bitrate": ("STRING", {"default": "192k", "multiline": False}),
                "preset": (
                    [
                        "ultrafast",
                        "superfast",
                        "veryfast",
                        "faster",
                        "fast",
                        "medium",
                        "slow",
                        "slower",
                        "veryslow",
                    ],
                    {"default": "medium"},
                ),
            },
        }

    RETURN_TYPES = ("STRING",)  # Returns list of file paths as a string
    FUNCTION = "split_video"
    CATEGORY = "video"

    def split_video(
        self,
        video_path,
        prefix="split/segment_",
        segment_length=10.0,
        overlap=2.0,
        video_codec="libx264",
        video_bitrate="8000k",
        audio_codec="aac",
        audio_bitrate="192k",
        preset="medium",
    ):
        # Validate video path
        if not os.path.exists(video_path):
            raise ValueError(f"Video file not found: {video_path}")

        # Handle directory in prefix
        output_dir = os.path.join(
            folder_paths.get_output_directory(), os.path.dirname(prefix)
        )
        os.makedirs(output_dir, exist_ok=True)

        # Get the actual prefix without directory
        prefix_name = os.path.basename(prefix)

        print(f"Loading video: {video_path}")
        video = VideoFileClip(video_path)
        duration = video.duration
        step = segment_length - overlap
        start_times = list(range(0, int(duration), int(step)))
        total_segments = len(start_times)

        print(f"Splitting video into {total_segments} segments...")
        segment_paths = []

        for i, start in enumerate(start_times):
            # Report progress
            progress = (i / total_segments) * 100
            print(f"Processing segment {i+1}/{total_segments} ({progress:.1f}%)")

            end = min(start + segment_length, duration)
            if end - start < 3:
                continue

            segment = video.subclip(start, end)
            output_path = os.path.join(
                output_dir, f"{prefix_name}{i:03d}_{start:05.1f}-{end:05.1f}.mp4"
            )

            # Write segment with specified encoding parameters
            segment.write_videofile(
                output_path,
                codec=video_codec,
                bitrate=video_bitrate,
                audio_codec=audio_codec,
                audio_bitrate=audio_bitrate,
                preset=preset,
                threads=4,
                logger=None,  # Suppress moviepy's internal progress bars
            )
            segment.close()
            segment_paths.append(output_path)

        video.close()
        print("Video splitting completed!")
        return (",".join(segment_paths),)  # Return paths as comma-separated string
