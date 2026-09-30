"""Backwards-compatible alias: image/video generation now live in image_service.py / video_service.py."""
from src.services.image_service import ImageService, enrich_prompt  # noqa: F401
from src.services.video_service import VideoService, enrich_video_prompt  # noqa: F401
from src.services.media_service import MediaResult, media_service  # noqa: F401

image_service = ImageService()
video_service = VideoService()
