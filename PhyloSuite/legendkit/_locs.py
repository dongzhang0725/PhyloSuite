from matplotlib.axes import Axes


def add_x(x, y, offset):
    return x + offset, y


def add_y(x, y, offset):
    return x, y + offset


def minus_x(x, y, offset):
    return x - offset, y


def minus_y(x, y, offset):
    return x, y - offset


def blank(x, y, offset):
    return x, y


class Locs:
    combs = {
        'out upper left': ('lower left', (0, 1), add_y),
        'out upper center': ('lower center', (0.5, 1), add_y),
        'out upper right': ('lower right', (1, 1), add_y),

        'out lower left': ('upper left', (0, 0), minus_y),
        'out lower center': ('upper center', (0.5, 0), minus_y),
        'out lower right': ('upper right', (1, 0), minus_y),

        'out left upper': ('upper right', (0, 1), minus_x),
        'out left center': ('center right', (0, 0.5), minus_x),
        'out left lower': ('lower right', (0, 0), minus_x),

        'out right upper': ('upper left', (1, 1), add_x),
        'out right center': ('center left', (1, 0.5), add_x),
        'out right lower': ('lower left', (1, 0), add_x),

        'lower left': ('lower left', (0, 0), blank),

        'center left': ('center left', (0, 0.5), blank),
        'center right': ('center right', (1, 0.5), blank),
    }

    LOC_OPTIONS = [
        'lower left', 'lower center', 'lower right',
        'upper left', 'upper center', 'upper right',
        'center left', 'center', 'center right',
        'out upper left', 'out upper center', 'out upper right',
        'out lower left', 'out lower center', 'out lower right',
        'out left upper', 'out left center', 'out left lower',
        'out right upper', 'out right center', 'out right lower'
    ]

    def transform(self,
                  ax,
                  loc=None,
                  bbox_to_anchor=None,
                  bbox_transform=None,
                  deviation=0,
                  ):
        if loc is None:
            loc = "upper right"
        if loc not in self.LOC_OPTIONS:
            msg = f"`loc` must be one of {', '.join(self.LOC_OPTIONS)}"
            raise ValueError(msg)
        replacement = self.combs.get(loc)
        if replacement is not None:
            loc = replacement[0]
            bbox = replacement[1]
            offset_func = replacement[2]
            bbox_to_anchor = offset_func(*bbox, deviation)
            if isinstance(ax, Axes):
                bbox_transform = ax.transAxes
            else:
                fig = ax.get_figure()
                bbox_transform = fig.transSubfigure
        return loc, bbox_to_anchor, bbox_transform
