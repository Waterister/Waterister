"""
Quick demonstration of the geologic pblock wave-to-voxel conversion.

This script shows a minimal example of the conversion workflow.
"""

import sys
import os

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from geologic_processing import WaveReader, VoxelConverter, ArcGISExporter


def demo_conversion():
    """Demonstrate the basic conversion workflow."""
    print("Geologic Pblock Wave-to-Voxel Conversion Demo")
    print("=" * 50)
    
    # Step 1: Create a simple example
    print("Creating example data...")
    example_file = "demo_model.wave"
    
    with open(example_file, 'w') as f:
        f.write("# WAVE_FORMAT v1.0\n")
        f.write("# Demo geologic model\n") 
        f.write("# BOUNDS: 0.0 0.0 0.0 100.0 100.0 50.0\n")
        f.write("# BLOCKS: 2\n")
        f.write("# X Y Z WIDTH HEIGHT DEPTH ROCK_TYPE POROSITY PERMEABILITY\n")
        f.write("25.0 25.0 15.0 30.0 30.0 20.0 sandstone 0.20 1.0e-12\n")
        f.write("75.0 75.0 35.0 30.0 30.0 20.0 limestone 0.10 5.0e-14\n")
    
    # Step 2: Read the data
    print("Reading wave format file...")
    reader = WaveReader(example_file)
    if not reader.read_wave_file():
        print("Failed to read wave file")
        return
    
    blocks = reader.get_blocks()
    print(f"Read {len(blocks)} geologic blocks")
    
    # Step 3: Convert to voxels
    print("Converting to voxel grid...")
    converter = VoxelConverter(voxel_size=20.0)
    voxel_grid = converter.convert_blocks_to_voxels(blocks)
    print(f"Created voxel grid: {voxel_grid.dimensions}")
    
    # Step 4: Export results
    print("Exporting to ArcGIS formats...")
    exporter = ArcGISExporter()
    
    # Export to CSV point cloud
    csv_file = "demo_points.csv"
    if exporter.export_to_point_cloud(voxel_grid, csv_file):
        print(f"Created point cloud: {csv_file}")
    
    # Export ASCII grids
    ascii_dir = "demo_grids"
    if exporter.export_to_ascii_grids(voxel_grid, ascii_dir, 'porosity'):
        print(f"Created ASCII grids: {ascii_dir}/")
    
    print("\nDemo completed! Files created:")
    print(f"- {example_file} (input wave format)")
    print(f"- {csv_file} (CSV point cloud)")
    print(f"- {ascii_dir}/ (ASCII grid layers)")
    
    print("\nTo process your own data, use:")
    print("python convert_wave_to_voxel.py your_model.wave")
    
    # Clean up
    try:
        os.remove(example_file)
    except:
        pass


if __name__ == "__main__":
    demo_conversion()