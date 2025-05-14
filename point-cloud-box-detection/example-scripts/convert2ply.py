import os
import tkinter as tk
from tkinter import filedialog
import pyrealsense2 as rs

# Hide the main tkinter window
root = tk.Tk()
root.withdraw()

# Select the bag file
bag_file = filedialog.askopenfilename(
    title="Select RealSense Bag File",
    filetypes=[("Bag files", "*.bag"), ("All files", "*.*")]
)
if not bag_file:
    print("No bag file selected, exiting.")
    exit()

# Select the output folder
output_dir = filedialog.askdirectory(title="Select Output Folder for PLY Files")
if not output_dir:
    print("No output folder selected, exiting.")
    exit()

# Create the output folder if it doesn't exist (tkinter usually returns an existing folder, but this is a safeguard)
os.makedirs(output_dir, exist_ok=True)

# Set up the pipeline with the bag file
pipeline = rs.pipeline()
config = rs.config()
config.enable_device_from_file(bag_file, repeat_playback=False)
profile = pipeline.start(config)
profile.get_device().as_playback().set_real_time(False)

frame_number = 0
try:
    while True:
        frames = pipeline.wait_for_frames()

        # Create a file path inside the output directory
        ply_filename = os.path.join(output_dir, f"frame_{frame_number}.ply")

        # Export the current frame to a PLY file
        ply_exporter = rs.save_to_ply(ply_filename)
        ply_exporter.set_option(rs.save_to_ply.option_ply_binary, True)
        ply_exporter.set_option(rs.save_to_ply.option_ignore_color, False)
        ply_exporter.set_option(rs.save_to_ply.option_ply_normals, True)
        ply_exporter.process(frames)

        print(f"Saved frame {frame_number} to {ply_filename}")
        frame_number += 1

except Exception as e:
    print("Finished processing frames or encountered an error:", e)
finally:
    pipeline.stop()
