import os
import re
import tkinter as tk
from tkinter import filedialog
import open3d as o3d

def main():
    # Hide the Tkinter root window and prompt for folder selection
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Select Folder Containing PLY Files")
    if not folder:
        raise ValueError("No folder was selected.")

    # Get sorted list of PLY files (assumes filenames contain numbers, e.g. frame_0.ply, frame_1.ply, ...)
    ply_files = sorted(
        [f for f in os.listdir(folder) if f.endswith('.ply')],
        key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else 0
    )
    if not ply_files:
        raise ValueError("No PLY files found in the selected folder.")
    
    print(f"Found {len(ply_files)} PLY files in {folder}")

    # Define frame index and load the first point cloud
    frame_index = 0
    file_path = os.path.join(folder, ply_files[frame_index])
    pcd = o3d.io.read_point_cloud(file_path)

    # Create a visualizer with a key callback for spacebar
    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window(window_name="PLY Viewer", width=800, height=600)
    vis.add_geometry(pcd)

    def key_callback(vis, action, mods):
        nonlocal frame_index, pcd  # Use nonlocal to reference variables from the enclosing scope
        # Only trigger on key press (action == 1)
        if action == 1:
            frame_index += 1
            if frame_index >= len(ply_files):
                frame_index = 0  # loop back to the first file
            new_file = os.path.join(folder, ply_files[frame_index])
            new_pcd = o3d.io.read_point_cloud(new_file)
            # Update the geometry (points, colors, normals)
            pcd.points = new_pcd.points
            pcd.colors = new_pcd.colors
            pcd.normals = new_pcd.normals
            vis.update_geometry(pcd)
            print(f"Displaying: {ply_files[frame_index]}")
        return False

    # Register key callback for the spacebar (key code: ord(' '))
    vis.register_key_action_callback(ord(' '), key_callback)

    print("Press the spacebar to display the next PLY file.")
    vis.run()
    vis.destroy_window()

if __name__ == '__main__':
    main()