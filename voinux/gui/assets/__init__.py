"""GUI assets and icon loading utilities."""

from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

# Assets directory
ASSETS_DIR = Path(__file__).parent


def load_svg_icon(icon_name: str, size: int = 48) -> QIcon:
    """Load an SVG icon as a QIcon.

    Args:
        icon_name: Name of the icon file (without .svg extension)
        size: Desired icon size in pixels

    Returns:
        QIcon: Loaded icon
    """
    svg_path = ASSETS_DIR / f"{icon_name}.svg"

    if not svg_path.exists():
        # Return empty icon if file doesn't exist
        return QIcon()

    # Load SVG and render to pixmap
    renderer = QSvgRenderer(str(svg_path))
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)  # Transparent background

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


def get_asset_path(filename: str) -> Path:
    """Get the full path to an asset file.

    Args:
        filename: Name of the asset file

    Returns:
        Path: Full path to the asset
    """
    return ASSETS_DIR / filename
