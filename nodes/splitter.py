"""Video Splitter Node for ComfyUI

This module provides a node for splitting videos into segments with configurable overlap
and encoding settings. The node is designed to work within the ComfyUI framework.
"""

from typing import Tuple, List
import os
from moviepy.editor import VideoFileClip
from . import VideoUtils, VideoEncodingSettings

class VideoSplitterNode:
    """
    ComfyUI node for splitting videos into overlapping segments.

    This node takes a video file and splits it into multiple segments of specified length
    with configurable overlap between segments. It supports various encoding options and
    provides progress reporting during processing.

    Attributes:
        RETURN_TYPES (tuple): Defines the return type as a string (comma-separated paths)
        FUNCTION (str): Name of the main processing function
        CATEGORY (str): Category in ComfyUI's node menu
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        """
        Define the input parameters for the node.

        Returns:
            Dictionary containing input parameter specifications
        """
        return {
            "required": {
                "video_path": ("STRING", {
                    "default": "", 
                    "multiline": False
                }),
                "prefix": ("STRING", {
                    "default": "split/segment_",
                    "multiline": False
                }),
                "segment_length": ("FLOAT", {
                    "default": 10.0,
                    "min": 3.0,
                    "max": 60.0,
                    "step": 1.0
                }),
                "overlap": ("FLOAT", {
                    "default": 2.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.5
                }),
            },
            "optional": {
                "video_codec": (VideoEncodingSettings.VALID_VIDEO_CODECS, {
                    "default": "libx264"
                }),
                "video_bitrate": ("STRING", {
                    "default": "8000k",
                    "multiline": False
                }),
                "audio_codec": (VideoEncodingSettings.VALID_AUDIO_CODECS, {
                    "default": "aac"
                }),
                "audio_bitrate": ("STRING", {
                    "default": "192k",
                    "multiline": False
                }),
                "preset": (VideoEncodingSettings.VALID_PRESETS, {
                    "default": "medium"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "split_video"
    CATEGORY = "video"

    def split_video(
        self,
        video_path: str,
        prefix: str = "split/segment_",
        segment_length: float = 10.0,
        overlap: float = 2.0,
        video_codec: str = "libx264",
        video_bitrate: str = "8000k",
        audio_codec: str = "aac",
        audio_bitrate: str = "192k",
        preset: str = "medium"
    ) -> Tuple[str]:
        """
        Split a video into segments with overlap.

        Args:
            video_path: Path to input video file
            prefix: Output filename prefix (can include directory structure)
            segment_length: Length of each segment in seconds
            overlap: Overlap between segments in seconds
            video_codec: Video codec for output segments
            video_bitrate: Video bitrate for output segments
            audio_codec: Audio codec for output segments
            audio_bitrate: Audio bitrate for output segments
            preset: Encoding preset name

        Returns:
            Tuple containing a comma-separated string of output file paths

        Raises:
            ValueError: If video file not found or processing fails
        """
        # Validate video path
        if not VideoUtils.validate_video_path(video_path):
            raise ValueError(f"Invalid video file: {video_path}")

        # Set up output directory and get encoding parameters
        output_dir, prefix_name = VideoUtils.setup_output_path(prefix)
        encoding_params = VideoEncodingSettings.get_encoding_params(
            video_codec, video_bitrate, audio_codec, audio_bitrate, preset
        )

        print(f"Loading video: {video_path}")
        video = VideoFileClip(video_path)
        duration = video.duration
        step = segment_length - overlap
        start_times = list(range(0, int(duration), int(step)))
        total_segments = len(start_times)

        print(f"Splitting video into {total_segments} segments...")
        segment_paths: List[str] = []

        for i, start in enumerate(start_times):
            progress = (i / total_segments) * 100
            print(f"Processing segment {i+1}/{total_segments} ({progress:.1f}%)")

            end = min(start + segment_length, duration)
            if end - start < 3:
                continue

            segment = video.subclip(start, end)
            output_path = os.path.join(
                output_dir,
                f"{prefix_name}{i:03d}_{start:05.1f}-{end:05.1f}.mp4"
            )

            segment.write_videofile(
                output_path,
                codec=encoding_params['codec'],
                bitrate=encoding_params['bitrate'],
                audio_codec=encoding_params['audio_codec'],
                audio_bitrate=encoding_params['audio_bitrate'],
                preset=encoding_params['preset'],
                threads=encoding_params['threads'],
                logger=None
            )
            segment.close()
            segment_paths.append(output_path)

        video.close()
        print("Video splitting completed!")
        return (",".join(segment_paths),)