"""NotebookLM Podcast Automator - Automate podcast creation and distribution.

This package provides tools to automate the process of creating and distributing
podcasts using NotebookLM and Spotify for Podcasters.
"""

from .core import NotebookLMAutomator, run_automation_with_urls
from .spotify import SpotifyAutomator

__version__ = "0.1.0"

__all__ = [
    'NotebookLMAutomator',
    'SpotifyAutomator',
    'run_automation_with_urls',
]