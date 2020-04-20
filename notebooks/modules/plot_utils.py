"""
Helper functions for plotting data
"""


import quantities as pq
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredOffsetbox
from matplotlib.ticker import MultipleLocator
import seaborn as sns
from .utils import DownsampleNeoSignal


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

def get_sig(blk, name):
    sig = next((sig for sig in blk.segments[0].analogsignals if sig.name==name), None)
    if sig is None:
        raise Exception(f'Channel "{name}" could not be found')
    else:
        return sig

def plot_signals_with_axes(
    blk,
    t_start,
    t_stop,
    plots,

    outfile_basename=None, # base name of output files
    export_only=False,     # if True, will not render in notebook
    formats=['pdf', 'svg', 'png'], # extensions of output files
    dpi=300,               # resolution (applicable only for PNG)

    figsize=(14, 7),       # figure size in inches
    linewidth=1,           # thickness of lines in points
    layout_settings=None,  # positioning of plot edges and the space between plots

    majorticks=5,          # spacing of labeled x-axis ticks in seconds
    minorticks=1,          # spacing of unlabeled x-axis ticks in seconds
    ylabel_offset=-0.06,   # horizontal positioning of y-axis labels
):

    if export_only:
        plt.ioff()

    fig, axes = plt.subplots(len(plots), 1, sharex=True, figsize=figsize, squeeze=False)
    axes = axes.flatten()

    for i, p in enumerate(plots):

        # get the subplot axes handle
        ax = axes[i]

        # select and rescale a channel for the subplot
        sig = get_sig(blk, p['channel'])
        sig = sig.time_slice(max(sig.t_start, t_start), min(sig.t_stop, t_stop))
        sig = sig.rescale(p['units'])

        # downsample the data
        sig_downsampled = DownsampleNeoSignal(sig, p.get('decimation_factor', 1))

        # specify the x- and y-data for the subplot
        ax.plot(
            sig_downsampled.times,
            sig_downsampled.as_quantity(),
            linewidth=linewidth,
            color=p.get('color', 'k'),
        )

        # specify the y-axis label
        ylabel = p.get('ylabel', f'{sig.name} ({sig.units.dimensionality.string})')
        ax.set_ylabel(ylabel)

        # position the y-axis label so that all subplot y-axis labels are aligned
        ax.yaxis.set_label_coords(ylabel_offset, 0.5)

        # specify the plot range
        ax.set_xlim([t_start, t_stop])
        ax.set_ylim(p['ylim'])

        if i == len(plots)-1:
            # turn on minor (frequent and unlabeled) ticks for the bottom x-axis
            ax.xaxis.set_minor_locator(MultipleLocator(minorticks))

            # turn on major (infrequent and labeled) ticks for the bottom x-axis
            ax.xaxis.set_major_locator(MultipleLocator(majorticks))

            # disable scientific notation for major tick labels
            # ax.xaxis.get_major_formatter().set_useOffset(False) # not necessary?

            # specify the bottom x-axis label
            ax.set_xlabel(f'Time ({sig.times.units.dimensionality.string})')

            # offset axes from plot
            sns.despine(ax=ax, offset=10)#, trim=True)
        else:
            # offset axes and remove x-axis
            sns.despine(ax=ax, offset=10, trim=True, bottom=True)
            ax.xaxis.set_visible(False)

    # adjust the white space around and between the subplots
    if layout_settings is None:
        fig.tight_layout()
    else:
        plt.subplots_adjust(**layout_settings)

    if outfile_basename is not None:
        # specify file metadata (applicable only for PDF)
        metadata = dict(
            Subject = f'Data file: {blk.file_origin}\n' +
                      f'Start time: {t_start}\n' +
                      f'End time: {t_stop}',
        )

        # write the figure to files
        for ext in formats:
            fig.savefig(f'{outfile_basename}.{ext}', metadata=metadata, dpi=dpi)

    if export_only:
        plt.ion()

    return fig, axes

def plot_signals_with_scalebars(
    blk,
    t_start,
    t_stop,
    plots,

    outfile_basename=None, # base name of output files
    export_only=False,     # if True, will not render in notebook
    formats=['pdf', 'svg', 'png'], # extensions of output files
    dpi=300,               # resolution (applicable only for PNG)

    figsize=(14, 7),       # figure size in inches
    linewidth=1,           # thickness of lines in points
    layout_settings=None,  # positioning of plot edges and the space between plots

    x_scalebar=1*pq.s,     # size of the time scale bar in seconds
    ylabel_padding=10,     # space between trace labels and plots
    scalebar_padding=1,    # space between scale bars and plots
    scalebar_sep=5,        # space between scale bars and scale labels
    barwidth=2,            # thickness of scale bars
):

    if export_only:
        plt.ioff()

    fig, axes = plt.subplots(len(plots), 1, sharex=True, figsize=figsize, squeeze=False)
    axes = axes.flatten()

    for i, p in enumerate(plots):

        # get the subplot axes handle
        ax = axes[i]

        # select and rescale a channel for the subplot
        sig = get_sig(blk, p['channel'])
        sig = sig.time_slice(max(sig.t_start, t_start), min(sig.t_stop, t_stop))
        sig = sig.rescale(p['units'])

        # downsample the data
        sig_downsampled = DownsampleNeoSignal(sig, p.get('decimation_factor', 1))

        # specify the x- and y-data for the subplot
        ax.plot(
            sig_downsampled.times,
            sig_downsampled.as_quantity(),
            linewidth=linewidth,
            color=p.get('color', 'k'),
        )

        # hide the box around the subplot
        ax.set_frame_on(False)

        # specify the y-axis label
        ylabel = p.get('ylabel', sig.name)
        if ylabel is not None:
            ax.set_ylabel(ylabel, rotation='horizontal', ha='right', va='center', labelpad=ylabel_padding)

        # specify the plot range
        ax.set_xlim([t_start, t_stop])
        ax.set_ylim(p['ylim'])

        # disable tick marks
        ax.tick_params(
            bottom=False,
            left=False,
            labelbottom=False,
            labelleft=False)

        # add y-axis scale bar
        if p['scalebar'] is not None:
            add_scalebar(ax,
                sizey=p['scalebar'],
                labely=f'{p["scalebar"]} {sig.units.dimensionality.string}',

                loc='center left',
                bbox_to_anchor=(1, 0.5),

                borderpad=scalebar_padding,
                sep=scalebar_sep,
                barwidth=barwidth,
            )

    # add time scale bar below final plot
    if x_scalebar is not None:
        add_scalebar(axes[-1],
            sizex=x_scalebar.rescale(sig.times.units).magnitude,
            labelx=f'{x_scalebar.magnitude:g} {x_scalebar.units.dimensionality.string}',

            loc='upper right',
            bbox_to_anchor=(1, 0),

            borderpad=scalebar_padding,
            sep=scalebar_sep,
            barwidth=barwidth,
        )

    # adjust the white space around and between the subplots
    if layout_settings is None:
        fig.tight_layout(h_pad=0, w_pad=0, pad=0)
    else:
        plt.subplots_adjust(**layout_settings)

    if outfile_basename is not None:
        # specify file metadata (applicable only for PDF)
        metadata = dict(
            Subject = f'Data file: {blk.file_origin}\n' +
                      f'Start time: {t_start}\n' +
                      f'End time: {t_stop}',
        )

        # write the figure to files
        for ext in formats:
            fig.savefig(f'{outfile_basename}.{ext}', metadata=metadata, dpi=dpi)

    if export_only:
        plt.ion()

    return fig, axes
