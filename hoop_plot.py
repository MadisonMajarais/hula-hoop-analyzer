import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot_hoop_data(df, min_swing_frac):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
    ax1.plot(df["time"], df["x_pos"], label="x_pos")
    ax1.plot(df["time"], df["drift"], label="drift")
    ax1.set_ylabel("pixels")
    ax1.set_title("Drift of person moving horizontally while hula hooping")
    ax1.legend()

    ax2.plot(df["time"], df["offset"])
    ax2.set_xlabel("time (s)")
    ax2.set_ylabel("offset")
    ax2.axhline(min_swing_frac, linestyle="--", color="gray")
    ax2.axhline(-min_swing_frac, linestyle="--", color="gray")
    ax2.set_title("Hoop centre position relative to person")

    fig.savefig("static/outputs/offset.png", dpi=100)
    plt.close(fig)
