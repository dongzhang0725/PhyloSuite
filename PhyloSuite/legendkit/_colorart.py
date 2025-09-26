#!/usr/bin/env python
#-*- coding:utf-8 -*-
# 移除 from __future__ import annotations

import matplotlib as mpl
import matplotlib.transforms as mtransforms
import numpy as np
from matplotlib import cm, contour, ticker, colors
from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.font_manager import FontProperties
from matplotlib.offsetbox import DrawingArea, VPacker, TextArea, \
    AnchoredOffsetbox
from matplotlib.patches import Rectangle
from matplotlib.text import Text

from ._locs import Locs

# 添加自定义函数替代 _api.check_in_list
def check_in_list(valid_values, **kwargs):
    """
    检查参数值是否在有效值列表中
    """
    for key, value in kwargs.items():
        if value not in valid_values:
            raise ValueError(
                f"'{value}' is not a valid value for {key}; "
                f"supported values are {', '.join(repr(x) for x in valid_values)}")
    return kwargs[list(kwargs.keys())[0]]

# 添加自定义函数替代 _api.check_getitem
def check_getitem(mapping, **kwargs):
    """
    从映射中获取项目
    """
    key = kwargs[list(kwargs.keys())[0]]
    try:
        return mapping[key]
    except KeyError:
        raise ValueError(
            f"'{key}' is not a valid value for {list(kwargs.keys())[0]}; "
            f"supported values are {', '.join(repr(x) for x in mapping)}")

def get_colormap(cmap):
    if isinstance(cmap, colors.Colormap):
        return cmap
    return mpl.colormaps.get(cmap)

