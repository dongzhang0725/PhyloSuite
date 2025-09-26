from ._handlers import SquareHandler, RectHandler, CircleHandler, BoxplotHanlder
from .handles import SquareItem, RectItem, CircleItem, BoxplotItem


def register():
    import matplotlib as mpl
    from matplotlib.legend import Legend

    # # Overwrite the default rcParams for legend
    _legend_config = {
        # 'legend.loc': 'best',
        'legend.frameon': False,  # True  # if True, draw the legend on a background patch
        # 'legend.framealpha': 0.8,  # legend patch transparency
        # 'legend.facecolor': 'inherit',  # inherit from axes.facecolor; or color spec
        # 'legend.edgecolor': 0.8,  # background patch boundary color
        # 'legend.fancybox': True,  # if True, use a rounded box for the legend background, else a rectangle
        # 'legend.shadow': False,  # if True, give background a shadow effect
        # 'legend.numpoints': 1,  # the number of marker points in the legend line
        # 'legend.scatterpoints': 1,  # number of scatter points
        # 'legend.markerscale': 1.0,  # the relative size of legend markers vs. original
        'legend.fontsize': 10,
        # 'legend.labelcolor': None,
        'legend.title_fontsize': 10,  # None sets to the same as the default axes.

        # Dimensions as fraction of font size:
        'legend.borderpad': 0.,  # 0.4,  # border whitespace
        'legend.labelspacing': 0.5,  # the vertical space between the legend entries
        'legend.handlelength': 1.0,  # 2.0,  # the length of the legend lines
        'legend.handleheight': 1.0,  # 0.7,  # the height of the legend handle
        'legend.handletextpad': 0.5,  # 0.8,  # the space between the legend line and legend text
        'legend.borderaxespad': 0.5,  # 0.5,  # the border between the axes and legend edge
        'legend.columnspacing': 1.0  # 2.0,  # column separation
    }

    mpl.rcParams.update(_legend_config)

    # Register new legend handlers
    _default_handlers = Legend.get_default_handler_map()
    Legend.set_default_handler_map({**_default_handlers,
                                    SquareItem: SquareHandler(),
                                    RectItem: RectHandler(),
                                    CircleItem: CircleHandler(),
                                    BoxplotItem: BoxplotHanlder(),
                                    })
