"""Dash package — analyst UI mounted under /analytics."""

from app.dash_app.app import create_dash_app

__all__ = ["create_dash_app"]
