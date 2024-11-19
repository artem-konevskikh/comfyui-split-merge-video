import os
import re
from collections import namedtuple
import numpy as np
from moviepy.editor import VideoFileClip, concatenate_videoclips

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

Segment = namedtuple("Segment", ["path", "start", "end"])


class VideoMergerNode:
    """
    ComfyUI node for merging video segments with crossfade and progress reporting
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "segments_paths": ("STRING", {"default": "", "multiline": False}),
                "prefix": ("STRING", {"default": "merged/output_", "multiline": False}),
                "fade_duration": (
                    "FLOAT",
                    {"default": 2.0, "min": 0.5, "max": 5.0, "step": 0.5},
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

    RETURN_TYPES = ("STRING",)  # Returns output file path
    FUNCTION = "merge_videos"
    CATEGORY = "video"

    def create_opacity_mask(
        self, clip, fade_in=False, fade_out=False, fade_duration=2.0
    ):
        def make_frame(t):
            mask = np.ones((clip.h, clip.w))
            if fade_in and t < fade_duration:
                mask = mask * (t / fade_duration)
            elif fade_out and t > (clip.duration - fade_duration):
                mask = mask * ((clip.duration - t) / fade_duration)
            return mask

        return clip.set_mask(clip.to_mask().fl(lambda gf, t: make_frame(t)))

    def extract_time_info(self, filename):
        match = re.search(r"_(\d+\.\d+)-(\d+\.\d+)\.mp4$", filename)
        if match:
            return float(match.group(1)), float(match.group(2))
        return None, None

    def merge_videos(
        self,
        segments_paths,
        prefix="merged/output_",
        fade_duration=2.0,
        video_codec="libx264",
        video_bitrate="8000k",
        audio_codec="aac",
        audio_bitrate="192k",
        preset="medium",
    ):
        # Split the comma-separated paths
        segment_paths = segments_paths.split(",")
        if not segment_paths:
            raise ValueError("No segment paths provided")

        # Handle directory in prefix
        output_dir = os.path.join(
            folder_paths.get_output_directory(), os.path.dirname(prefix)
        )
        os.makedirs(output_dir, exist_ok=True)

        # Get the actual prefix without directory
        prefix_name = os.path.basename(prefix)

        # Get and sort segments
        print("Analyzing video segments...")
        segments = []
        for path in segment_paths:
            if not os.path.exists(path):
                print(f"Warning: Segment not found: {path}")
                continue
            name = os.path.basename(path)
            start, end = self.extract_time_info(name)
            if start is not None and end is not None:
                segments.append(Segment(path=path, start=start, end=end))

        segments.sort(key=lambda x: x.start)

        if not segments:
            raise ValueError("No valid video segments found")

        # Load and process clips
        clips = []
        total_segments = len(segments)
        print(f"Found {total_segments} segments to merge")

        for i, segment in enumerate(segments):
            # Report loading progress
            print(
                f"Loading segment {i+1}/{total_segments} ({(i/total_segments)*100:.1f}%)"
            )
            clip = VideoFileClip(segment.path)

            if i > 0:
                clip = self.create_opacity_mask(
                    clip, fade_in=True, fade_duration=fade_duration
                )
            if i < total_segments - 1:
                clip = self.create_opacity_mask(
                    clip, fade_out=True, fade_duration=fade_duration
                )

            clips.append(clip)

        print("Concatenating clips...")
        final_clip = concatenate_videoclips(
            clips, method="compose", padding=-fade_duration
        )

        # Generate output path with prefix
        timestamp = segments[0].start
        output_file = os.path.join(output_dir, f"{prefix_name}{timestamp:05.1f}.mp4")

        print(f"Writing final video to: {output_file}")
        final_clip.write_videofile(
            output_file,
            codec=video_codec,
            bitrate=video_bitrate,
            audio_codec=audio_codec,
            audio_bitrate=audio_bitrate,
            preset=preset,
            threads=4,
            logger=None,
        )

        # Clean up
        print("Cleaning up...")
        for clip in clips:
            clip.close()
        final_clip.close()

        print("Video merging completed!")
        return (output_file,)
