#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
description goes here
'''

import io
import os
from collections import Counter, defaultdict
from copy import deepcopy
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
# import patchworklib as pw
from phytreeviz.treeviz import TreeViz


class PS_Treeviz(TreeViz):

    def __init__(
            self,
            tree_data,  # type: ignore
            # invert_ = False,
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
            leaf_label_dict = {},
            line_prop={}
    ):
        super(PS_Treeviz, self).__init__(
            tree_data,
            orientation=orientation,
            format=format,
            height=height,
            width=width,
            align_leaf_label=align_leaf_label,
            ignore_branch_length=ignore_branch_length,
            leaf_label_size=leaf_label_size,
            innode_label_size=innode_label_size,
            show_auto_innode_label=show_auto_innode_label,
            leaf_label_xmargin_ratio=leaf_label_xmargin_ratio,
            innode_label_xmargin_ratio=innode_label_xmargin_ratio,
            reverse=reverse,
        )
        # for setting xlim
        self._orientation = 'right'
        self.leaf_label_dict = leaf_label_dict
        self.line_prop = line_prop
        # tmp
        self.tree_lengths = [self.max_tree_depth]
        self.yscale = 1
        self.hscale = 1
        # tmp
        self.xmax_ = self.max_tree_depth
        self.top_right = None

    @property
    def xlim(self):
        """Axes xlim"""
        # if self._orientation == "left":
        #     return (max(self.tree_lengths), 0)
        # else:
        #     return (0, max(self.tree_lengths))
        # return (0, max(self.tree_lengths))
        # 测试,该方法可以实时获取lim
        list_ws = []
        for node in self.tree.find_clades():
            if node.is_terminal():
                if hasattr(node, "ax_text"):
                    ax_text = node.ax_text
                    trans_box = self.get_text_rect(ax_text)
                    list_ws.append(trans_box.x1)
        max_w = max(list_ws) if list_ws else self.max_tree_depth
        if self._orientation == "left":
            return (max_w, 0)
        else:
            return (0, max_w)
        # # 该方法只能获取最初建立树的时候的lim
        # if self._orientation == "left":
        #     return (self.xmax_, 0)
        # else:
        #     return (0, self.xmax_)

    @property
    def ylim(self):
        """Axes ylim"""
        return (0, self.tree.count_terminals() + 1)

    def plotfig(
            self,
            *,
            fig_=None,
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
            if fig_:
                fig = fig_
            else:
                fig = ax.get_figure()  # type: ignore
        self._ax = ax
        self.fig = fig
        # pos1 = self._ax.get_position() # get the original position
        # print(pos1)
        # ax占据整个figure
        pos2 = [0, 0, 1, 1]
        self._ax.set_position(pos2) # set a new position

        # Plot tree line
        self._plot_tree_node_line(ax)
        # Plot node label
        self._plot_node_label(ax)

        # 画完label以后再设置lim
        # ax.set_xlim((0, self.xlim[1]+0.5))
        ax.set_ylim(*self.ylim)
        # print(self.max_tree_depth, self.xlim)
        # print(ax.get_xlim())

        # Plot all patches
        for patch in self._get_plot_patches():
            ax.add_patch(patch)
        # Execute all plot functions
        for plot_func in self._get_plot_funcs():
            plot_func(ax)

        return fig

    def _init_axes(self, ax):
        """Initialize matplotlib axes

        - xlim = (0, `root -> leaf max branch length`)
        - ylim = (0, `total tree leaf count + 1`)

        Parameters
        ----------
        ax : Axes
            Matplotlib axes
        """
        # ax.set_xlim(*self.xlim)
        # ax.set_ylim(*self.ylim)
        axis_pos2show = dict(bottom=False, top=False, left=False, right=False)
        for axis_pos, show in axis_pos2show.items():
            ax.spines[axis_pos].set_visible(show)
        ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)

    def show_scale_bar(
            self,
            *,
            scale_size = None,
            text_size = 8,
            loc = "lower left",
            label_top = False,
            size_vertical = 0.1,
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

        def plot_scale_bar(ax):
            auto_size = ax.get_xticks()[1]  # type: ignore
            scale = AnchoredSizeBar(
                ax.transData,
                size=auto_size if scale_size is None else scale_size,
                label=str(auto_size) if scale_size is None else str(scale_size),
                loc=loc,
                label_top=label_top,
                frameon=False,
                fontproperties=FontProperties(size=text_size),  # type: ignore
                size_vertical=size_vertical,
            )
            ax.add_artist(scale)
            # size=auto_size if scale_size is None else scale_size
            # ax.axhline(y=0, xmin=0, xmax=size, linewidth=1, color='black')
            # # 添加标签到线的下方并设置位置
            # ax.text(size/2, 0, str(size), ha='center', va='top')

        self._plot_funcs.append(plot_scale_bar)

    # @cached_property
    def name2y(self, name):
        return self.name2xy[name][1]

    def make_bar_plot(self,
                      tab_tableview,
                      array,
                      ax_tree,
                      mode=None,
                      ):
        # 获取参数
        configs = tab_tableview.model().arraydata
        dict_configs = dict(configs)
        width, height = ax_tree._originalsize
        ax_ = pw.Brick(figsize=(width*float(dict_configs["Width fraction"]),
                                height))
        ax_.set_axis_off()
        tab_tableview.list_item.ax_ = ax_
        # 设置y对应
        ax_.set_ylim(*self.ylim)
        # 画图
        for list_row in array:
            name, value = list_row
            if value:
                ax_.barh(self.name2y(name), value, color=dict_configs["Color"])
        return tab_tableview

    def get_text_rect(self, text_element):
        # renderer=self.fig.canvas.renderer
        return self.ax.transData.inverted().transform_bbox(text_element.get_window_extent())

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
                _tree_line_kws.update(self.line_prop)
                # Plot vertical line
                v_line_points = (parent_x, parent_x), (parent_y, child_y)
                v_line = ax.plot(*v_line_points, **_tree_line_kws)
                v_line[0].__dict__["type"] = "branch"
                y_l = abs(child_y - parent_y)*0.5
                # in order to draw rectangle when mouse hover, we need to know the rect parameters
                rect_parms = [(parent_x, child_y-y_l/2), abs(child_x-parent_x), y_l]
                # print(v_line)
                # v_line[0].__dict__["tree_node"] = child_node
                # v_line[0].__dict__["rect_parms"] = rect_parms
                # Plot horizontal line
                h_line_points = (parent_x, child_x), (child_y, child_y)
                h_line = ax.plot(*h_line_points, **_tree_line_kws)
                h_line[0].__dict__["tree_node"] = child_node
                h_line[0].__dict__["rect_parms"] = rect_parms
                h_line[0].__dict__["type"] = "branch"
                # Plot horizontal line for label alignment if required
                if child_node.is_terminal() and self._align_leaf_label:
                    _tree_align_line_kws = deepcopy(self._tree_align_line_kws)
                    _tree_align_line_kws.update(color=_tree_line_kws["color"])
                    h_line_points = (child_x, self.max_tree_depth), (child_y, child_y)
                    align_line = ax.plot(*h_line_points, **_tree_align_line_kws)
                    align_line[0].__dict__["tree_node"] = child_node
                    align_line[0].__dict__["rect_parms"] = rect_parms
                    align_line[0].__dict__["type"] = "branch"

    def _plot_node_label(self, ax):
        """Plot tree node label

        Parameters
        ----------
        ax : Axes
            Matplotlib axes for plotting
        """
        node: Clade
        self.tree_lengths = [self.max_tree_depth]
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
            text_kws.update(self.leaf_label_dict)
            if self._orientation == "left":
                text_kws.update(ha="right")

            ax_text = ax.text(x, y, s=node.name, **text_kws)
            # trans_bbox = self.ax.transData.inverted().transform_bbox(ax_text.get_window_extent())
            # text_length = trans_bbox.width # trans_bbox.xmax - trans_bbox.xmin
            # # in order to draw rectangle when mouse hover, we need to know the rect parameters
            # rect_parms = [(x, y-trans_bbox.height/2), text_length, trans_bbox.height]
            ax_text.__dict__["tree_node"] = node
            ax_text.__dict__["type"] = "leaf"
            node.ax_text = ax_text
            # ax_text.__dict__["rect_parms"] = rect_parms

            bbox = self.get_text_rect(ax_text)

            # bbox = ax_text.get_bbox()
            if bbox.x1>self.xmax_:
                self.xmax_ = bbox.x1
                self.top_right = ax_text

            # # get toot to text width
            # if node.is_terminal():
            #     # text_length = self._get_texts_rect(node.name).get_width()
            #     length = x + text_length
            #     self.tree_lengths.append(length)
        # self._init_axes(self.ax)

    def _get_longest_text_width(self):
        # print({node.name:self._get_texts_rect(node.name).get_width() for node in self.tree.get_terminals()})
        return max([self._get_texts_rect(node.name).get_width() for node in self.tree.get_terminals()])

    def _calc_name2xy_pos(self,
                          pos = "center"
                          ):
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

        yscale = self.yscale / self.hscale

        # Calculate right position xy coordinate
        name2xy_right = {}
        node: Clade
        for idx, node in enumerate(leaf_nodes, 1):
            # Leaf node xy coordinates
            name2xy_right[str(node.name)] = (self.tree.distance(node.name),
                                             idx*yscale)
        for node in self.tree.get_nonterminals("postorder"):
            # Internal node xy coordinates
            x = self.tree.distance(node.name)
            y = sum([name2xy_right[n.name][1] for n in node.clades]) / len(node.clades)
            y = y
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
