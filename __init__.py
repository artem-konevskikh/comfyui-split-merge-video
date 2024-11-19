from .nodes.splitter import VideoSplitterNode
from .nodes.merger import VideoMergerNode

NODE_CLASS_MAPPINGS = {
    "VideoSplitter": VideoSplitterNode,
    "VideoMerger": VideoMergerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoSplitter": "Split Video into Segments",
    "VideoMerger": "Merge Video Segments",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
