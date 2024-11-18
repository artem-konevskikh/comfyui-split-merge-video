# ComfyUI Video Processing Nodes

<span style="color:red;">**Note:** This project is under active development. It may not work at all. Features and documentation may change.</span>

Custom nodes for ComfyUI that add video splitting and merging capabilities with crossfade transitions.

## Features

- **Video Splitter Node**: Split long videos into segments with configurable overlap
  - Adjustable segment length and overlap
  - Customizable video/audio encoding settings
  - Progress reporting

- **Video Merger Node**: Merge video segments with smooth crossfade transitions
  - Configurable crossfade duration
  - Automatic segment ordering
  - Customizable output encoding

## Installation

### Method 1: Using ComfyUI Manager (Recommended)
1. Install [ComfyUI Manager](https://github.com/ltdrdata/ComfyUI-Manager)
2. Find "Video Processing Nodes" in the Manager and install it

### Method 2: Manual Installation
1. Navigate to your ComfyUI custom nodes directory:
```bash
cd ComfyUI/custom_nodes/
```

2. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/comfyui-video-nodes
```

3. Install the required dependencies:
```bash
cd comfyui-video-nodes
pip install -r requirements.txt
```

4. Restart ComfyUI

## Usage

### Video Splitter Node
- Input:
  - `video_path`: Path to the input video file
  - `segment_length`: Length of each segment (default: 10.0 seconds)
  - `overlap`: Overlap between segments (default: 2.0 seconds)
- Optional settings:
  - Video codec and bitrate
  - Audio codec and bitrate
  - Encoding preset
- Output:
  - Directory path containing the video segments

### Video Merger Node
- Input:
  - `segments_dir`: Directory containing the video segments
  - `fade_duration`: Duration of crossfade transition (default: 2.0 seconds)
- Optional settings:
  - Video codec and bitrate
  - Audio codec and bitrate
  - Encoding preset
- Output:
  - Path to the merged output video

## Example Workflow

1. Add the Video Splitter node to your workspace
2. Connect your video path to the node
3. Adjust segment length and overlap as needed
4. Add the Video Merger node
5. Connect the Splitter's output directory to the Merger's input
6. Run the workflow to get your processed video

## Encoding Options

Both nodes support the following encoding options:
- Video codecs: libx264, hevc
- Audio codecs: aac, libmp3lame, copy
- Encoding presets: ultrafast to veryslow
- Customizable video and audio bitrates

## Requirements

- Python 3.8 or higher
- moviepy >= 1.0.3
- numpy >= 1.22.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.