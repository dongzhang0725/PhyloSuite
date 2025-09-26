# from __future__ import annotations
import io
import os
from collections import Counter, defaultdict
from copy import deepcopy
# from functools import cached_property
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import urlopen

import matplotlib.pyplot as plt
import numpy as np
from Bio import Phylo
from Bio.Phylo.BaseTree import Clade, Tree
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Patch, Rectangle
from matplotlib.text import Text
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar


class TreeViz:
    """Phylogenetic Tree Visualization Class"""

    def __init__(
            self,
            tree_data = None,
            *,
            format = "newick",
            height = 0.5,
            width = 8,
            orientation = "right",
            align_leaf_label = False,
            ignore_branch_length = False,
            leaf_label_size = 12,
            innode_label_size = 0,
            show_auto_innode_label = True,
            leaf_label_xmargin_ratio = 0.01,
            innode_label_xmargin_ratio = 0.01,
            reverse = False,
    ):
        """
        Parameters
        ----------
        tree_data : str | Path | Tree
            Tree data (`File`|`File URL`|`Tree Object`|`Tree String`)
        format : str, optional
            Tree format (`newick`|`phyloxml`|`nexus`|`nexml`|`cdao`)
        height : float, optional
            Figure height per leaf node of tree
        width : float, optional
            Figure width
        orientation : str, optional
            Tree orientation (`right`|`left`)
        align_leaf_label: bool, optional
            If True, align leaf label.
        ignore_branch_length : bool, optional
            If True, Ignore branch length for plotting tree.
        leaf_label_size : float, optional
            Leaf label size
        innode_label_size : float, optional
            Internal node label size
        show_auto_innode_label : bool, optional
            If True, show auto defined internal node label
            (e.g. `N_1`, `N_2`, ..., `N_XX`)
        leaf_label_xmargin_ratio : float, optional
            Leaf label x margin ratio
        innode_label_xmargin_ratio : float, optional
            Internal node label x margin ratio
        reverse : bool, optional
            Plot tree in reverse order
        """
        tree = self._load_tree(tree_data, format=format)

        # Set unique node name and branch length if not exists
        tree, auto_innode_labels = self._set_uniq_innode_name(tree)
        self._check_node_name_dup(tree)
        max_tree_depth = max(tree.depths().values())
        if ignore_branch_length or max_tree_depth == 0:
            tree = self._to_ultrametric_tree(tree)
        self._tree = tree

        # Plot parameters
        self._figsize = (width, height * self.tree.count_terminals())
        self._align_leaf_label = align_leaf_label
        self._leaf_label_size = leaf_label_size
        self._innode_label_size = innode_label_size
        self._show_auto_innode_label = show_auto_innode_label
        self._auto_innode_labels = auto_innode_labels
        self._leaf_label_xmargin_ratio = leaf_label_xmargin_ratio
        self._innode_label_xmargin_ratio = innode_label_xmargin_ratio
        self._reverse = reverse
        self._ax = None
        if orientation in ("right", "left"):
            self._orientation = orientation
        else:
            raise ValueError(f"{orientation} is invalid (`right` or `left`).")

        self._node2label_props = defaultdict(lambda: {})
        self._node2line_props = defaultdict(lambda: {})

        self._tree_line_kws = dict(color="black", lw=1, clip_on=False)
        self._tree_align_line_kws = dict(
            lw=0.5, ls="dashed", alpha=0.5, clip_on=False
        )

        # Plot objects
        self._plot_patches = []
        self._plot_funcs = []

    ############################################################
    # Properties
    ############################################################

    @property
    def tree(self):
        """BioPython's Tree Object"""
        return self._tree

    @property
    def figsize(self):
        """Figure size"""
        return self._figsize

    @property
    def xlim(self):
        """Axes xlim"""
        if self._orientation == "left":
            return (self.max_tree_depth, 0)
        else:
            return (0, self.max_tree_depth)

    @property
    def ylim(self):
        """Axes ylim"""
        return (0, self.tree.count_terminals() + 1)

    @property
    def leaf_labels(self):
        """Leaf labels"""
        return [str(n.name) for n in self.tree.get_terminals()]

    @property
    def innode_labels(self):
        """Internal node labels"""
        return [str(n.name) for n in self.tree.get_nonterminals()]

    @property
    def all_node_labels(self):
        """All node labels"""
        return self.leaf_labels + self.innode_labels

    @property
    def max_tree_depth(self):
        """Max tree depth (root -> leaf max branch length)"""
        return max(self.tree.depths().values())

    @property
    def name2xy(self):
        """Tree node name & node xy coordinate dict (alias for `name2xy_right`)"""
        return self.name2xy_right

    @property
    def name2xy_right(self):
        """Tree node name & node right xy coordinate dict"""
        return self._calc_name2xy_pos("right")

    @property
    def name2xy_center(self):
        """Tree node name & node center xy coordinate dict"""
        return self._calc_name2xy_pos("center")

    @property
    def name2xy_left(self):
        """Tree node name & node left xy coordinate dict"""
        return self._calc_name2xy_pos("left")

    @property
    def name2rect(self):
        """Tree node name & rectangle dict"""
        return self._calc_name2rect()

    @property
    def ax(self):
        """Plot axes

        Can't access `ax` property before calling `tv.plotfig()` method
        """
        if self._ax is None:
            err_msg = "Can't access ax property before calling `tv.plotfig()` method"
            raise ValueError(err_msg)
        return self._ax

    ############################################################
    # Public Method
    ############################################################

    def show_branch_length(
            self,
            *,
            size = 8,
            xpos = "center",
            ypos = "top",
            xmargin_ratio = 0.01,
            ymargin_ratio = 0.05,
            label_formatter = None,
            **kwargs,
    ):
        """Show branch length text label on each branch

        Parameters
        ----------
        size : int, optional
            Text size
        xpos : str, optional
            X position of plot text (`left`|`center`|`right`)
        ypos : str, optional
            Y position of plot text (`top`|`center`|`bottom`)
        xmargin_ratio : float, optional
            Text x margin ratio. If `xpos = center`, this param is ignored.
        ymargin_ratio : float, optional
            Text y margin ratio. If `ypos = center`, this param is ignored.
        label_formatter : Callable[[float], str] | None, optional
            User-defined branch length value label format function
            (e.g. `lambda v: f"{v:.3f}"`)
        **kwargs : dict, optional
            Text properties (e.g. `color="red", bbox=dict(color="skyblue"), ...`)
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.text.html>
        """
        for node in self.tree.find_clades():
            branch_length = node.branch_length
            if node == self.tree.root or branch_length is None:
                continue
            # Format label
            if label_formatter:
                label = label_formatter(float(branch_length))
            elif str(branch_length).isdigit():
                label = str(branch_length)
            else:
                label = f"{float(branch_length):.2f}"

            self.text_on_branch(
                str(node.name),
                label,
                size=size,
                xpos=xpos,
                ypos=ypos,
                xmargin_ratio=xmargin_ratio,
                ymargin_ratio=ymargin_ratio,
                **kwargs,
            )

    def show_confidence(
            self,
            *,
            size = 8,
            xpos = "center",
            ypos = "bottom",
            xmargin_ratio = 0.01,
            ymargin_ratio = 0.05,
            label_formatter = None,
            **kwargs,
    ):
        """Show confidence text label on each branch

        Parameters
        ----------
        size : int, optional
            Text size
        xpos : str, optional
            X position of plot text (`left`|`center`|`right`)
        ypos : str, optional
            Y position of plot text (`top`|`center`|`bottom`)
        xmargin_ratio : float, optional
            Text x margin ratio. If `xpos = center`, this param is ignored.
        ymargin_ratio : float, optional
            Text y margin ratio. If `ypos = center`, this param is ignored.
        label_formatter : Callable[[float], str] | None, optional
            User-defined confidence value label format function
            (e.g. `lambda v: f"{v:.3f}"`)
        **kwargs : dict, optional
            Text properties (e.g. `color="red", bbox=dict(color="skyblue"), ...`)
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.text.html>
        """
        node: Clade
        for node in self.tree.find_clades():
            confidence = node.confidence
            if confidence is None:
                continue
            # Format label
            if label_formatter:
                label = label_formatter(float(confidence))
            elif str(confidence).isdigit():
                label = str(confidence)
            else:
                label = f"{float(confidence):.2f}"

            self.text_on_branch(
                str(node.name),
                label,
                size=size,
                xpos="right" if node == self.tree.root and xpos == "center" else xpos,
                ypos=ypos,
                xmargin_ratio=xmargin_ratio,
                ymargin_ratio=ymargin_ratio,
                **kwargs,
            )

    def show_scale_axis(
            self,
            *,
            ticks_interval= None,
            ypos= 0,
    ):
        """Show scale axis

        Parameters
        ----------
        ticks_interval : float | None, optional
            Ticks interval. If None, interval is automatically defined.
        ypos : float, optional
            Y position of axis.
        """

        def plot_scale_axis(ax: Axes):
            ax.tick_params(bottom=True, labelbottom=True)
            ax.spines["bottom"].set_visible(True)
            ax.spines["bottom"].set_position(("data", ypos))
            if ticks_interval:
                stop = self.max_tree_depth + (ticks_interval / 100)
                xticks = np.arange(0, stop, ticks_interval)
                ax.set_xticks(xticks)  # type: ignore

        self._plot_funcs.append(plot_scale_axis)

    def show_scale_bar(
            self,
            *,
            scale_size = None,
            text_size = 8,
            loc = "lower left",
            label_top = False,
    ):
        """Show scale bar

        Parameters
        ----------
        scale_size : float | None, optional
            Scale size. If None, size is automatically defined.
        text_size : float | None, optional
            Text label size
        loc : str, optional
            Bar location (e.g. `lower left`, `upper left`)
        label_top : bool, optional
            If True, plot label on top. If False, plot label on bottom.
        """

        def plot_scale_bar(ax: Axes):
            auto_size = ax.get_xticks()[1]  # type: ignore
            scale = AnchoredSizeBar(
                ax.transData,
                size=auto_size if scale_size is None else scale_size,
                label=str(auto_size) if scale_size is None else str(scale_size),
                loc=loc,
                label_top=label_top,
                frameon=False,
                fontproperties=FontProperties(size=text_size),  # type: ignore
            )
            ax.add_artist(scale)

        self._plot_funcs.append(plot_scale_bar)

    def highlight(
            self,
            query,
            color,
            *,
            alpha = 0.5,
            area = "branch-label",
            **kwargs,
    ):
        """Plot highlight for target node

        Parameters
        ----------
        query : str | list[str] | tuple[str]
            Search query node name(s) for highlight. If multiple node names are set,
            MRCA(Most Recent Common Ancester) node is set.
        color : str
            Highlight color
        alpha : float
            Highlight color alpha(transparancy) value
        area : str
            Highlight area (`branch`|`branch-label`|`full`)
        **kwargs : dict, optional
            Rectangle properties (e.g. `alpha=0.5, ec="grey", lw=1.0, ...`)
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.Rectangle.html>
        """
        if area not in ("branch", "branch-label", "full"):
            raise ValueError(f"{area} is invalid ('branch'|'branch-label'|'full').")

        # Set rectangle properties
        target_node_name = self._search_target_node_name(query)
        rect = deepcopy(self.name2rect[target_node_name])
        rect.set_color(color)
        rect.set_alpha(alpha)
        kwargs.setdefault("lw", 0)
        kwargs.setdefault("zorder", 0)
        kwargs.setdefault("clip_on", False)
        rect.set(**kwargs)

        def plot_highlight(ax: Axes):
            if area == "branch-label":
                texts_rect = self._get_texts_rect(query)
                texts_rect_xmax = texts_rect.get_x() + texts_rect.get_width()
                rect.set_width(texts_rect_xmax - rect.get_x())
            elif area == "full":
                texts_rect = self._get_texts_rect(self.leaf_labels)
                texts_rect_xmax = texts_rect.get_x() + texts_rect.get_width()
                rect.set_width(texts_rect_xmax - rect.get_x())
            ax.add_patch(deepcopy(rect))

        self._plot_funcs.append(plot_highlight)

    def annotate(
            self,
            query,
            label,
            *,
            text_size = 10,
            text_color = "black",
            text_orientation = "horizontal",
            line_color = "black",
            xmargin_ratio = 0.01,
            align = False,
            text_kws = None,
            line_kws = None,
    ):
        """Annotate tree clade with line & text label

        Parameters
        ----------
        query : str | list[str] | tuple[str]
            Search query node name(s) for annotate. If multiple node names are set,
            MRCA(Most Recent Common Ancester) node is set.
        label : str
            Label name
        text_size : float, optional
            Text size
        text_color : str, optional
            Text color
        text_orientation : str, optional
            Text orientation (`horizontal`|`vertical`)
        line_color : str, optional
            Line color
        xmargin_ratio : float, optional
            X margin ratio
        align : bool, optional
            If True, annotate position is aligned to rightmost edge.
        text_kws : dict[str, Any] | None, optional
            Text properties
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.text.html>
        line_kws : dict[str, Any] | None, optional
            Axes.plot properties (e.g. dict(lw=2.0, ls="dashed", ...))
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.plot.html>
        """
        text_kws = {} if text_kws is None else deepcopy(text_kws)
        line_kws = {} if line_kws is None else deepcopy(line_kws)

        line_kws.setdefault("lw", 1)
        line_kws.update(dict(color=line_color, clip_on=False))
        text_kws.update(dict(size=text_size, color=text_color, va="center", ha="left"))
        if self._orientation == "left":
            text_kws.update(ha="right")
        if text_orientation == "horizontal":
            text_kws.update(dict(rotation=0))
        elif text_orientation == "vertical":
            text_kws.update(dict(rotation=-90))
        else:
            err_msg = f"{text_orientation} is invalid (`horizontal`|`vertical)"
            raise ValueError(err_msg)

        def plot_annotate(ax: Axes):
            # Get target texts entire rectangle
            texts_rect = self._get_texts_rect(query)
            xmin, ymin = texts_rect.xy
            xmax, ymax = xmin + texts_rect.get_width(), ymin + texts_rect.get_height()
            xmargin = self.max_tree_depth * xmargin_ratio

            if align:
                all_texts_rect = self._get_texts_rect(self.leaf_labels)
                xmax = all_texts_rect.get_x() + all_texts_rect.get_width()

            # Plot annotate line
            line_x = [xmax + xmargin] * 2
            line_y = [ymin, ymax]
            ax.plot(line_x, line_y, **line_kws)

            # Plot annotate label
            text_x, text_y = line_x[0] + xmargin, sum(line_y) / 2
            ax.text(text_x, text_y, label, **text_kws)

        self._plot_funcs.append(plot_annotate)

    def marker(
            self,
            query,
            marker = "o",
            *,
            size = 6,
            descendent = False,
            **kwargs,
    ):
        """Plot marker on target node(s)

        Parameters
        ----------
        query : str | list[str] | tuple[str]
            Search query node name(s) for plotting marker.
            If multiple node names are set,
            MRCA(Most Recent Common Ancester) node is set.
        marker : str, optional
            Marker type (e.g. `o`, `s`, `D`, `P`, `*`, `x`, `d`, `^`, `v`, `<`, `>`)
            <https://matplotlib.org/stable/api/markers_api.html>
        size : int, optional
            Marker size
        descendent : bool, optional
            If True, plot markers on target node's descendent as well.
        **kwargs : dict, optional
            Axes.scatter properties (e.g. `color="red", ec="black", alpha=0.5, ...`)
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.scatter.html>
        """
        target_node_name = self._search_target_node_name(query)

        if descendent:
            clade = next(self.tree.find_clades(target_node_name))
            descendent_nodes = list(clade.find_clades())
            x, y = [], []
            for descendent_node in descendent_nodes:
                node_x, node_y = self.name2xy[str(descendent_node.name)]
                if descendent_node.is_terminal() and self._align_leaf_label:
                    node_x = max(self.xlim)
                x.append(node_x)
                y.append(node_y)
        else:
            x, y = self.name2xy[target_node_name]
            target_node = next(self.tree.find_clades(target_node_name))
            if target_node.is_terminal() and self._align_leaf_label:
                x = max(self.xlim)

        kwargs.setdefault("clip_on", False)
        kwargs.setdefault("zorder", 2.0)

        def plot_marker(ax: Axes):
            ax.scatter(x, y, s=size**2, marker=marker, **kwargs)  # type: ignore

        self._plot_funcs.append(plot_marker)

    def link(
            self,
            query1,
            query2,
            *,
            pos1 = "center",
            pos2 = "center",
            color = "red",
            linestyle = "dashed",
            arrowstyle = "-|>",
            connectionstyle = "arc3,rad=0",
            **kwargs,
    ):
        """Plot link line between target nodes

        Parameters
        ----------
        query1 : str | list[str] | tuple[str]
            Search query node name(s) for setting link start node.
            If multiple node names are set,
            MRCA(Most Recent Common Ancester) node is set.
        query2 : str | list[str] | tuple[str]
            Search query node name(s) for setting link end node.
            If multiple node names are set,
            MRCA(Most Recent Common Ancester) node is set.
        pos1 : str, optional
            Link start node branch position1 (`left`|`center`|`right`)
        pos2 : str, optional
            Link end node branch position2 (`left`|`center`|`right`)
        color : str, optional
            Link line color
        linestyle : str, optional
            Line line style (e.g. `dotted`, `dashdot`, `solid`)
        arrowstyle : str, optional
            Arrow style (e.g. `-`, `->`, `<->`, `<|-|>`)
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.ArrowStyle.html>
        connectionstyle : str, optional
            Connection style (e.g. `arc3,rad=0.2`, `arc3,rad=-0.5`)
            <https://matplotlib.org/stable/gallery/userdemo/connectionstyle_demo.html>
        **kwargs : dict, optional
            PathPatch properties (e.g. `lw=0.5, alpha=0.5, zorder=0, ...`)
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.PathPatch.html>
        """
        target_node_name1 = self._search_target_node_name(query1)
        target_node_name2 = self._search_target_node_name(query2)

        xy1 = self._get_target_pos_name2xy(pos1)[target_node_name1]
        xy2 = self._get_target_pos_name2xy(pos2)[target_node_name2]

        def plot_link(ax: Axes):
            ax.annotate(
                text="",
                xy=xy2,
                xytext=xy1,
                arrowprops=dict(
                    color=color,
                    ls=linestyle,
                    arrowstyle=arrowstyle,
                    connectionstyle=connectionstyle,
                    **kwargs,
                ),
            )

        self._plot_funcs.append(plot_link)

    def text_on_branch(
            self,
            query,
            text,
            *,
            size = 8,
            xpos = "right",
            ypos = "top",
            xmargin_ratio = 0.01,
            ymargin_ratio = 0.05,
            **kwargs,
    ):
        """Plot text on branch of target node

        Parameters
        ----------
        query : str | list[str] | tuple[str]
            Search query node name(s) for plotting text. If multiple node names are set,
            MRCA(Most Recent Common Ancester) node is set.
        text : str
            Text content
        size : int, optional
            Text size
        xpos : str, optional
            X position of plot text (`left`|`center`|`right`)
        ypos : str, optional
            Y position of plot text (`top`|`center`|`bottom`)
        xmargin_ratio : float, optional
            Text x margin ratio. If `xpos = center`, this param is ignored.
        ymargin_ratio : float, optional
            Text y margin ratio. If `ypos = center`, this param is ignored.
        **kwargs : dict, optional
            Text properties (e.g. `color="red", bbox=dict(color="skyblue"), ...`)
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.text.html>
        """
        # Set text ha & va by xpos & ypos
        if xpos not in ("left", "center", "right"):
            raise ValueError(f"{xpos} is invalid ('left'|'center'|'right').")
        if ypos not in ("top", "center", "bottom"):
            raise ValueError(f"{ypos} is invalid ('top'|'center'|'bottom').")
        ypos2va = dict(top="bottom", center="center", bottom="top")
        ha, va = xpos, ypos2va[ypos]

        if self._orientation == "left":
            xpos = dict(left="right", right="left", center="center")[xpos]

        # Get text plot target node & xy coordinate
        target_node_name = self._search_target_node_name(query)
        xpos2xy = dict(
            left=self.name2xy_left[target_node_name],
            center=self.name2xy_center[target_node_name],
            right=self.name2xy_right[target_node_name],
        )
        x, y = xpos2xy[xpos]

        # Apply margin to x, y coordinate
        xmargin_size = self.max_tree_depth * xmargin_ratio
        if xpos == "left":
            x += xmargin_size
        elif xpos == "right":
            x -= xmargin_size
        ymargin_size = ymargin_ratio
        if ypos == "top":
            y += ymargin_size
        elif ypos == "bottom":
            y -= ymargin_size

        def plot_text(ax: Axes):
            # Plot text
            ax.text(x, y, s=text, size=size, va=va, ha=ha, **kwargs)

        self._plot_funcs.append(plot_text)

    def text_on_node(
            self,
            query,
            text,
            *,
            size = 8,
            **kwargs,
    ):
        """Plot text on target node

        Parameters
        ----------
        query : str | list[str] | tuple[str]
            Search query node name(s) for plotting text. If multiple node names are set,
            MRCA(Most Recent Common Ancester) node is set.
        text : str
            Text content
        size : int, optional
            Text size
        **kwargs : dict, optional
            Text properties (e.g. `color="red", bbox=dict(color="skyblue"), ...`)
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.text.html>
        """
        target_node_name = self._search_target_node_name(query)
        x, y = self.name2xy[target_node_name]

        kwargs.setdefault("va", "center_baseline")
        kwargs.setdefault("ha", "center")

        def plot_text(ax: Axes):
            ax.text(x, y, s=text, size=size, **kwargs)

        self._plot_funcs.append(plot_text)

    def set_node_label_props(self, target_node_label, **kwargs):
        """Set tree node label properties

        Parameters
        ----------
        target_node_label : str
            Target node label name
        kwargs : dict, optional
            Text properties (e.g. `color="red", ...`)
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.text.html>
        """
        self._search_target_node_name(target_node_label)
        self._node2label_props[target_node_label] = kwargs

    def set_node_line_props(
            self,
            query,
            *,
            descendent = True,
            **kwargs,
    ):
        """Set tree node line properties

        Parameters
        ----------
        query : str | list[str] | tuple[str]
            Search query node name(s) for coloring tree node line.
            If multiple node names are set,
            MRCA(Most Recent Common Ancester) node is set.
        descendent : bool, optional
            If True, set properties on target node's descendent as well.
        **kwargs : dict, optional
            Axes.plot properties (e.g. `color="blue", lw=2.0, ls="dashed", ...`)
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.plot.html>
        """
        target_node_name = self._search_target_node_name(query)

        clade = next(self.tree.find_clades(target_node_name))
        if descendent:
            descendent_nodes = list(clade.find_clades())
            for descendent_node in descendent_nodes:
                self._node2line_props[str(descendent_node.name)] = kwargs
        else:
            self._node2line_props[str(clade.name)] = kwargs

    def set_title(
            self,
            label,
            **kwargs,
    ):
        """Set title

        Parameters
        ----------
        label : str
            Title text label
        **kwargs : dict, optional
            Axes.set_title properties (e.g. `size=12, color="red", ...`)
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.set_title.html>
        """

        def set_title(ax: Axes):
            ax.set_title(label, **kwargs)

        self._plot_funcs.append(set_title)

    def update_plot_props(
            self,
            *,
            tree_line_kws = None,
            tree_align_line_kws = None,
    ):
        """Update plot properties

        Parameters
        ----------
        tree_line_kws : dict[str, Any], optional
            Axes.plot properties (e.g. `dict(color="red", lw=0.5, ...)`)
            By default, `color="black", lw=1, clip_on=False` are set.
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.plot.html>
        tree_align_line_kws : dict[str, Any], optional
            Axes.plot properties (e.g. `dict(color="red", ls="dashed", ...)`)
            By default, `lw=0.5, ls="dashed", alpha=0.5, clip_on=False` are set.
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.plot.html>
        """
        tree_line_kws = {} if tree_line_kws is None else tree_line_kws
        tree_align_line_kws = {} if tree_align_line_kws is None else tree_align_line_kws

        self._tree_line_kws.update(tree_line_kws)
        self._tree_align_line_kws.update(tree_align_line_kws)

    def plotfig(
            self,
            *,
            dpi=100,
            ax = None,
    ):
        """Plot figure

        Parameters
        ----------
        dpi : int, optional
            Figure DPI
        ax : Axes | None, optional
            Matplotlib axes for plotting. If None, figure & axes are newly created.

        Returns
        -------
        figure : Figure
            Matplotlib figure
        """
        # Initialize axes
        if ax is None:
            # Create matplotlib Figure & Axes
            fig, ax = self._init_figure(self.figsize, dpi=dpi)
            self._init_axes(ax)
        else:
            # Get matplotlib Figure & Axes
            self._init_axes(ax)
            fig = ax.get_figure()  # type: ignore
        self._ax = ax

        # Plot tree line
        self._plot_tree_node_line(ax)
        # Plot node label
        self._plot_node_label(ax)
        # Plot all patches
        for patch in self._get_plot_patches():
            ax.add_patch(patch)
        # Execute all plot functions
        for plot_func in self._get_plot_funcs():
            plot_func(ax)

        return fig

    def savefig(
            self,
            savefile,
            *,
            dpi = 100,
            pad_inches = 0.1,
    ):
        """Save figure to file

        `tv.savefig("result.png")` is alias for
        `tv.plotfig().savefig("result.png")`

        Parameters
        ----------
        savefile : str | Path
            Save file (`*.png`|`*.jpg`|`*.svg`|`*.pdf`)
        dpi : int, optional
            DPI
        pad_inches : float, optional
            Padding inches
        """
        fig = self.plotfig(dpi=dpi)
        fig.savefig(
            fname=savefile,  # type: ignore
            dpi=dpi,
            pad_inches=pad_inches,
            bbox_inches="tight",
        )
        # Clear & close figure to suppress memory leak
        fig.clear()
        plt.close(fig)

    ############################################################
    # Private Method
    ############################################################

    def _init_figure(
            self,
            figsize,
            dpi = 100,
    ):
        """Initialize matplotlib figure

        Parameters
        ----------
        figsize : tuple[float, float]
            Figure size
        dpi : int, optional
            Figure DPI

        Returns
        -------
        figure, axes : tuple[Figure, Axes]
            Matplotlib Figure & Axes
        """
        fig = plt.figure(figsize=figsize, dpi=dpi, layout="none")
        ax = fig.add_subplot()
        return fig, ax  # type: ignore

    def _init_axes(self, ax):
        """Initialize matplotlib axes

        - xlim = (0, `root -> leaf max branch length`)
        - ylim = (0, `total tree leaf count + 1`)

        Parameters
        ----------
        ax : Axes
            Matplotlib axes
        """
        ax.set_xlim(*self.xlim)
        ax.set_ylim(*self.ylim)
        axis_pos2show = dict(bottom=False, top=False, left=False, right=False)
        for axis_pos, show in axis_pos2show.items():
            ax.spines[axis_pos].set_visible(show)
        ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)

    def _get_plot_patches(self):
        """Plot patches"""
        return deepcopy(self._plot_patches)

    def _get_plot_funcs(self):
        """Plot functions"""
        return self._plot_funcs

    def _plot_tree_node_line(self, ax):
        """Plot tree line

        Parameters
        ----------
        ax : Axes
            Matplotlib axes for plotting
        """
        node: Clade
        child_node: Clade
        for node in self.tree.get_nonterminals():
            parent_x, parent_y = self.name2xy[str(node.name)]
            for child_node in node.clades:
                child_x, child_y = self.name2xy[str(child_node.name)]
                _tree_line_kws = deepcopy(self._tree_line_kws)
                _tree_line_kws.update(self._node2line_props[str(child_node.name)])
                # Plot vertical line
                v_line_points = (parent_x, parent_x), (parent_y, child_y)
                ax.plot(*v_line_points, **_tree_line_kws)
                # Plot horizontal line
                h_line_points = (parent_x, child_x), (child_y, child_y)
                ax.plot(*h_line_points, **_tree_line_kws)
                # Plot horizontal line for label alignment if required
                if child_node.is_terminal() and self._align_leaf_label:
                    _tree_align_line_kws = deepcopy(self._tree_align_line_kws)
                    _tree_align_line_kws.update(color=_tree_line_kws["color"])
                    h_line_points = (child_x, self.max_tree_depth), (child_y, child_y)
                    ax.plot(*h_line_points, **_tree_align_line_kws)

    def _plot_node_label(self, ax):
        """Plot tree node label

        Parameters
        ----------
        ax : Axes
            Matplotlib axes for plotting
        """
        node: Clade
        for node in self.tree.find_clades():
            # Get label x, y position
            x, y = self.name2xy[str(node.name)]
            # Get label size & xmargin
            if node.is_terminal():
                label_size = self._leaf_label_size
                label_xmargin_ratio = self._leaf_label_xmargin_ratio
            else:
                label_size = self._innode_label_size
                label_xmargin_ratio = self._innode_label_xmargin_ratio
            label_xmargin = self.max_tree_depth * label_xmargin_ratio
            # Set label x position with margin
            if node.is_terminal() and self._align_leaf_label:
                x = self.max_tree_depth + label_xmargin
            else:
                x += label_xmargin
            # Skip if 'label is auto set name' or 'no label size'
            if label_size <= 0:
                continue
            is_auto_innode_label = node.name in self._auto_innode_labels
            if not self._show_auto_innode_label and is_auto_innode_label:
                continue
            # Plot label
            text_kws = dict(size=label_size, ha="left", va="center_baseline")
            text_kws.update(self._node2label_props[str(node.name)])
            if self._orientation == "left":
                text_kws.update(ha="right")
            ax.text(x, y, s=node.name, **text_kws)  # type: ignore

    def _load_tree(self, data, format):
        """Load tree data

        Parameters
        ----------
        data : str | Path | Tree
            Tree data
        format : str
            Tree format

        Returns
        -------
        tree : Tree
            Tree object
        """
        if isinstance(data, str) and urlparse(data).scheme in ("http", "https"):
            # Load tree file from URL
            return Phylo.read(io.StringIO(urlopen(data).read().decode()), format=format)
        elif isinstance(data, (str, Path)) and os.path.isfile(data):
            # Load tree file
            return Phylo.read(data, format=format)
        elif isinstance(data, str):
            # Load tree string
            return Phylo.read(io.StringIO(data), format=format)
        elif isinstance(data, Tree):
            return data
        else:
            raise ValueError(f"{data} is invalid input tree data!!")

    def _set_uniq_innode_name(self, tree):
        """Set unique internal node name (N_1, N_2, ..., N_XXX)

        Parameters
        ----------
        tree : Tree
            Tree object

        Returns
        -------
        tree, uniq_node_names: tuple[Tree, list[str]]
            Unique node name set tree object & set unique node names
        """
        tree = deepcopy(tree)
        uniq_innode_names = []
        for idx, node in enumerate(tree.get_nonterminals(), 1):
            uniq_innode_name = f"N_{idx}"
            if node.name is None:
                node.name = uniq_innode_name
                uniq_innode_names.append(uniq_innode_name)
        return tree, uniq_innode_names

    def _to_ultrametric_tree(self, tree):
        """Convert to ultrametric tree

        Parameters
        ----------
        tree : Tree
            Tree

        Returns
        -------
        tree : Tree
            Ultrametric tree
        """
        tree = deepcopy(tree)
        # Get unit branch depth info
        name2depth = {str(n.name): float(d) for n, d in tree.depths(True).items()}
        name2depth = dict(sorted(name2depth.items(), key=lambda t: t[1], reverse=True))
        max_tree_depth = max(name2depth.values())
        # Reset node branch length
        for node in tree.find_clades():
            node.branch_length = None
        tree.root.branch_length = 0
        # Calculate appropriate ultrametric tree branch length
        for name, depth in name2depth.items():
            node = next(tree.find_clades(name))
            if not node.is_terminal():
                continue
            path = tree.get_path(node)
            if path is None:
                raise ValueError(f"{name} node not exists?")
            if depth == max_tree_depth:
                for path_node in path:
                    path_node.branch_length = 1
            else:
                # Collect nodes info which has branch length
                bl_sum, bl_exist_node_count = 0, 0
                for path_node in path:
                    if path_node.branch_length is not None:
                        bl_sum += path_node.branch_length
                        bl_exist_node_count += 1
                # Set branch length to no branch length nodes
                other_bl = (max_tree_depth - bl_sum) / (len(path) - bl_exist_node_count)
                for path_node in path:
                    if path_node.branch_length is None:
                        path_node.branch_length = other_bl
        return tree

    def _check_node_name_dup(self, tree):
        """Check node name duplication in tree

        Parameters
        ----------
        tree : Tree
            Tree object
        """
        all_node_names = [str(n.name) for n in tree.find_clades()]
        err_msg = ""
        for node_name, count in Counter(all_node_names).items():
            if count > 1:
                err_msg += f"{node_name} is duplicated in tree ({count}).\n"
        if err_msg != "":
            err_msg += "\nphyTreeViz cannot handle tree with duplicate node names!!"
            raise ValueError("\n" + err_msg)

    def _search_target_node_name(
            self,
            query,
    ):
        """Search target node name from query

        Parameters
        ----------
        query : str | list[str] | tuple[str]
            Search query node name(s). If multiple node names are set,
            MRCA(Most Recent Common Ancester) node is set.
        """
        self._check_node_name_exist(query)
        if isinstance(query, (list, tuple)):
            target_node_name = self.tree.common_ancestor(*query).name
        else:
            target_node_name = query
        return target_node_name

    def _check_node_name_exist(
            self,
            query,
    ):
        """Check node name exist in tree

        Parameters
        ----------
        query : str | list[str] | tuple[str]
            Query node name(s) for checking exist
        """
        if isinstance(query, str):
            query = [query]
        err_msg = ""
        for node_name in query:
            if node_name not in self.all_node_labels:
                err_msg += f"{node_name} is not found in tree.\n"
        if err_msg != "":
            err_msg = f"\n{err_msg}\nAvailable node names:\n{self.all_node_labels}"
            raise ValueError(err_msg)

    def _get_target_pos_name2xy(
            self,
            pos = "right",
    ):
        """Get tree node name & xy coordinate dict in target position

        Parameters
        ----------
        pos : str, optional
            Target position (`left`|`center`|`right`)

        Returns
        -------
        name2xy : dict[str, tuple[float, float]]
            Tree node name & xy coordinate dict
        """
        if pos not in ("left", "center", "right"):
            raise ValueError(f"{pos} is invalid ('left'|'center'|'right').")

        return dict(
            left=self.name2xy_left,
            center=self.name2xy_center,
            right=self.name2xy_right,
        )[pos]

    def _get_texts_rect(
            self,
            query,
    ):
        """Get query label texts rectangle

        Parameters
        ----------
        query : str | list[str] | tuple[str]
            Search query node name(s) for rectangle. If multiple node names are set,
            MRCA(Most Recent Common Ancester) node is set.

        Returns
        -------
        rect : Rectangle
            Label texts rectangle
        """
        target_node_name = self._search_target_node_name(query)
        node = next(self.tree.find_clades(target_node_name))
        target_labels = [str(n.name) for n in node.get_terminals()]

        target_texts = [
            t for t in self.ax.texts if t.get_text() in target_labels
        ]
        x_list = []
        y_list = []
        for text in target_texts:
            bbox = text.get_window_extent()
            trans_bbox = self.ax.transData.inverted().transform_bbox(bbox)
            x_list.extend([trans_bbox.xmin, trans_bbox.xmax])
            y_list.extend([trans_bbox.ymin, trans_bbox.ymax])
        xmin, xmax = min(x_list), max(x_list)
        ymin, ymax = min(y_list), max(y_list)

        return Rectangle(xy=(xmin, ymin), width=xmax - xmin, height=ymax - ymin)

    def _calc_name2xy_pos(self, pos = "center"):
        """Calculate tree node name & xy coordinate

        Parameters
        ----------
        pos : str, optional
            Target xy position (`left`|`center`|`right`)

        Returns
        -------
        name2xy_pos : dict[str, tuple[float, float]]
            Tree node name & xy coordinate dict
        """
        if pos not in ("left", "center", "right"):
            raise ValueError(f"{pos} is invalid ('left'|'center'|'right').")

        leaf_nodes = list(reversed(self.tree.get_terminals()))
        if self._reverse:
            leaf_nodes = list(reversed(leaf_nodes))

        # Calculate right position xy coordinate
        name2xy_right = {}
        node: Clade
        for idx, node in enumerate(leaf_nodes, 1):
            # Leaf node xy coordinates
            name2xy_right[str(node.name)] = (self.tree.distance(node.name), idx)
        for node in self.tree.get_nonterminals("postorder"):
            # Internal node xy coordinates
            x = self.tree.distance(node.name)
            y = sum([name2xy_right[n.name][1] for n in node.clades]) / len(node.clades)
            name2xy_right[str(node.name)] = (x, y)
        if pos == "right":
            return name2xy_right

        # Calculate left or center position xy coordinate
        name2xy_pos = {}
        node: Clade
        for node in self.tree.find_clades():
            node_name = str(node.name)
            if node == self.tree.root:
                name2xy_pos[node_name] = name2xy_right[node_name]
            else:
                tree_path = self.tree.get_path(node.name)
                tree_path = [self.tree.root] + tree_path  # type: ignore
                parent_node = tree_path[-2]
                parent_xy = self.name2xy_right[str(parent_node.name)]
                if pos == "center":
                    x = (self.name2xy_right[node_name][0] + parent_xy[0]) / 2
                elif pos == "left":
                    x = parent_xy[0]
                else:
                    raise ValueError(f"{pos} is invalid ('center' or 'left').")
                y = self.name2xy_right[node_name][1]
                name2xy_pos[node_name] = (x, y)
        return name2xy_pos

    def _calc_name2rect(self):
        """Calculate tree node name & rectangle for highlight

        Returns
        -------
        name2rect : dict[str, Rectangle]
            Tree node name & rectangle dict
        """
        name2rect = {}
        for name, xy in self.name2xy.items():
            # Get parent node
            node = next(self.tree.find_clades(name))
            if node == self.tree.root:
                parent_node = node
            else:
                tree_path = self.tree.get_path(node.name)
                tree_path = [self.tree.root] + tree_path  # type: ignore
                parent_node = tree_path[-2]

            # Get child node xy coordinates
            child_node_names = [str(n.name) for n in node.find_clades()]
            x_list = []
            y_list = []
            for child_node_name in child_node_names:
                x, y = self.name2xy[child_node_name]
                x_list.append(x)
                y_list.append(y)

            # Calculate rectangle min-max xy coordinate
            parent_xy = self.name2xy[str(parent_node.name)]
            min_x = (xy[0] + parent_xy[0]) / 2
            max_x = self.max_tree_depth if self._align_leaf_label else max(x_list)
            min_y = min(y_list) - 0.5
            max_y = max(y_list) + 0.5

            # Set rectangle
            rect = Rectangle(
                xy=(min_x, min_y),
                width=max_x - min_x,
                height=max_y - min_y,
            )
            name2rect[name] = rect

        return name2rect