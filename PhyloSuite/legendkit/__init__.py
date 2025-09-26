"""Legend creation and manipulation with ease for matplotlib"""

__version__ = "0.3.4"

from ._colorart import ColorArt
from ._colorbar import Colorbar
from ._legend import ListLegend, CatLegend, SizeLegend
# To register default setting and legend handlers
from ._register import register
from .layout import vstack, hstack

register()

colorbar = Colorbar
colorart = ColorArt
legend = ListLegend
cat_legend = CatLegend
size_legend = SizeLegend
