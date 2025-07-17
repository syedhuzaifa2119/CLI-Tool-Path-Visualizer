# CLI-Tool-Path-Visualizer
A Python GUI application for visualizing CNC tool paths from CLI files with heat modeling and animation.

## Features

- Parse CLI files with layers
- Visualize tool paths with heat distribution
- Animate tool movement step-by-step
- Layer Switching  
<img width="985" height="713" alt="Screenshot 2025-07-17 220506" src="https://github.com/user-attachments/assets/65c0ae1a-3d0b-4cd3-b9b4-6ecaa325625a" />



https://github.com/user-attachments/assets/e22bbd64-28a3-4128-86fb-bd9f6cddf6b8



## Installation

pip install numpy matplotlib tkinter
pip install numpy matplotlib
```

## Usage

## Running the Application
python test_toolpath_visualizer.py


1. Click "Load CLI File" to select your file
2. Choose layer from dropdown or select "All"
3. Toggle "Heat Overlay" to show thermal effects
4. Use "Play" to animate tool movement

## CLI File Format

```
$$LAYER/60
10.0,20.0
15.0,25.0
20.0,30.0

$$LAYER/90
25.0,35.0
30.0,40.0
```
## CLI File Parsing Logic

### Parser Architecture

The `CLIParser` class handles file parsing with the following logic:

#### Layer Detection
```python
$$LAYER/xxx  # Creates new layer with number xxx
```
- Uses regex pattern `\$\$LAYER/(\d+)` to extract layer numbers
- Subsequent coordinates are assigned to the current layer
- Layers are stored in a dictionary for easy access

#### Coordinate Parsing
The parser handles multiple coordinate formats:
- **Comma-separated**: `X,Y` (e.g., `10.5,20.3`)
- **Space-separated**: `X Y` (e.g., `10.5 20.3`)
- **Automatic detection**: Uses `is_coordinate_line()` to identify valid coordinates

#### Hatch Processing
```python
$$HATCHES/type/count/x1,y1,x2,y2,...
```
- Extracts coordinate pairs from hatch definitions
- Converts units from micrometers to millimeters (×0.001)
- Adds hatch points to the current layer

#### Error Handling
- Ignores malformed lines and continues parsing
- Skips comments and empty lines
- Gracefully handles missing or invalid data

## Heat Source Modeling

### Heat Distribution Model

#### Gaussian Heat Distribution
```python
heat_map = intensity * weight * exp(-r²/(2σ²))
```

Where:
- `intensity`: Base heat intensity (default: 1000)
- `weight`: Position-dependent weighting factor
- `σ` (sigma): Heat spread parameter (default: 2.0)
- `r`: Distance from heat source

#### Heat Decay Model
For animation, heat decays over time:
```python
decay_factor = decay_rate^(time_since_visit)
```

- `decay_rate`: Heat retention factor (default: 0.95)
- Newer tool positions contribute more heat
- Creates realistic cooling effect

#### Weighting Strategy
Heat intensity varies based on:
1. **Sequence position**: Earlier points have reduced intensity
2. **Time decay**: Heat dissipates over time in animations
3. **Current tool position**: Active tool head has maximum intensity

### Heat Visualization
- Uses matplotlib's `contourf` with 'hot' colormap
- 20 contour levels for smooth gradients
- Alpha blending (0.6) for overlay transparency
- Grid resolution: 50×50 points for performance

## GUI Structure

### Main Components

#### 1. Application Class (`ToolPathVisualizer`)
- **Main window**: 1000×700 pixels
- **State management**: Tracks current frame, animation state, and heat parameters
- **Event handling**: File loading, layer selection, animation control

#### 2. Control Panel
Located at the top of the interface:
- **File controls**: Load button and status label
- **Layer selector**: Dropdown for layer navigation
- **Heat toggle**: Enable/disable heat visualization
- **Animation controls**: Play/pause/reset buttons
- **Progress bar**: Shows animation progress

#### 3. Visualization Area
- **Matplotlib canvas**: Embedded plot area
- **Tool path display**: Lines, start/end markers, and legends
- **Heat overlay**: Contour plots for thermal visualization
- **Coordinate system**: Millimeter units with grid

#### 4. Status Bar
- **Real-time feedback**: Loading status, point counts, and layer information

### Threading Model
- **Main thread**: GUI updates and user interaction
- **Animation thread**: Background animation loop (daemon thread)
- **Thread safety**: Uses `root.after()` for GUI updates from worker threads

## Configuration Options

### Heat Parameters
Modify these variables in the `__init__` method:
```python
self.heat_intensity = 1000      # Base heat intensity
self.heat_sigma = 2.0           # Heat spread radius
self.heat_decay_rate = 0.95     # Heat retention factor
```

## Requirements

- Python 3.7+
- numpy
- matplotlib
- tkinter (included with Python)
