MediaManager
============

A Python application for rendering video files complaint against user specified criteria

The following dependencies need to be resolved:

BeautifulSoup4
Install with pip install bs4

MediaInfo
Install according to distribution mediainfo such as "sudo apt-get install mediainfo"

FFMPEG
Install according to distribution the following:
ffmpeg

Changelog
=========

v0.1
-Initial offering provides ability to scan specified SOURCES for media files and stream copies video, converts audio where not ac3 and muxes to mkv container. If files comply with that criteria then they are ignored.