class ColorArt(Artist):
    """Axes-independent colorbar

    Most of the time, it's safe to use :func:`colorart`
    as a drop-in replacement for :func:`colorbar`.

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
    alpha : float
        Control the transparency
    values :
    boundaries :
    flip : bool
        Flip the
    orientation : {'vertical', 'horizontal'}
        The orientation of colorart.
    ticks : list of ticks or Locator
    format : str or Formatter
    tick_width : float
        The width of tick.
    tick_size : float
        The length of tick.
    tick_color : color
        The color of tick.
    ticklocation : {'both', 'left', 'right', 'top', 'bottom'}
        The location of the colorbar ticks.
    width : float
        The width of colorart
    height : float
        The height of colorart
    borderpad : float, default: `rcParams["legend.borderpad"]`
        The fractional whitespace inside the colorart border,
        in font-size units.
    textpad : float, default: `rcParams["legend.handletextpad"]`
        The space between label and the colorart
    borderaxespad : float, default: `rcParams["legend.borderaxespad"]`
        The pad between the axes and colorart border, in font-size units.
    prop : :class:`FontProperties <matplotlib.font_manager.FontProperties>`
        The font properties of the colorart.
    fontsize : float
        The fontsize
    title : str
        The title of colorart
    title_fontsize : float
        The fontsize of title
    title_fontproperties : :class:`FontProperties <matplotlib.font_manager.FontProperties>`
        The fontproperties of title
    alignment : {'center', 'left', 'right'}, default: 'center'
        The alignment of the colorart and title.
    loc : str
        Apart from the default location code, you can add 'out' as prefix
        to place the legend ouside the axes.
        See :ref:`all available options. <tutorial/title&layout:Legend Placement>`
    deviation : float
        The space between colorbar and axes if place outside
    bbox_to_anchor
    bbox_transform
    rasterized : bool
        Whether to rasterize the colorart,
        reduce file size in vectorized backend.

    Examples
    --------

    .. plot::

        >>> from legendkit import colorart
        >>> data = np.random.rand(10, 10)
        >>> mp = plt.pcolormesh(data, cmap="RdBu")
        >>> colorart(mp)

    """

    def __repr__(self):
        return "<ColorArt>"

    def __init__(self,
                 mappable=None,
                 cmap=None,
                 norm=None,
                 *,
                 ax: Axes = None,
                 alpha=None,
                 values=None,
                 boundaries=None,
                 # extend=None,
                 # extendfrac=None,
                 # extendrect=False,
                 flip=False,
                 spacing='uniform',
                 orientation="vertical",

                 ticks=None,
                 format=None,
                 tick_width=1,
                 tick_size=0.25,
                 tick_color="white",
                 ticklabel_loc="auto",
                 ticklocation="both",

                 width: float = None,  # relative to fontsize
                 height: float = None,
                 # arguments from legend
                 borderpad: float = None,
                 textpad: float = None,
                 borderaxespad: float = None,

                 prop=None,
                 fontsize=None,
                 title=None,  # legend title
                 title_fontsize=None,  # legend title font size
                 title_fontproperties=None,  # legend title font size
                 alignment="left",

                 loc=None,
                 deviation=0.05,
                 bbox_to_anchor=None,
                 bbox_transform=None,

                 rasterized=True,

                 ):
        super().__init__()
        if ax is None:
            ax = plt.gca()
        self.is_axes = True
        if not isinstance(ax, Axes):
            self.is_axes = False
            self.figure = ax

        else:
            self.figure = ax.figure
            self.axes = ax
        if rasterized:
            # Force rasterization
            self._rasterized = True

        if mappable is None:
            mappable = cm.ScalarMappable(norm=norm, cmap=cmap)

        if mappable.get_array() is not None:
            mappable.autoscale_None()

        self.mappable = mappable
        cmap = mappable.cmap
        norm = mappable.norm

        if isinstance(mappable, contour.ContourSet):
            cs = mappable
            alpha = cs.get_alpha()
            boundaries = cs._levels
            values = cs.cvalues
            extend = cs.extend
            if ticks is None:
                ticks = ticker.FixedLocator(cs.levels, nbins=10)
        elif isinstance(mappable, Artist):
            alpha = mappable.get_alpha()

        check_in_list(['vertical', 'horizontal'], orientation=orientation)
        check_in_list(['both', 'left', 'right', 'top', 'bottom'],
                           ticklocation=ticklocation)
        check_in_list(['uniform', 'proportional'], spacing=spacing)

        extend = None
        if extend is None:
            if (not isinstance(mappable, contour.ContourSet)) \
                    and (getattr(cmap, 'colorbar_extend', False) is not False):
                extend = cmap.colorbar_extend
            elif hasattr(norm, 'extend'):
                extend = norm.extend
            else:
                extend = 'neither'
        self.extend = extend
        self.flip = flip
        self.alpha = None
        self.set_alpha(alpha)
        self.cmap = cmap
        self.norm = norm
        self.values = values
        self.boundaries = boundaries
        self.spacing = spacing
        self._inside = check_getitem(
            {'neither': slice(0, None), 'both': slice(1, -1),
             'min': slice(1, None), 'max': slice(0, -1)},
            extend=extend)
        self.orientation = orientation

        # handle locator
        self._locator = None
        self._formatter = None
        self._minorlocator = None
        self.__scale = None

        if np.iterable(ticks):
            self._locator = ticker.FixedLocator(ticks, nbins=len(ticks))
        else:
            self._locator = ticks  # Handle default in _ticker()

        if isinstance(format, str):
            # Check format between FormatStrFormatter and StrMethodFormatter
            try:
                self._formatter = ticker.FormatStrFormatter(format)
                _ = self._formatter(0)
            except TypeError:
                self._formatter = ticker.StrMethodFormatter(format)
        else:
            self._formatter = format

        self.tick_width = tick_width
        self.tick_size = tick_size
        self.tick_color = tick_color
        self.ticklocation = ticklocation
        self.ticklabel_loc = ticklabel_loc

        if fontsize is None:
            fontsize = mpl.rcParams["legend.fontsize"]
        # Copy from matplotlib/lib/plot_simple_tutorial.py
        if prop is None:
            self.prop = FontProperties(size=fontsize)
        else:
            self.prop = FontProperties._from_any(prop)
            if isinstance(prop, dict) and "size" not in prop:
                self.prop.set_size(mpl.rcParams["legend.fontsize"])

        self._fontsize = self.prop.get_size_in_points()
        self._set_height_width(height, width)
        self.title = title
        if title_fontsize is None:
            title_fontsize = mpl.rcParams["legend.title_fontsize"]
        self.title_fontsize = title_fontsize
        self.title_fontproperties = title_fontproperties
        self.alignment = alignment

        if loc is None:
            loc = "out right center"

        self._loc, self._bbox_to_anchor, self._bbox_transform = \
            Locs().transform(ax, loc, bbox_to_anchor=bbox_to_anchor,
                             bbox_transform=bbox_transform,
                             deviation=deviation)

        self.textpad = mpl.rcParams[
            'legend.handletextpad'] if textpad is None else textpad
        self.borderpad = mpl.rcParams[
            'legend.borderpad'] if borderpad is None else borderpad
        self.borderaxespad = mpl.rcParams[
            'legend.borderaxespad'] if borderaxespad is None else borderaxespad

        # the container for title, colorbar, ticks and tick labels
        self._final_pack = None
        self._cbar_box = None
        self._process_values()
        self._get_locator_formatter()
        self._get_ticks()
        self._make_cbar_box()

    def _set_height_width(self, height, width):
        if self.orientation == "vertical":
            if width is not None:
                self.width = width * self._fontsize
            else:
                self.width = 2. * self._fontsize
            if height is not None:
                self.height = height * self._fontsize
            else:
                self.height = 5 * self.width

        else:
            if height is not None:
                self.height = height * self._fontsize
            else:
                self.height = 2. * self._fontsize
            if width is not None:
                self.width = width * self._fontsize
            else:
                self.width = 5 * self.height

    def _make_cbar_box(self):
        locs, ticks1, ticks2, ticklabels, offset_string = self._get_ticks()
        x_offset, y_offset = self._get_text_size(ticklabels)
        da_width, da_height = self.width, self.height
        textpad = self.textpad * self._fontsize
        if self.orientation == "vertical":
            da_width = self.width + x_offset + textpad
        else:
            da_height = self.height + y_offset + textpad

        # Add cbar
        canvas = DrawingArea(da_width, da_height, clip=False)
        # self._add_color_patches(self._cbar_canvas)
        # canvas.set_figure(self.figure)
        canvas.figure = self.figure

        cmap_caller = get_colormap(self.cmap)
        colors_list = cmap_caller(np.arange(cmap_caller.N))

        if self.flip:
            colors_list = colors_list[::-1]

        rects = []
        if isinstance(self.norm, colors.BoundaryNorm):
            if self.orientation == "vertical":
                for i, (y1, y2) in enumerate(zip(locs, locs[1::])):
                    rects.append(Rectangle((0, y1), width=self.width,
                                           height=y2 - y1, fc=colors_list[i]))
            else:
                for i, (x1, x2) in enumerate(zip(locs, locs[1::])):
                    rects.append(Rectangle((x1, 0), width=x2 - x1,
                                           height=self.height,
                                           fc=colors_list[i]))
        else:
            x, y = 0, 0
            for c in colors_list:
                if self.orientation == "vertical":
                    dy = self.height / len(colors_list)
                    rh, rw = dy, self.width
                    y += dy
                else:
                    dx = self.width / len(colors_list)
                    rh, rw = self.height, dx
                    x += dx
                rects.append(Rectangle((x, y), width=rw, height=rh,
                                       fc=c, antialiased=False,
                                       alpha=self.alpha))

        patches = PatchCollection(rects, match_original=True)
        canvas.add_artist(patches)

        # Add ticks
        # the tick will only be added if shape is rect
        ticks1_lines = LineCollection(
            ticks1,
            color=self.tick_color, zorder=100,
            visible=True, linewidth=self.tick_width)

        ticks2_lines = LineCollection(
            ticks2,
            color=self.tick_color, zorder=100,
            visible=True, linewidth=self.tick_width)

        if self.ticklocation == "both":
            canvas.add_artist(ticks1_lines)
            canvas.add_artist(ticks2_lines)
        elif self.ticklocation in ["bottom", "left"]:
            canvas.add_artist(ticks1_lines)
        else:
            canvas.add_artist(ticks2_lines)

        label_x = self.width + textpad
        label_y = self.height + textpad
        va, ha = "bottom", "center"
        if self.orientation == "vertical":
            va, ha = "center", "left"
        options = dict(va=va, ha=ha, fontsize=self._fontsize,
                       fontproperties=self.prop)
        for loc, label in zip(locs, ticklabels):
            if self.orientation == "vertical":
                t = Text(label_x, loc, label, **options)
            else:
                t = Text(loc, label_y, label, **options)
            canvas.add_artist(t)

        if self.title is not None:
            if self.title_fontproperties is None:
                textprops = dict(fontweight='bold', fontsize=self.title_fontsize)
            else:
                textprops = dict(fontproperties=self.title_fontproperties)
            title_canvas = TextArea(self.title, textprops=textprops)
            title_pack = VPacker(pad=0,
                                 # A heuristic value to make the title
                                 # not overlap with labels
                                 sep=0.4 * self._fontsize,
                                 children=[title_canvas, canvas],
                                 align=self.alignment
                                 )
            # title_pack.set_figure(self.figure)
            title_pack.figure = self.figure
            final_pack = title_pack
        else:
            final_pack = canvas
        self._final_pack = final_pack
        self._cbar_box = AnchoredOffsetbox(
            self._loc, child=final_pack,
            pad=self.borderpad,
            borderpad=self.borderaxespad,
            bbox_transform=self._bbox_transform,
            bbox_to_anchor=self._bbox_to_anchor,
            frameon=False)
        # self._cbar_box.set_figure(self.figure)
        self._cbar_box.figure = self.figure
        if self.is_axes:
            self.axes.add_artist(self._cbar_box)
        else:
            self.figure.add_artist(self._cbar_box)

    def get_bbox(self, renderer=None):
        return self._final_pack.get_bbox(renderer=renderer)

    def get_window_extent(self, renderer=None):
        return self._final_pack.get_window_extent(renderer=renderer)

    def set_offset(self, offset):
        self._final_pack.set_offset(offset)

    def _get_text_size(self, ticklabels):
        """Used to get the proper size for drawing area"""
        renderer = self.figure.canvas.get_renderer()
        all_texts = []
        for t in ticklabels:
            text_obj = Text(0, 0, t, fontsize=self._fontsize,
                            fontproperties=self.prop)
            if self.is_axes:
                self.axes.add_artist(text_obj)
            else:
                self.figure.add_artist(text_obj)
            all_texts.append(text_obj)
        x_sizes, y_sizes = [], []
        for t in all_texts:
            bbox = t.get_window_extent(renderer)
            x_sizes.append(bbox.xmax - bbox.xmin)
            y_sizes.append(bbox.ymax - bbox.ymin)
            t.remove()  # so it won't be drawn
        dpi_cor = renderer.points_to_pixels(1.)
        x_offset = np.max(x_sizes) / dpi_cor
        y_offset = np.max(y_sizes) / dpi_cor
        return x_offset, y_offset

    def _process_values(self):
        if self.values is not None:
            # set self._boundaries from the values...
            self._values = np.array(self.values)
            if self.boundaries is None:
                # bracket values by 1/2 dv:
                b = np.zeros(len(self.values) + 1)
                b[1:-1] = 0.5 * (self._values[:-1] + self._values[1:])
                b[0] = 2.0 * b[1] - b[2]
                b[-1] = 2.0 * b[-2] - b[-3]
                self._boundaries = b
                return
            self._boundaries = np.array(self.boundaries)
            return

        # otherwise values are set from the boundaries
        if isinstance(self.norm, colors.BoundaryNorm):
            b = self.norm.boundaries
        elif isinstance(self.norm, colors.NoNorm):
            # NoNorm has N blocks, so N+1 boundaries, centered on integers:
            b = np.arange(self.cmap.N + 1) - .5
        elif self.boundaries is not None:
            b = self.boundaries
        else:
            # otherwise make the boundaries from the size of the cmap:
            N = self.cmap.N + 1
            b = np.linspace(0, 1, N)
        # add extra boundaries if needed:
        if self._extend_lower():
            b = np.hstack((b[0] - 1, b))
        if self._extend_upper():
            b = np.hstack((b, b[-1] + 1))

        # transform from 0-1 to vmin-vmax:
        # TODO: For CenteredNorm and TwoSlopeNorm
        #   Maybe need to ask user to scaled it first
        if isinstance(self.norm, colors.CenteredNorm):
            if self.norm.halfrange is None:
                self.norm.halfrange = 1
            self.norm.vmin = self.norm.vcenter - self.norm.halfrange
            self.norm.vmax = self.norm.vcenter + self.norm.halfrange

        if not self.norm.scaled():
            self.norm.vmin = 0
            self.norm.vmax = 1
        self.norm.vmin, self.norm.vmax = mtransforms.nonsingular(
            self.norm.vmin, self.norm.vmax, expander=0.1)
        if (not isinstance(self.norm, colors.BoundaryNorm) and
                (self.boundaries is None)):
            b = self.norm.inverse(b)

        self._boundaries = np.asarray(b, dtype=float)
        self._values = 0.5 * (self._boundaries[:-1] + self._boundaries[1:])
        if isinstance(self.norm, colors.NoNorm):
            self._values = (self._values + 0.00001).astype(np.int16)

    def _get_locator_formatter(self):
        """Determine the locator to get ticks"""
        locator = self._locator
        formatter = self._formatter
        minorlocator = self._minorlocator
        if isinstance(self.norm, colors.BoundaryNorm):
            b = self.norm.boundaries
            if locator is None:
                locator = ticker.FixedLocator(b, nbins=5)
            if minorlocator is None:
                minorlocator = ticker.FixedLocator(b)
        elif isinstance(self.norm, colors.NoNorm):
            if locator is None:
                # put ticks on integers between the boundaries of NoNorm
                nv = len(self._values)
                base = 1 + int(nv / 10)
                locator = ticker.IndexLocator(base=base, offset=0)
        elif isinstance(self.norm, colors.LogNorm):
            base = self.norm._scale.base
            if locator is None:
                locator = ticker.LogLocator(base=base)
            if formatter is None:
                formatter = ticker.LogFormatterSciNotation(base=base)
        elif isinstance(self.norm, colors.SymLogNorm):
            base = self.norm._scale.base
            if locator is None:
                locator = ticker.SymmetricalLogLocator(
                    linthresh=self.norm.linthresh, base=base)
            if formatter is None:
                formatter = ticker.LogFormatterSciNotation(base=base)
        elif self.boundaries is not None:
            b = self._boundaries[self._inside]
            if locator is None:
                locator = ticker.FixedLocator(b, nbins=5)
        else:
            # AsinhNorm is introduced at 3.6
            if hasattr(colors, 'AsinhNorm'):
                if isinstance(self.norm, colors.AsinhNorm):
                    base = 10  # self.norm._scale.base
                    if locator is None:
                        locator = ticker.AsinhLocator(
                            linear_width=self.norm.linear_width, base=base)
                    if formatter is None:
                        if base > 1:
                            formatter = ticker.LogFormatterSciNotation(
                                base=base)
                        else:
                            formatter = ticker.StrMethodFormatter('{x:.3g}')
            # most cases:
            if locator is None:
                # we haven't set the locator explicitly, so use the default
                # for this axis:
                locator = ticker.MaxNLocator(nbins=5, steps=[1, 2, 2.5, 5, 10])
            if minorlocator is None:
                minorlocator = ticker.NullLocator()

        if minorlocator is None:
            minorlocator = ticker.NullLocator()

        if formatter is None:
            formatter = ticker.ScalarFormatter()

        self._locator = locator
        self._formatter = formatter
        self._minorlocator = minorlocator

    def _get_ticks(self):
        if isinstance(self.norm, colors.NoNorm) and self.boundaries is None:
            intv = self._values[0], self._values[-1]
        else:
            intv = (np.nanmin(self._values), np.nanmax(self._values))

        locator = self._locator
        formatter = self._formatter
        locator.create_dummy_axis(minpos=intv[0])
        locator.axis.set_view_interval(*intv)
        locator.axis.set_data_interval(*intv)
        formatter.set_axis(locator.axis)

        b = np.array(locator())
        if isinstance(self.norm, colors.BoundaryNorm):
            pass
        elif isinstance(locator, ticker.LogLocator):
            eps = 1e-10
            b = b[(b <= intv[1] * (1 + eps)) & (b >= intv[0] * (1 - eps))]
            # b = b[(b >= intv[0] * (1 - eps))]
        else:
            eps = (intv[1] - intv[0]) * 1e-10
            b = b[(b <= intv[1] + eps) & (b >= intv[0] - eps)]
        locs, ticks1, ticks2 = self._locate(b)
        ticklabels = formatter.format_ticks(b)
        offset_string = formatter.get_offset()
        return locs, ticks1, ticks2, ticklabels, offset_string

    def _locate(self, v):
        if isinstance(self.norm, (colors.NoNorm, colors.BoundaryNorm)):
            arr = self._boundaries
            normalize = colors.Normalize(vmin=np.min(arr), vmax=np.max(arr))
            locs = np.array([normalize(i) for i in v])
        else:
            locs = np.array([self.norm(i) for i in v])

        h, w = self.height, self.width
        if self.orientation == "horizontal":
            h, w = w, h

        if isinstance(self.norm, colors.BoundaryNorm) & \
                (self.spacing == "uniform"):
            locs = np.linspace(0, h, len(locs))
        else:
            locs = (1 - locs) * h if self.flip else locs * h

        ticks1, ticks2 = [], []
        for loc in locs:
            if self.orientation == "vertical":
                t1 = [(0, loc), (w * self.tick_size, loc)]
                t2 = [(w, loc), (w * (1 - self.tick_size), loc)]
            else:
                t1 = [(loc, 0), (loc, w * self.tick_size)]
                t2 = [(loc, w), (loc, w * (1 - self.tick_size))]
            ticks1.append(t1)
            ticks2.append(t2)

        return locs, ticks1, ticks2

    def _extend_lower(self):
        """Return whether the lower limit is open ended."""
        minmax = "max" if self.flip else "min"
        return self.extend in ('both', minmax)

    def _extend_upper(self):
        """Return whether the upper limit is open ended."""
        minmax = "min" if self.flip else "max"
        return self.extend in ('both', minmax)

    def set_alpha(self, alpha):
        self.alpha = None if isinstance(alpha, np.ndarray) else alpha

    def get_children(self):
        return self._cbar_box

    def remove(self):
        self._cbar_box.remove()

    def set_border(self, *args):
        # TODO: allow user to draw border on the colorbar
        pass
