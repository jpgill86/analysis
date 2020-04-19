"""
Helper functions for plotting data
"""


from matplotlib.offsetbox import AnchoredOffsetbox


class AnchoredScaleBar(AnchoredOffsetbox):
    # modified from https://gist.github.com/dmeliza/3251476
    def __init__(self, transform, sizex=0, sizey=0, labelx=None, labely=None, loc=4,
                 pad=0.1, borderpad=0.1, sep=2, prop=None, barcolor="black", barwidth=None,
                 **kwargs):
        """
        Draw a horizontal and/or vertical  bar with the size in data coordinate
        of the give axes. A label will be drawn underneath (center-aligned).
        - transform : the coordinate frame (typically axes.transData)
        - sizex,sizey : width of x,y bar, in data units. 0 to omit
        - labelx,labely : labels for x,y bars; None to omit
        - loc : position in containing axes
        - pad, borderpad : padding, in fraction of the legend font size (or prop)
        - sep : separation between labels and bars in points.
        - **kwargs : additional arguments passed to base class constructor
        """
        from matplotlib.patches import Rectangle
        from matplotlib.offsetbox import AuxTransformBox, VPacker, HPacker, TextArea, DrawingArea
        bars = AuxTransformBox(transform)
        if sizex:
#             bars.add_artist(Rectangle((0,0), sizex, 0, ec=barcolor, lw=barwidth, fc="none"))
            bars.add_artist(Rectangle((0,0), -sizex, 0, ec=barcolor, lw=barwidth, fc="none"))
        if sizey:
            bars.add_artist(Rectangle((0,0), 0, sizey, ec=barcolor, lw=barwidth, fc="none"))

        if sizex and labelx:
            self.xlabel = TextArea(labelx, minimumdescent=False)
            bars = VPacker(children=[bars, self.xlabel], align="center", pad=0, sep=sep)
        if sizey and labely:
            self.ylabel = TextArea(labely)
#             bars = HPacker(children=[self.ylabel, bars], align="center", pad=0, sep=sep)
            bars = HPacker(children=[bars, self.ylabel], align="center", pad=0, sep=sep)

        AnchoredOffsetbox.__init__(self, loc, pad=pad, borderpad=borderpad,
                                   child=bars, prop=prop, frameon=False, **kwargs)


def add_scalebar(ax, **kwargs):
    sb = AnchoredScaleBar(ax.transData, bbox_transform=ax.transAxes, pad=0, **kwargs)
    ax.add_artist(sb)
    return sb

def solve_figure_horizontal_dimensions(ncols, subplot_width_in_inches, left_margin_in_inches, right_margin_in_inches, wspace):
    """
    Determine horizontal figure dimensions from fixed subplot dimensions for
    matplotlib.pyplot.subplots and matplotlib.pyplot.subplots_adjust.

    Returns: fig_width_in_inches, left_fraction, right_fraction
    """

    fig_width_in_inches = (ncols)*(subplot_width_in_inches) + (ncols-1)*(wspace*subplot_width_in_inches) + left_margin_in_inches + right_margin_in_inches
    left_fraction = left_margin_in_inches/fig_width_in_inches
    right_fraction = 1 - right_margin_in_inches/fig_width_in_inches

    return fig_width_in_inches, left_fraction, right_fraction

def solve_figure_vertical_dimensions(nrows, subplot_height_in_inches, bottom_margin_in_inches, top_margin_in_inches, hspace):
    """
    Determine vertical figure dimensions from fixed subplot dimensions for
    matplotlib.pyplot.subplots and matplotlib.pyplot.subplots_adjust.

    Returns: fig_height_in_inches, bottom_fraction, top_fraction
    """

    fig_height_in_inches = (nrows)*(subplot_height_in_inches) + (nrows-1)*(hspace*subplot_height_in_inches) + bottom_margin_in_inches + top_margin_in_inches
    bottom_fraction = bottom_margin_in_inches/fig_height_in_inches
    top_fraction = 1 - top_margin_in_inches/fig_height_in_inches

    return fig_height_in_inches, bottom_fraction, top_fraction
