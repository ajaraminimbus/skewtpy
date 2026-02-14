import numpy as np
import matplotlib.pyplot as plt


def skew_transform(Tc, p_hPa, skew=-40):
    """
    Transform temperature (°C) into skewed x-coordinate space using:

        x = T + skew * ln(p)

    Parameters
    ----------
    Tc : array-like
        Temperature in °C.
    p_hPa : array-like
        Pressure in hPa.
    skew : float
        Controls the tilt of isotherms (typical values: 25–40).

    Returns
    -------
    array-like
        Skewed x-coordinate values.
    """
    return Tc + skew * np.log(p_hPa)


def plot_skewt_logp(T, Td, p, xlim_C=None, pmin=100, lang='en', skew=-40):
    """
    Plot a simplified Skew-T log-p diagram with professional styling.

    Parameters
    ----------
    T : array-like
        Environmental temperature (°C).
    Td : array-like or None
        Dew point temperature (°C).
    p : array-like
        Pressure levels (hPa).
    xlim_C : tuple or None
        Optional temperature limits (°C) for x-axis.
    pmin : float
        Minimum pressure (upper boundary) displayed (hPa).
    lang : str
        Axis language ("en" or "es").
    skew : float
        Skew factor controlling isotherm tilt.
    """

    if lang == "en":
        ylabel_name = "Pressure (hPa)"
        xlabel_name = "Temperature (°C)"
    if lang == "es":
        ylabel_name = "Presión (hPa)"
        xlabel_name = "Temperatura (°C)"

    fig, ax = plt.subplots(figsize=(7.5, 9))

    # Restrict calculations to visible pressure levels only
    mask = p >= pmin

    # --- Temperature profile ---
    T_skew = skew_transform(T, p, skew=skew)

    # Black outline for publication-quality contrast
    ax.plot(T_skew, p, linewidth=2.6, color="black", alpha=0.7, zorder=3)
    ax.plot(T_skew, p, linewidth=1.6, color="red", zorder=4, label="T (°C)")

    # Compute x-limits using only visible pressure range
    Xmax = np.max(T_skew[mask])
    Xmin = np.min(T_skew[mask])

    # --- Dewpoint profile ---
    if Td is not None:
        Td_skew = skew_transform(Td, p, skew=skew)

        ax.plot(Td_skew, p, linewidth=2.2, color="black", ls="--", alpha=0.6, zorder=3)
        ax.plot(Td_skew, p, linewidth=1.4, color="blue", ls="--", zorder=4, label="Td (°C)")

        # Update limits including dewpoint
        Xmin = min(Xmin, np.min(Td_skew[mask]))
        Xmax = max(Xmax, np.max(Td_skew[mask]))


    # --- Background isotherms ---
    T0s = np.arange(-200, 80, 10)
    p_grid = np.linspace(1010, 50, 200)

    for T0 in T0s:
        x_line = skew_transform(T0 * np.ones_like(p_grid), p_grid, skew=skew)

        # Emphasize every 20°C isotherm
        lw = 1.2 if (T0 % 20 == 0) else 0.8
        alpha = 0.35 if (T0 % 20 == 0) else 0.18

        ax.plot(x_line, p_grid, color="0.3", linewidth=lw, alpha=alpha, zorder=0)

    # Highlight the 0°C isotherm
    x0 = skew_transform(0 * np.ones_like(p_grid), p_grid, skew=skew)
    ax.plot(x0, p_grid, color="0.2", linewidth=1.6, alpha=0.6, zorder=1)

    # --- X-axis labeling referenced to surface pressure ---
    p_ref = 1025
    x_ticks = skew_transform(T0s, p_ref * np.ones_like(T0s), skew=skew)
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f"{t:d}" for t in T0s])
    ax.set_xlabel(xlabel_name)
    
    # --- Logarithmic pressure axis ---
    ax.set_yscale("log")
    ax.set_ylim(p_ref, pmin)
    ax.set_ylabel(ylabel_name)
    
    # Standard major pressure levels (NOAA-style)
    p_major = np.array([1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100])
    p_major = p_major[(p_major <= p_ref) & (p_major >= pmin)]
    ax.set_yticks(p_major)
    ax.set_yticklabels([f"{int(v)}" for v in p_major])

    # Pressure gridlines with hierarchical emphasis
    ax.grid(True, which="major", axis="y", linewidth=0.8, alpha=0.35)
    ax.grid(True, which="minor", axis="y", linewidth=0.5, alpha=0.15)
    

    # Set x-limits
    if xlim_C is not None:
        x_left  = skew_transform(xlim_C[0], p_ref, skew=skew)
        x_right = skew_transform(xlim_C[1], p_ref, skew=skew)
        ax.set_xlim(x_left, x_right)
    else:
        ax.set_xlim(Xmin - 10, Xmax + 10)

    # Draw 1000 hPa baseline
    ax.axhline(1000, color='black', linewidth=1.5, alpha=0.8, zorder=5)

    # --- Publication-style aesthetics ---
    ax.set_facecolor("white")

    for spine in ax.spines.values():
        spine.set_linewidth(1.1)

    ax.tick_params(axis="both", which="major", length=6, width=1.0, direction="out")
    ax.tick_params(axis="both", which="minor", length=3, width=0.8, direction="out")

    ax.legend(frameon=False, loc="upper right")

    plt.tight_layout()
    plt.show()
    return fig

