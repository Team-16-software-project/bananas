import os
import re
import time
import tkinter as tk
from tkinter import filedialog
import open3d as o3d

# Hide the main Tkinter window
root = tk.Tk()
root.withdraw()

# Prompt the user to select a directory
folder = filedialog.askdirectory(title='Select Folder Containing Frame Files')
if not folder:
    raise ValueError("No folder was selected.")

# Sort .ply files if they follow a naming convention like 'frame_0.ply'
ply_files = sorted(
    [f for f in os.listdir(folder) if f.endswith('.ply') and f.startswith('frame_')],
    key=lambda x: int(re.findall(r'\d+', x)[0])
)

frames = len(ply_files)
if frames == 0:
    raise ValueError("No frame files found in the selected folder.")

# Create a visualizer window
vis = o3d.visualization.VisualizerWithKeyCallback()
vis.create_window(width=800, height=600)

# Load the first point cloud
first_frame_path = os.path.join(folder, ply_files[0])
pcd = o3d.io.read_point_cloud(first_frame_path)
vis.add_geometry(pcd)

# Set a delay (in seconds) between frames
delay = 0.1
frame_index = 0
last_update_time = time.time()
is_paused = False

def animation_callback(vis):
    global frame_index, last_update_time, is_paused
    if is_paused:
        return False

    current_time = time.time()
    if current_time - last_update_time < delay:
        # Not enough time has passed; do nothing this callback
        return False
    last_update_time = current_time

    # Load the next frame
    frame_path = os.path.join(folder, ply_files[frame_index])
    print(f"Loading frame {frame_index}: {frame_path}")
    new_pcd = o3d.io.read_point_cloud(frame_path)
    
    # Update points, colors, and normals if they exist
    pcd.points = new_pcd.points
    pcd.colors = new_pcd.colors
    pcd.normals = new_pcd.normals
    
    vis.update_geometry(pcd)
    frame_index = (frame_index + 1) % frames  # loop back to first frame

    return False  # returning False continues the animation callback

def keyboard_callback(vis, action, mods):
    global is_paused
    if action == 1:
        is_paused = not is_paused
    return False

# Register the animation callback
vis.register_animation_callback(animation_callback)
vis.register_key_action_callback(ord(' '), keyboard_callback)

# Run the visualizer's main loop; this will keep the window interactive.
vis.run()
vis.destroy_window()
