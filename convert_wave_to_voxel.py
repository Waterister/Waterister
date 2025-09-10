"""
Main script for converting geologic pblock models from wave to voxel format.

This script demonstrates the complete workflow:
1. Read wave format geologic model
2. Convert to voxel grid
3. Export to ArcGIS-compatible formats
"""

import os
import sys
import argparse
from typing import Optional

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from geologic_processing import WaveReader, VoxelConverter, ArcGISExporter


def main():
    """Main conversion workflow."""
    parser = argparse.ArgumentParser(description='Convert geologic pblock models from wave to voxel format')
    parser.add_argument('input_file', help='Input wave format file')
    parser.add_argument('-o', '--output', default='./output', help='Output directory (default: ./output)')
    parser.add_argument('--voxel-size', type=float, default=10.0, help='Voxel size in model units (default: 10.0)')
    parser.add_argument('--format', choices=['netcdf', 'ascii', 'csv', 'all'], default='all', 
                       help='Output format (default: all)')
    parser.add_argument('--sample-rate', type=float, default=1.0, 
                       help='Sampling rate for point cloud export (0.0-1.0, default: 1.0)')
    parser.add_argument('--coordinate-system', default='EPSG:4326',
                       help='Coordinate reference system (default: EPSG:4326)')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found")
        return 1
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    print("=" * 60)
    print("Geologic Pblock Model Wave-to-Voxel Conversion")
    print("=" * 60)
    print(f"Input file: {args.input_file}")
    print(f"Output directory: {args.output}")
    print(f"Voxel size: {args.voxel_size}")
    print(f"Output format(s): {args.format}")
    print()
    
    try:
        # Step 1: Read wave format file
        print("Step 1: Reading wave format file...")
        reader = WaveReader(args.input_file)
        
        if not reader.read_wave_file():
            print("Error: Failed to read wave format file")
            return 1
        
        blocks = reader.get_blocks()
        bounds = reader.get_bounds()
        
        print(f"  - Successfully read {len(blocks)} geologic blocks")
        if bounds:
            print(f"  - Spatial bounds: X=[{bounds['xmin']:.2f}, {bounds['xmax']:.2f}], "
                  f"Y=[{bounds['ymin']:.2f}, {bounds['ymax']:.2f}], "
                  f"Z=[{bounds['zmin']:.2f}, {bounds['zmax']:.2f}]")
        print()
        
        # Step 2: Convert to voxel grid
        print("Step 2: Converting to voxel grid...")
        converter = VoxelConverter(voxel_size=args.voxel_size)
        
        voxel_grid = converter.convert_blocks_to_voxels(blocks, bounds)
        
        print(f"  - Created voxel grid with dimensions: {voxel_grid.dimensions}")
        print(f"  - Voxel spacing: {voxel_grid.spacing}")
        print(f"  - Grid origin: {voxel_grid.origin}")
        print()
        
        # Step 3: Export to ArcGIS formats
        print("Step 3: Exporting to ArcGIS-compatible formats...")
        exporter = ArcGISExporter(coordinate_system=args.coordinate_system)
        
        exported_files = []
        base_name = os.path.splitext(os.path.basename(args.input_file))[0]
        
        try:
            if args.format in ['netcdf', 'all']:
                print("  - Exporting to NetCDF format...")
                netcdf_path = os.path.join(args.output, f"{base_name}_voxels.nc")
                if exporter.export_to_netcdf(voxel_grid, netcdf_path):
                    exported_files.append(netcdf_path)
            
            if args.format in ['ascii', 'all']:
                print("  - Exporting to ASCII grid format...")
                ascii_dir = os.path.join(args.output, f"{base_name}_ascii_grids")
                if exporter.export_to_ascii_grids(voxel_grid, ascii_dir):
                    exported_files.append(ascii_dir)
            
            if args.format in ['csv', 'all']:
                print("  - Exporting to CSV point cloud...")
                csv_path = os.path.join(args.output, f"{base_name}_points.csv")
                if exporter.export_to_point_cloud(voxel_grid, csv_path, sample_rate=args.sample_rate):
                    exported_files.append(csv_path)
            
            # Create ArcGIS import instructions
            exporter.create_arcgis_project_file(args.output, exported_files)
            
            print()
            print("Conversion completed successfully!")
            print(f"Output files saved to: {args.output}")
            print("See 'arcgis_import_instructions.txt' for ArcGIS import guidance.")
            
        finally:
            # Clean up any temporary files
            exporter.cleanup_temp_files()
        
        return 0
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        return 1


def create_example_wave_file(output_path: str = "example_geologic_model.wave"):
    """
    Create an example wave format file for testing.
    
    Args:
        output_path: Path for the example file
    """
    print(f"Creating example wave file: {output_path}")
    
    # Create a simple text-based wave format file
    with open(output_path, 'w') as f:
        f.write("# WAVE_FORMAT v1.0\n")
        f.write("# Geologic Pblock Model - Example\n")
        f.write("# BOUNDS: 0.0 0.0 0.0 1000.0 1000.0 200.0\n")
        f.write("# BLOCKS: 100\n")
        f.write("# Format: X Y Z WIDTH HEIGHT DEPTH ROCK_TYPE POROSITY PERMEABILITY\n")
        f.write("#\n")
        
        # Generate example blocks
        import random
        random.seed(42)  # For reproducible results
        
        for i in range(100):
            x = random.uniform(50, 950)
            y = random.uniform(50, 950) 
            z = random.uniform(10, 190)
            width = random.uniform(20, 100)
            height = random.uniform(20, 100)
            depth = random.uniform(10, 50)
            
            # Rock types
            rock_types = ['sandstone', 'limestone', 'shale', 'granite', 'basalt']
            rock_type = random.choice(rock_types)
            
            # Properties based on rock type
            if rock_type == 'sandstone':
                porosity = random.uniform(0.1, 0.3)
                permeability = random.uniform(1e-12, 1e-10)
            elif rock_type == 'limestone':
                porosity = random.uniform(0.05, 0.25)
                permeability = random.uniform(1e-15, 1e-11)
            elif rock_type == 'shale':
                porosity = random.uniform(0.02, 0.1)
                permeability = random.uniform(1e-18, 1e-15)
            elif rock_type == 'granite':
                porosity = random.uniform(0.001, 0.05)
                permeability = random.uniform(1e-20, 1e-16)
            else:  # basalt
                porosity = random.uniform(0.01, 0.15)
                permeability = random.uniform(1e-17, 1e-13)
            
            f.write(f"{x:.2f} {y:.2f} {z:.2f} {width:.2f} {height:.2f} {depth:.2f} "
                   f"{rock_type} {porosity:.6f} {permeability:.2e}\n")
    
    print(f"Example wave file created with 100 blocks")


if __name__ == "__main__":
    # Check if we need to create an example file
    if len(sys.argv) > 1 and sys.argv[1] == "--create-example":
        create_example_wave_file()
        print("\nTo convert the example file, run:")
        print("python convert_wave_to_voxel.py example_geologic_model.wave")
    else:
        exit_code = main()
        sys.exit(exit_code)