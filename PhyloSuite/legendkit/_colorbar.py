from typing import Any, Dict

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colorbar import Colorbar as MPLColorbar
from matplotlib.patches import Ellipse, Polygon
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from ._locs import Locs


class Colorbar(MPLColorbar):
    """Colorbar based on Axes

    For other parameters, see `colorbar <matplotlib.color.Colorbar>`

    Parameters
    ----------
    mappable : :class:`ScalarMapping <matplotlib.cm.ScalarMappable>`
        The mappable whose colormap and norm will be used.
    norm : :class:`Normalize <matplotlib.colors.Normalize>`
        The normalization to use.
    cmap : :class:`Colormap <matplotlib.colors.Colormap>`
        The colormap to use.
    ax : :class:`Axes <matplotlib.axes.Axes>`
        The axes to draw colorbar.
    style : {'white', 'normal'}, default: 'white'
    width : float
        The width of colorbar
    height : float
        The height of colorbar
    loc : str
        Apart from the default location code, you can add 'out' as prefix
        to place the legend ouside the axes.
        See :ref:`all available options. <tutorial/title&layout:Legend Placement>`
    deviation : float
        The space between colorbar and axes if place outside
    bbox_to_anchor
    bbox_transform
    axes_class
    axes_kwargs
    borderpad
    orientation : {'vertical', 'horizontal'}
        The orientation of the colorbar
    title : str
        The title of colorbar
    alignment : {'left', 'right', 'center'}, default: 'center'
        The alignment of title and colorbar
    title_fontproperties
    colorbar_options : mapping
        Pass to :class:`matplotlib.colorbar.Colorbar`

    Examples
    --------

    .. plot::

        >>> from legendkit import colorbar
        >>> data = np.random.rand(10, 10)
        >>> mp = plt.pcolormesh(data, cmap="RdBu")
        >>> colorbar(mp)

    """

    def __repr__(self):
        return "<Colorbar>"

    def __init__(
            self,
            mappable=None,
            norm=None,
            cmap=None,
            *,
            ax: Axes = None,
            style: str = "white",  # normal, white
            shape: str = "rect",
            width: float = None,
            height: float = None,
            loc=None,
            deviation=0.05,
            bbox_to_anchor: Any = None,
            bbox_transform: Any = None,
            axes_class: Any = None,
            axes_kwargs: Any = None,
            borderpad: Any = 0,
            orientation: str = "vertical",
            title: str = None,
            alignment: str = "left",
            title_fontproperties: Dict = None,
            **colorbar_options,
    ):

        if ax is None:
            ax = plt.gca()
        if loc is None:
            loc = "out right center"

        if (width is None) & (height is None):
            width, height = (0.3, 1.5)
            # Flip width and height
            if orientation == 'horizontal':
                width, height = height, width
        elif (width is not None) & (height is not None):
            pass
        else:
            if width is None:
                width = 1.5 if orientation == "horizontal" else 0.3
            else:
                height = 0.3 if orientation == "horizontal" else 1.5

        loc, bbox_to_anchor, bbox_transform = \
            Locs().transform(ax, loc, bbox_to_anchor=bbox_to_anchor,
                             bbox_transform=bbox_transform,
                             deviation=deviation)

        axins = inset_axes(ax, width=width, height=height, borderpad=borderpad,
                           bbox_to_anchor=bbox_to_anchor,
                           bbox_transform=bbox_transform, loc=loc,
                           axes_class=axes_class, axes_kwargs=axes_kwargs,
                           )

        super().__init__(axins,
                         mappable,
                         norm=norm,
                         cmap=cmap,
                         orientation=orientation,
                         **colorbar_options)

        if style == "white":
            # Inward ticks and white color
            self._long_axis() \
                .set_tick_params(direction="in", color="white",
                                 width=1, size=5)
            self._long_axis() \
                .set_tick_params(which="minor",
                                 direction="in", color="white",
                                 )
            # turn off outlines
            self.outline.set_visible(0)

        if title is not None:
            if title_fontproperties is None:
                title_fontproperties = {'weight': 'bold', 'size': 'medium'}
            self.ax.set_title(title, loc=alignment,
                              fontdict=title_fontproperties)
        self.ax.set_facecolor('none')
        # shape clip not work for BoundaryNorm or CounterSet
        if self.solids is not None:
            if shape != "rect":
                self._long_axis().set_tick_params(width=0)
            if shape == "ellipse":
                xrange = self.get_xrange()
                yrange = self.get_yrange()
                patch = Ellipse(self.get_midpoint(), xrange, yrange,
                                facecolor='none')
                self.ax.add_patch(patch)
                self.solids.set_clip_path(patch)
            elif shape == "triangle":
                corner = self.get_corner()
                patch = Polygon([corner[0], corner[1], corner[2]],
                                facecolor='none')
                self.ax.add_patch(patch)
                self.solids.set_clip_path(patch)
            elif shape == "trapezoid":
                corner = self.get_corner()
                xrange = self.get_xrange()
                patch = Polygon([corner[0], corner[1], corner[2],
                                 (xrange / 2.5, corner[3][1])],
                                facecolor='none')
                self.ax.add_patch(patch)
                self.solids.set_clip_path(patch)
            else:
                pass

    def set_title(self, *args, **kw):
        self.ax.set_title(*args, **kw)

    def get_xrange(self):
        xlims = np.sort(self.ax.get_xlim())
        return xlims[1] - xlims[0]

    def get_yrange(self):
        ylims = np.sort(self.ax.get_ylim())
        return ylims[1] - ylims[0]

    def get_midpoint(self):
        xlims = np.sort(self.ax.get_xlim())
        ylims = np.sort(self.ax.get_ylim())
        xrange = xlims[1] - xlims[0]
        yrange = ylims[1] - ylims[0]
        xcenter = xlims[0] + xrange / 2
        ycenter = ylims[0] + yrange / 2
        return xcenter, ycenter

    def get_corner(self):
        """

        2-----3
        |     |
        |     |
        1-----4

        """
        xlims = np.sort(self.ax.get_xlim())
        ylims = np.sort(self.ax.get_ylim())
        return (xlims[0], ylims[0]), (xlims[0], ylims[1]), \
            (xlims[1], ylims[1]), (xlims[1], ylims[0])
