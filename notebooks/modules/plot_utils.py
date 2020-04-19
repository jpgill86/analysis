"""
Helper functions for plotting data
"""


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
