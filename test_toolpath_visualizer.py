import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import threading
import time

class CLIParser:
    def __init__(self):
        self.points = []
        self.layers = {}
        self.current_layer = 0
        
    def parse_file(self, filepath: str):
        self.points = []
        self.layers = {}
        self.current_layer = 0
        
        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith(('//', '#')):
                    continue
                    
                # Layer parsing 
                if line.upper().startswith('$$LAYER'):
                    layer_match = re.search(r'\$\$LAYER/(\d+)', line)
                    if layer_match:
                        self.current_layer = int(layer_match.group(1))
                        print(f"Found layer: {self.current_layer}")  
                
                # Hatch parsing
                if line.upper().startswith('$$HATCHES'):
                    try:
                        parts = line.split('/')[-1].split(',')
                        coords = parts[2:2 + int(parts[1]) * 2]
                        for i in range(0, len(coords), 2):
                            if i + 1 < len(coords):
                                point = (float(coords[i]) * 0.001, float(coords[i+1]) * 0.001)
                                self.points.append(point)
                                self.layers.setdefault(self.current_layer, []).append(point)
                    except:
                        pass
                
                # Coordinate parsing
                elif self.is_coordinate_line(line):
                    self.parse_coordinate_line(line)
                    
        return self.points

    def is_coordinate_line(self, line: str) -> bool:
        if any(x in line for x in [',', ' ']):
            parts = line.replace(',', ' ').split()
            if len(parts) >= 2:
                try:
                    float(parts[0])
                    float(parts[1])
                    return True
                except ValueError:
                    pass
        return False

    def parse_coordinate_line(self, line: str):
        try:
            if ',' in line:
                coords = [c.strip() for c in line.split(',')]
                x, y = float(coords[0]), float(coords[1])
            else:
                coords = line.split()
                x, y = float(coords[0]), float(coords[1])
            
            point = (x, y)
            self.points.append(point)
            self.layers.setdefault(self.current_layer, []).append(point)
        except:
            pass

class ToolPathVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("2D Tool Path Visualizer")
        self.root.geometry("1000x700")
        
        self.points = []
        self.layers = {}
        self.parser = CLIParser()
        self.current_frame = 0
        self.is_playing = False
        self.animation_speed = 50
        self.heat_intensity = 1000
        self.heat_sigma = 2.0
        self.heat_decay_rate = 0.95  # heat decays over time
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Controls
        ctrl = ttk.Frame(main_frame)
        ctrl.pack(fill=tk.X, pady=(0, 10))
        
        # File , visualization controls
        ttk.Button(ctrl, text="Load CLI File", command=self.load_cli_file).pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(ctrl, text="No file loaded")
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        # Layer controls
        ttk.Label(ctrl, text="Layer:").pack(side=tk.LEFT, padx=5)
        self.layer_var = tk.StringVar(value="All")
        self.layer_combo = ttk.Combobox(ctrl, textvariable=self.layer_var, width=8, state="readonly")
        self.layer_combo.pack(side=tk.LEFT, padx=5)
        self.layer_combo.bind('<<ComboboxSelected>>', lambda e: self.update_visualization())
        
        # Heat controls
        self.heat_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(ctrl, text="Heat Overlay", variable=self.heat_enabled_var, 
                       command=self.update_visualization).pack(side=tk.LEFT, padx=20)
        
        # Animation controls
        self.play_button = ttk.Button(ctrl, text="Play", command=self.toggle_animation)
        self.play_button.pack(side=tk.LEFT, padx=20)
        ttk.Button(ctrl, text="Reset", command=self.reset_animation).pack(side=tk.LEFT, padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(ctrl, variable=self.progress_var, maximum=100, length=200)
        self.progress_bar.pack(side=tk.LEFT, padx=10)
        
        # Plot
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, main_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status_var).pack(fill=tk.X, pady=(5, 0))
        
        self.setup_empty_plot()

    def setup_empty_plot(self):
        self.ax.clear()
        self.ax.set_xlabel('X (mm)')
        self.ax.set_ylabel('Y (mm)')
        self.ax.set_title(f'Tool Path - Layer {self.layer_var.get()}')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()

    def load_cli_file(self):
        file_path = filedialog.askopenfilename(
            title="Select CLI File",
            filetypes=[("CLI files", "*.cli"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            self.status_var.set("Loading...")
            self.root.update()
            
            self.points = self.parser.parse_file(file_path)
            self.layers = self.parser.layers
            
            if not self.points:
                messagebox.showerror("Error", "No valid tool path data found")
                return
                
            self.file_label.config(text=f"Loaded: {len(self.points)} points")
            
            sorted_layers = sorted(self.layers.keys())
            self.layer_combo['values'] = ["All"] + [str(i) for i in sorted_layers]
            self.layer_combo.set("All")
            
            self.update_visualization()
            self.status_var.set(f"Loaded {len(self.points)} points from {len(self.layers)} layers")
            
            # Debug: Print found layers
            print(f"Found layers: {sorted_layers}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def get_display_points(self):
        if self.layer_var.get() == "All":
            return self.points
        else:
            layer_num = int(self.layer_var.get())
            return self.layers.get(layer_num, [])

    def update_visualization(self):
        if not self.points:
            return
            
        self.ax.clear()
        display_points = self.get_display_points()
        
        if not display_points:
            self.setup_empty_plot()
            return
            
        x_coords, y_coords = zip(*display_points)
        
        self.ax.plot(x_coords, y_coords, 'b-', linewidth=1, alpha=0.7, label='Tool Path')
        self.ax.plot(x_coords[0], y_coords[0], 'go', markersize=8, label='Start')
        self.ax.plot(x_coords[-1], y_coords[-1], 'ro', markersize=8, label='End')
        
        if self.heat_enabled_var.get():
            self.add_heat_overlay(display_points)
        
        self.ax.set_xlabel('X (mm)')
        self.ax.set_ylabel('Y (mm)')
        self.ax.set_title(f'Tool Path Visualization - Layer {self.layer_var.get()}')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        self.ax.set_aspect('equal')
        self.canvas.draw()

    def add_heat_overlay(self, points):
        if not points:
            return
            
        x_coords, y_coords = zip(*points)
        padding = 5
        x_min, x_max = min(x_coords) - padding, max(x_coords) + padding
        y_min, y_max = min(y_coords) - padding, max(y_coords) + padding
        
        x_grid = np.linspace(x_min, x_max, 50)
        y_grid = np.linspace(y_min, y_max, 50)
        X, Y = np.meshgrid(x_grid, y_grid)
        
        heat_map = np.zeros_like(X)
        for i, (px, py) in enumerate(points):
            weight = 1.0 - (i / len(points)) * 0.8
            r_squared = (X - px)**2 + (Y - py)**2
            heat_map += self.heat_intensity * weight * np.exp(-r_squared / (2 * self.heat_sigma**2))
        
        if np.max(heat_map) > 0:
            self.ax.contourf(X, Y, heat_map, levels=20, cmap='hot', alpha=0.6)

    def toggle_animation(self):
        if not self.points:
            messagebox.showwarning("Warning", "Please load a CLI file first")
            return
        
        # Check if selected layer has points
        display_points = self.get_display_points()
        if not display_points:
            messagebox.showwarning("Warning", f"No points found for layer {self.layer_var.get()}")
            return
            
        self.is_playing = not self.is_playing
        self.play_button.config(text="Pause" if self.is_playing else "Play")
        
        if self.is_playing:
            threading.Thread(target=self.animate_tool_path, daemon=True).start()

    def animate_tool_path(self):
        self.current_frame = 0
        self.animation_points = self.get_display_points()
        total_frames = len(self.animation_points)
        
        if total_frames == 0:
            self.is_playing = False
            self.play_button.config(text="Play")
            return
        
        self.heat_history = []
        
        while self.is_playing and self.current_frame < total_frames:
            self.root.after(0, self.update_animation_frame)
            self.progress_var.set((self.current_frame / total_frames) * 100)
            self.current_frame += 1
            time.sleep(self.animation_speed / 1000.0)
        
        self.root.after(0, lambda: self.play_button.config(text="Play"))
        self.is_playing = False

    def update_animation_frame(self):
        if not hasattr(self, 'animation_points') or self.current_frame >= len(self.animation_points):
            return
            
        self.ax.clear()
        current_points = self.animation_points[:self.current_frame + 1]
        
        if len(current_points) > 1:
            x_coords, y_coords = zip(*current_points)
            self.ax.plot(x_coords[:-1], y_coords[:-1], 'b-', linewidth=1, alpha=0.7)
            
            # Current point
            current_x, current_y = current_points[-1]
            self.ax.plot(current_x, current_y, 'ro', markersize=8)
            
            if self.heat_enabled_var.get():
                self.add_realistic_animation_heat(current_points)
        
        self.ax.set_xlabel('X (mm)')
        self.ax.set_ylabel('Y (mm)')
        self.ax.set_title(f'Animation - Layer {self.layer_var.get()} - Point {self.current_frame}/{len(self.animation_points)}')
        self.ax.grid(True, alpha=0.3)
        
        if len(self.animation_points) > 0:
            all_x, all_y = zip(*self.animation_points)
            padding = 5
            self.ax.set_xlim(min(all_x) - padding, max(all_x) + padding)
            self.ax.set_ylim(min(all_y) - padding, max(all_y) + padding)
        self.ax.set_aspect('equal')
        self.canvas.draw()

    def add_realistic_animation_heat(self, current_points):
        """ accumulated heat overlay """
        if not current_points:
            return
            
        all_x, all_y = zip(*self.animation_points)
        padding = 5
        x_min, x_max = min(all_x) - padding, max(all_x) + padding
        y_min, y_max = min(all_y) - padding, max(all_y) + padding
        
        x_grid = np.linspace(x_min, x_max, 50)
        y_grid = np.linspace(y_min, y_max, 50)
        X, Y = np.meshgrid(x_grid, y_grid)
        
        heat_map = np.zeros_like(X)
        
        for i, (px, py) in enumerate(current_points):
            time_since = len(current_points) - i - 1
            decay_factor = (self.heat_decay_rate ** time_since)
            
            sequence_weight = 1.0 - (i / len(current_points)) * 0.3
            
            total_weight = decay_factor * sequence_weight
            
            # Add Gaussian heat distribution for this point
            r_squared = (X - px)**2 + (Y - py)**2
            heat_contribution = self.heat_intensity * total_weight * np.exp(-r_squared / (2 * self.heat_sigma**2))
            heat_map += heat_contribution
        
        if len(current_points) > 0:
            current_x, current_y = current_points[-1]
            r_squared = (X - current_x)**2 + (Y - current_y)**2
            current_heat = self.heat_intensity * 1.5 * np.exp(-r_squared / (2 * (self.heat_sigma * 0.8)**2))
            heat_map += current_heat
        
        if np.max(heat_map) > 0:
            self.ax.contourf(X, Y, heat_map, levels=20, cmap='hot', alpha=0.6)


    def reset_animation(self):
        self.is_playing = False
        self.play_button.config(text="Play")
        self.current_frame = 0
        self.progress_var.set(0)
        # Clear heat history
        if hasattr(self, 'heat_history'):
            self.heat_history = []
        self.update_visualization()

def main():
    root = tk.Tk()
    app = ToolPathVisualizer(root)    
    try:
        app.points = app.parser.parse_file("task 2.cli")
        app.layers = app.parser.layers
        if app.points:
            app.file_label.config(text=f"Loaded: {len(app.points)} points")
            sorted_layers = sorted(app.layers.keys())
            app.layer_combo['values'] = ["All"] + [str(i) for i in sorted_layers]
            app.layer_combo.set("All")
            app.update_visualization()
            app.status_var.set(f"Auto-loaded {len(app.points)} points from {len(app.layers)} layers")
    except:
        pass
    
    root.mainloop()

if __name__ == "__main__":
    main()
