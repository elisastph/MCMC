import numpy as np
import matplotlib.pyplot as plt
import os
from typing import Optional
import glob
import base64
import re
import matplotlib.animation as animation
from typing import List, Tuple
from matplotlib.animation import PillowWriter
import streamlit as st
import streamlit.components.v1 as components

def plot_ising_lattice(lattice: np.ndarray, step: Optional[int] = None):
    """Visualize Ising lattice as a binary colormap."""
    plt.figure(figsize=(6, 6))
    plt.imshow(lattice, cmap='gray', vmin=-1, vmax=1)
    plt.title(f"Ising Model{' - Step ' + str(step) if step else ''}")
    plt.axis('off')
    plt.colorbar(label="Spin")
    plt.tight_layout()
    plt.show()

def plot_clock_lattice(lattice: np.ndarray, M: int, step: Optional[int] = None):
    """Visualize Clock model lattice using quiver plot."""
    angles = 2 * np.pi * lattice / M
    U = np.cos(angles)
    V = np.sin(angles)
    X, Y = np.meshgrid(np.arange(lattice.shape[1]), np.arange(lattice.shape[0]))

    plt.figure(figsize=(6, 6))
    plt.quiver(X, Y, U, V, pivot='middle', headwidth=2, headlength=3, scale=30)
    plt.title(f"Clock Model{' - Step ' + str(step) if step else ''}")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def plot_xy_lattice(lattice: np.ndarray, step: Optional[int] = None):
    """Visualize XY model lattice using quiver plot with continuous angles."""
    U = np.cos(lattice)
    V = np.sin(lattice)
    X, Y = np.meshgrid(np.arange(lattice.shape[1]), np.arange(lattice.shape[0]))

    plt.figure(figsize=(6, 6))
    plt.quiver(X, Y, U, V, pivot='middle', headwidth=2, headlength=3, scale=30)
    plt.title(f"XY Model{' - Step ' + str(step) if step else ''}")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def load_lattices_for_model(model_name, folder="../results"):
    files = sorted(glob.glob(f"{folder}/lattice_{model_name}_*.csv"))

    # Nur zweite Hälfte verwenden
    total = len(files)
    files = files[total // 2:]

    steps = []
    lattices = []

    for file in files:
        match = re.search(r"_(\d+)\.csv", file)
        if not match:
            continue
        step = int(match.group(1))
        data = np.loadtxt(file, delimiter=",")
        steps.append(step)
        lattices.append(data)

    return steps, lattices

def load_lattices_for_model_and_temperature(model_name: str, T: float, folder: str = "../results"):
    pattern = f"{folder}/lattice_{model_name}_T{T:.2f}_*.csv"
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"Keine Dateien gefunden für {model_name} bei T={T:.2f}")
        return [], []

    # Zweite Hälfte der Dateien verwenden
    total = len(files)
    files = files[total // 2:]

    steps, lattices = [], []

    for file in files:
        match = re.search(rf"_T{T:.2f}_(\d+)\.csv", file)
        if not match:
            continue
        step = int(match.group(1))
        data = np.loadtxt(file, delimiter=",")
        steps.append(step)
        lattices.append(data)

    return steps, lattices

def animate_ising(steps, lattices, T_target: float, save_path="ising_animation.gif"):
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(lattices[0], cmap="gray", vmin=-1, vmax=1)
    # im = ax.imshow(lattices[0], cmap='RdBu', vmin=-1, vmax=1)
    ax.set_title(f"Ising Model - {T_target} T - Step {steps[0]}")
    ax.axis("off")

    def update(frame):
        im.set_array(lattices[frame])
        ax.set_title(f"Ising Model - {T_target} T - Step {steps[frame]}")
        return [im]

    ani = animation.FuncAnimation(fig, update, frames=len(lattices), interval=100)
    ani.save(save_path, writer=PillowWriter(fps=10))
    print(f"✅ Animation gespeichert als {save_path}")
    plt.close()

def animate_clock(steps: List[int], lattices: List[np.ndarray], T_target: float, M: int = 8, save_path: str = "clock_animation.gif"):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0)

    angles = 2 * np.pi * lattices[0] / M
    U = np.cos(angles)
    V = np.sin(angles)
    X, Y = np.meshgrid(np.arange(lattices[0].shape[1]), np.arange(lattices[0].shape[0]))

    quiv = ax.quiver(X, Y, U, V, pivot='middle', headwidth=2, headlength=3, scale=30)

    def update(frame):
        angles = 2 * np.pi * lattices[frame] / M
        U = np.cos(angles)
        V = np.sin(angles)
        quiv.set_UVC(U, V)
        ax.set_title(f"Clock Model - {T_target} T - Step {steps[frame]}")

    ani = animation.FuncAnimation(fig, update, frames=len(lattices), interval=100)
    ani.save(save_path, writer=PillowWriter(fps=10))
    print(f"✅ Animation gespeichert als {save_path}")
    plt.close()

