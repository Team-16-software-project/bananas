import os
import glob
import re
import tkinter as tk
from tkinter import filedialog
import open3d as o3d
import numpy as np

# Import the process_point_cloud function from your installed package
from ply_processor.point_cloud_processor import process_point_cloud

def select_folder(title):
    """Open a Tkinter dialog to select a folder."""
    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title=title)
    return folder_selected

def extract_number(filename):
    """Extract the first occurring number from a filename."""
    match = re.search(r'\d+', filename)
    return int(match.group()) if match else -1

def sample_bounding_box_edges(obb, points_per_edge=10):
    """
    Sample points along the edges of an oriented bounding box (OBB).
    
    Parameters:
        obb (open3d.geometry.OrientedBoundingBox): The bounding box.
        points_per_edge (int): Number of points to sample along each edge (including endpoints).
        
    Returns:
        open3d.geometry.PointCloud: A point cloud containing the sampled edge points.
    """
    # Get the 8 corners of the bounding box.
    corners = np.asarray(obb.get_box_points())
    
    # Define edges by the indices of the corner points.
    edges = [(0, 1), (0, 2), (0, 3),
             (4, 5), (4, 6), (4, 7),
             (1, 6), (1, 7),
             (2, 5), (2, 7),
             (3, 5), (3, 6)]
    
    sampled_points = []
    # For each edge, interpolate between the two corners.
    for start_idx, end_idx in edges:
        start = corners[start_idx]
        end = corners[end_idx]
        # Generate points_per_edge along the edge, including the endpoints.
        for t in np.linspace(0, 1, points_per_edge):
            point = (1 - t) * start + t * end
            sampled_points.append(point)
    
    # Create a point cloud from the sampled points.
    edge_pcd = o3d.geometry.PointCloud()
    edge_pcd.points = o3d.utility.Vector3dVector(np.array(sampled_points))
    return edge_pcd

def combine_geometries(visible_pcd, bounding_boxes_processed):
    """
    Combine the visible point cloud with a point cloud representation of bounding boxes.
    The bounding boxes are sampled to point clouds and colored red.
    """
    combined = visible_pcd
    for obb in bounding_boxes_processed:
        bbox_pcd = sample_bounding_box_edges(obb, points_per_edge=10)
        bbox_pcd.paint_uniform_color([1, 0, 0])  # Color red
        combined += bbox_pcd
    return combined

def process_all_files(input_folder, output_folder):
    # Find all .ply files in the input folder
    ply_files = glob.glob(os.path.join(input_folder, "*.ply"))
    
    if not ply_files:
        print("No PLY files found in the selected folder.")
        return

    # Sort files based on the numeric part of the filename
    ply_files = sorted(ply_files, key=lambda f: extract_number(os.path.basename(f)))
    
    for ply_file in ply_files:
        print(f"Processing {ply_file}...")
        try:
            # Process the file using your module function
            pcd = o3d.io.read_point_cloud(ply_file)
            result = process_point_cloud(pcd)
            
            # Get the original (visible) point cloud and the processed bounding boxes
            bounding_boxes_processed = result["bounding_boxes"]
            
            # Combine them into a single point cloud for export
            combined_pcd = combine_geometries(pcd, bounding_boxes_processed)
            
            # Prepare output file path: append '_processed' to filename
            base_name = os.path.splitext(os.path.basename(ply_file))[0]
            output_file = os.path.join(output_folder, f"{base_name}.ply")
            
            # Write the combined point cloud to a PLY file
            o3d.io.write_point_cloud(output_file, combined_pcd)
            print(f"Saved processed file to: {output_file}")
        except Exception as e:
            print(f"Error processing {ply_file}: {e}")

def main():
    print("Select the input folder containing PLY files.")
    input_folder = select_folder("Select Input Folder")
    if not input_folder:
        print("No input folder selected. Exiting.")
        return

    print("Select the output folder to save processed PLY files.")
    output_folder = select_folder("Select Output Folder")
    if not output_folder:
        print("No output folder selected. Exiting.")
        return

    process_all_files(input_folder, output_folder)
    print("Processing complete.")

if __name__ == "__main__":
    main()
