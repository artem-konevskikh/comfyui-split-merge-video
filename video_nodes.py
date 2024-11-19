import os
import re
from collections import namedtuple
import numpy as np
import folder_paths # type: ignore
from moviepy.editor import VideoFileClip, concatenate_videoclips

Segment = namedtuple("Segment", ["path", "start", "end"])

class VideoSplitterNode:
    """
    ComfyUI node for splitting videos into overlapping segments with progress reporting
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {
                    "default": "", 
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
                "video_codec": (["libx264", "hevc"], {
                    "default": "libx264"
                }),
                "video_bitrate": ("STRING", {
                    "default": "8000k",
                    "multiline": False
                }),
                "audio_codec": (["aac", "libmp3lame", "copy"], {
                    "default": "aac"
                }),
                "audio_bitrate": ("STRING", {
                    "default": "192k",
                    "multiline": False
                }),
                "preset": (["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"], {
                    "default": "medium"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "split_video"
    CATEGORY = "video"

    def split_video(self, video_path, segment_length=10.0, overlap=2.0, 
                   video_codec="libx264", video_bitrate="8000k",
                   audio_codec="aac", audio_bitrate="192k", 
                   preset="medium"):
        # Validate video path
        if not os.path.exists(video_path):
            raise ValueError(f"Video file not found: {video_path}")

        # Create output directory
        output_dir = os.path.join(folder_paths.get_temp_directory(), "video_segments")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"Loading video: {video_path}")
        video = VideoFileClip(video_path)
        duration = video.duration
        step = segment_length - overlap
        start_times = list(range(0, int(duration), int(step)))
        total_segments = len(start_times)

        print(f"Splitting video into {total_segments} segments...")
        for i, start in enumerate(start_times):
            # Report progress
            progress = (i / total_segments) * 100
            print(f"Processing segment {i+1}/{total_segments} ({progress:.1f}%)")

            end = min(start + segment_length, duration)
            if end - start < 3:
                continue

            segment = video.subclip(start, end)
            filename = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(
                output_dir,
                f"{filename}_segment_{i:03d}_{start:05.1f}-{end:05.1f}.mp4"
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
                logger=None  # Suppress moviepy's internal progress bars
            )
            segment.close()

        video.close()
        print("Video splitting completed!")
        return (output_dir,)

class VideoMergerNode:
    """
    ComfyUI node for merging video segments with crossfade and progress reporting
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "segments_dir": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "fade_duration": ("FLOAT", {
                    "default": 2.0,
                    "min": 0.5,
                    "max": 5.0,
                    "step": 0.5
                }),
            },
            "optional": {
                "video_codec": (["libx264", "hevc"], {
                    "default": "libx264"
                }),
                "video_bitrate": ("STRING", {
                    "default": "8000k",
                    "multiline": False
                }),
                "audio_codec": (["aac", "libmp3lame", "copy"], {
                    "default": "aac"
                }),
                "audio_bitrate": ("STRING", {
                    "default": "192k",
                    "multiline": False
                }),
                "preset": (["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"], {
                    "default": "medium"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "merge_videos"
    CATEGORY = "video"

    def create_opacity_mask(self, clip, fade_in=False, fade_out=False, fade_duration=2.0):
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

    def merge_videos(self, segments_dir, fade_duration=2.0,
                    video_codec="libx264", video_bitrate="8000k",
                    audio_codec="aac", audio_bitrate="192k",
                    preset="medium"):
        if not os.path.exists(segments_dir):
            raise ValueError(f"Segments directory not found: {segments_dir}")

        # Get and sort segments
        print("Analyzing video segments...")
        files = [f for f in os.listdir(segments_dir) if f.endswith(".mp4")]
        segments = []
        for file in files:
            start, end = self.extract_time_info(file)
            if start is not None and end is not None:
                segments.append(
                    Segment(path=os.path.join(segments_dir, file), start=start, end=end)
                )
        
        segments.sort(key=lambda x: x.start)
        
        if not segments:
            raise ValueError("No valid video segments found")

        # Load and process clips
        clips = []
        total_segments = len(segments)
        print(f"Found {total_segments} segments to merge")
        
        for i, segment in enumerate(segments):
            # Report loading progress
            print(f"Loading segment {i+1}/{total_segments} ({(i/total_segments)*100:.1f}%)")
            clip = VideoFileClip(segment.path)
            
            if i > 0:
                clip = self.create_opacity_mask(clip, fade_in=True, fade_duration=fade_duration)
            if i < total_segments - 1:
                clip = self.create_opacity_mask(clip, fade_out=True, fade_duration=fade_duration)
            
            clips.append(clip)

        print("Concatenating clips...")
        final_clip = concatenate_videoclips(clips, method="compose", padding=-fade_duration)
        
        # Generate output path
        output_file = os.path.join(folder_paths.get_output_directory(), "merged_video.mp4")
        
        print("Writing final video...")
        final_clip.write_videofile(
            output_file,
            codec=video_codec,
            bitrate=video_bitrate,
            audio_codec=audio_codec,
            audio_bitrate=audio_bitrate,
            preset=preset,
            threads=4,
            logger=None
        )

        # Clean up
        print("Cleaning up...")
        for clip in clips:
            clip.close()
        final_clip.close()
        
        print("Video merging completed!")
        return (output_file,)

# Register nodes
NODE_CLASS_MAPPINGS = {
    "VideoSplitter": VideoSplitterNode,
    "VideoMerger": VideoMergerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoSplitter": "Split Video into Segments",
    "VideoMerger": "Merge Video Segments"
}