def animate_xy(steps: List[int], lattices: List[np.ndarray], T_target: float, save_path: str = "xy_animation.gif"):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0)


    U = np.cos(lattices[0])
    V = np.sin(lattices[0])
    X, Y = np.meshgrid(np.arange(lattices[0].shape[1]), np.arange(lattices[0].shape[0]))
    quiv = ax.quiver(X, Y, U, V, pivot='middle', headwidth=2, headlength=3, scale=30)

    def update(frame):
        U = np.cos(lattices[frame])
        V = np.sin(lattices[frame])
        quiv.set_UVC(U, V)
        ax.set_title(f"XY Model - {T_target} T - Step {steps[frame]}")

    ani = animation.FuncAnimation(fig, update, frames=len(lattices), interval=100)
    ani.save(save_path, writer=PillowWriter(fps=10))
    print(f"✅ Animation gespeichert als {save_path}")
    plt.close()


def load_and_plot_all():
    examples = {
        "ising": ("../results/Lattice_Ising_1000.csv", plot_ising_lattice, {}),
        "clock": ("../results/Lattice_Clock_1000.csv", plot_clock_lattice, {"M": 8}),
        "xy": ("../results/Lattice_XY_1000.csv", plot_xy_lattice, {}),
    }

    for model, (filename, plot_func, kwargs) in examples.items():
        if os.path.exists(filename):
            lattice = np.loadtxt(filename, delimiter=",")
            print(f"📂 Visualizing {model} from {filename}")
            plot_func(lattice, step=1000, **kwargs)
        else:
            print(f"⚠️ Datei nicht gefunden: {filename}")

def generate_and_display_lattice_animations(models_selected, T_target, output_dir, display_width=300):
    # os.makedirs(output_dir, exist_ok=True)

    for model in models_selected:
        steps, lattices = load_lattices_for_model_and_temperature(model, T_target)

        if steps:
            gif_path = f"{output_dir}/{model.lower()}_T{T_target:.2f}.gif"
            
            if model == "Ising":
                animate_ising(steps, lattices, T_target, save_path=gif_path)
            elif model == "Clock":
                animate_clock(steps, lattices, T_target, M=8, save_path=gif_path)
            elif model == "XY":
                animate_xy(steps, lattices, T_target, save_path=gif_path)
            # GIF in Bytes lesen
            with open(gif_path, "rb") as f:
                gif_bytes = f.read()

            b64 = base64.b64encode(gif_bytes).decode()
            # display_width = 300

            html = f"""
            <img
            src="data:image/gif;base64,{b64}"
            style="
                display: block;
                margin-left: 0px;
                margin-right: auto;
                width: {display_width}px;
                height: {display_width}px;
            "
            />
            """
            components.html(
                html,
                width=display_width,
                height=display_width
            )

if __name__ == "__main__":
    output_dir = "../analysis_results/visualize_lattices"
    os.makedirs(output_dir, exist_ok=True)

    T_target = 2.0 # Beispiel: nur T=2.00 animieren

    steps, lattices = load_lattices_for_model_and_temperature("Ising", T_target)
    if steps:
        animate_ising(steps, lattices, T_target, save_path=f"{output_dir}/ising_T{T_target:.2f}.gif")

    clock_steps, clock_lattices = load_lattices_for_model_and_temperature("Clock", T_target)
    if clock_steps:
        animate_clock(clock_steps, clock_lattices, T_target, M=8, save_path=f"{output_dir}/clock_T{T_target:.2f}.gif")

    xy_steps, xy_lattices = load_lattices_for_model_and_temperature("XY", T_target)
    if xy_steps:
        animate_xy(xy_steps, xy_lattices, T_target, save_path=f"{output_dir}/xy_T{T_target:.2f}.gif")
