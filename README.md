## Description

This project is an interactive, visual simulation of a four-stroke internal combustion engine built using Python and the Pygame library. It aims to provide an educational tool to understand the fundamental mechanical operations and thermodynamic cycle (represented conceptually) of a typical engine.
The simulation displays the key components (piston, crankshaft, connecting rod, valves, spark plug) animating through the four strokes: Intake, Compression, Power, and Exhaust. It includes a particle system to visualize gas behavior and provides interactive controls and informational displays.

## Features

*   **Animated Engine Components:** Visual representation of piston, crankshaft, connecting rod movement.
*   **Valve System:** Synchronized intake and exhaust valve opening/closing based on the engine cycle.
*   **Spark Plug Visualization:** Visual spark ignition at the correct timing.
*   **4-Stroke Cycle Logic:** Accurate simulation of the Intake, Compression, Power, and Exhaust strokes over a 720-degree cycle.
*   **Particle Simulation:** Color-coded particles representing the air-fuel mixture/exhaust gases, demonstrating compression and expansion.
*   **Real-time PV Diagram:** A conceptual Pressure-Volume diagram plots the state of the gas inside the cylinder throughout the cycle.
*   **Component Annotations:** Labels pointing to the major parts of the engine.
*   **Dynamic Stroke Description:** Text display explaining the current stroke's actions.
*   **Interactive Controls:**
    *   Clickable Play/Pause, Reset, and Step (when paused) buttons.
    *   Draggable slider to control engine RPM (Revolutions Per Minute).
*   **Real-time Parameter Display:** Shows current RPM, cycle angle, stroke, conceptual volume, and pressure.

## Requirements

*   Python 3.x
*   Pygame library

## Installation

1.  **Clone the repository (or download the source code):**
    ```bash
    git clone <your_repository_url>
    cd <repository_directory_name>
    ```
    *(Replace `<your_repository_url>` and `<repository_directory_name>`)*

2.  **Install Pygame:**
    It's recommended to use a virtual environment:
    ```bash
    # Create a virtual environment (optional but recommended)
    python -m venv venv
    # Activate it (Windows)
    .\venv\Scripts\activate
    # Activate it (macOS/Linux)
    source venv/bin/activate

    # Install Pygame
    pip install pygame
    ```

## Usage

Run the main Python script from your terminal within the project directory (and with the virtual environment activated, if used):

```bash
python engine_sim.py
```

Controls
Play/Pause Button: Toggles the simulation between running and paused states.
Reset Button: Resets the simulation to its initial state (angle 0, paused).
Step Button: (Only works when paused) Advances the simulation by a small angle increment.
RPM Slider: Click and drag the knob to adjust the engine speed (RPM).
Keyboard: Press ESC key to quit the simulation.
