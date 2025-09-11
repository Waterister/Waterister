"""
ArcGIS Exporter for Voxel Data

This module exports voxel grids to formats compatible with ArcGIS,
including NetCDF, ASCII grids, and feature classes.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import os
from .voxel_converter import VoxelGrid
import tempfile


class ArcGISExporter:
    """
    Exports voxel grids to various ArcGIS-compatible formats.
    
    Supported formats:
    - NetCDF (.nc) - for 3D voxel visualization
    - ASCII Grid (.asc) - for 2D slice visualization  
    - CSV Point Cloud - for importing as 3D points
    - Shapefile - for block representations
    """
    
    def __init__(self, coordinate_system: str = "EPSG:4326"):
        """
        Initialize the ArcGIS exporter.
        
        Args:
            coordinate_system: Coordinate reference system (e.g., "EPSG:4326", "EPSG:3857")
        """
        self.coordinate_system = coordinate_system
        self.temp_files = []  # Track temporary files for cleanup
    
    def export_to_netcdf(self, voxel_grid: VoxelGrid, output_path: str, 
                        include_properties: bool = True) -> bool:
        """
        Export voxel grid to NetCDF format for 3D visualization in ArcGIS.
        
        Args:
            voxel_grid: VoxelGrid object to export
            output_path: Output NetCDF file path
            include_properties: Whether to include additional properties
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to import netCDF4 (may not be available in all environments)
            try:
                import netCDF4 as nc
                from netCDF4 import Dataset
            except ImportError:
                print("Warning: netCDF4 not available, using alternative format...")
                return self._export_to_ascii_layers(voxel_grid, output_path)
            
            # Create NetCDF file
            with Dataset(output_path, 'w', format='NETCDF4') as ncfile:
                # Create dimensions
                nx, ny, nz = voxel_grid.dimensions
                ncfile.createDimension('x', nx)
                ncfile.createDimension('y', ny)  
                ncfile.createDimension('z', nz)
                
                # Create coordinate variables
                x_var = ncfile.createVariable('x', 'f8', ('x',))
                y_var = ncfile.createVariable('y', 'f8', ('y',))
                z_var = ncfile.createVariable('z', 'f8', ('z',))
                
                # Set coordinate values
                x_var[:] = np.arange(nx) * voxel_grid.spacing[0] + voxel_grid.origin[0]
                y_var[:] = np.arange(ny) * voxel_grid.spacing[1] + voxel_grid.origin[1]
                z_var[:] = np.arange(nz) * voxel_grid.spacing[2] + voxel_grid.origin[2]
                
                # Add coordinate attributes
                x_var.units = 'meters'
                x_var.long_name = 'X coordinate'
                y_var.units = 'meters'
                y_var.long_name = 'Y coordinate'
                z_var.units = 'meters'
                z_var.long_name = 'Z coordinate (elevation)'
                
                # Create rock type variable (as integer codes)
                rock_codes, rock_types = self._encode_rock_types(voxel_grid.data)
                rock_var = ncfile.createVariable('rock_type', 'i4', ('x', 'y', 'z'))
                rock_var[:] = rock_codes
                rock_var.long_name = 'Rock Type Code'
                rock_var.rock_type_mapping = str(dict(enumerate(rock_types)))
                
                # Add property variables if requested
                if include_properties:
                    if 'porosity' in voxel_grid.properties:
                        por_var = ncfile.createVariable('porosity', 'f4', ('x', 'y', 'z'))
                        por_var[:] = voxel_grid.properties['porosity']
                        por_var.units = 'fraction'
                        por_var.long_name = 'Porosity'
                        por_var.valid_range = [0.0, 1.0]
                    
                    if 'permeability' in voxel_grid.properties:
                        perm_var = ncfile.createVariable('permeability', 'f4', ('x', 'y', 'z'))
                        perm_var[:] = voxel_grid.properties['permeability']
                        perm_var.units = 'm^2'
                        perm_var.long_name = 'Permeability'
                
                # Add global attributes
                ncfile.title = 'Geologic Voxel Model'
                ncfile.source = 'Converted from pblock wave format'
                ncfile.coordinate_system = self.coordinate_system
                ncfile.voxel_spacing_x = voxel_grid.spacing[0]
                ncfile.voxel_spacing_y = voxel_grid.spacing[1]
                ncfile.voxel_spacing_z = voxel_grid.spacing[2]
                
            print(f"Successfully exported to NetCDF: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting to NetCDF: {e}")
            return False
    
    def export_to_ascii_grids(self, voxel_grid: VoxelGrid, output_dir: str,
                             property_name: str = 'porosity', 
                             z_slices: Optional[List[int]] = None) -> bool:
        """
        Export 2D slices of the voxel grid as ASCII Grid files.
        
        Args:
            voxel_grid: VoxelGrid object to export
            output_dir: Directory to save ASCII grid files
            property_name: Property to export ('porosity', 'permeability', or 'rock_type')
            z_slices: Specific Z slice indices to export (default: all)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Get the data to export
            if property_name == 'rock_type':
                data, _ = self._encode_rock_types(voxel_grid.data)
            elif property_name in voxel_grid.properties:
                data = voxel_grid.properties[property_name]
            else:
                print(f"Property '{property_name}' not found in voxel grid")
                return False
            
            # Determine which slices to export
            if z_slices is None:
                z_slices = list(range(voxel_grid.dimensions[2]))
            
            nx, ny, nz = voxel_grid.dimensions
            
            for z_idx in z_slices:
                if z_idx >= nz:
                    continue
                    
                # Get the 2D slice (note: ASCII grid expects Y to increase northward)
                slice_data = data[:, :, z_idx].T  # Transpose for correct orientation
                slice_data = np.flipud(slice_data)  # Flip vertically for ASCII grid format
                
                # Calculate Z elevation for this slice
                z_elevation = voxel_grid.origin[2] + z_idx * voxel_grid.spacing[2]
                
                # Create ASCII grid file
                filename = f"{property_name}_z_{z_elevation:.1f}m.asc"
                filepath = os.path.join(output_dir, filename)
                
                # Write ASCII grid header and data
                with open(filepath, 'w') as f:
                    f.write(f"ncols {nx}\n")
                    f.write(f"nrows {ny}\n")
                    f.write(f"xllcorner {voxel_grid.origin[0]}\n")
                    f.write(f"yllcorner {voxel_grid.origin[1]}\n")
                    f.write(f"cellsize {voxel_grid.spacing[0]}\n")
                    f.write(f"NODATA_value -9999\n")
                    
                    # Write data rows
                    for row in slice_data:
                        f.write(" ".join([f"{val:.6f}" if not np.isnan(val) else "-9999" 
                                        for val in row]))
                        f.write("\n")
                
                print(f"Exported slice at Z={z_elevation:.1f}m to {filename}")
            
            return True
            
        except Exception as e:
            print(f"Error exporting ASCII grids: {e}")
            return False
    
    def export_to_point_cloud(self, voxel_grid: VoxelGrid, output_path: str,
                             sample_rate: float = 1.0, min_porosity: float = 0.0) -> bool:
        """
        Export voxel centers as a CSV point cloud for ArcGIS import.
        
        Args:
            voxel_grid: VoxelGrid object to export
            output_path: Output CSV file path
            sample_rate: Fraction of voxels to export (0.0-1.0)
            min_porosity: Minimum porosity threshold for export
            
        Returns:
            True if successful, False otherwise
        """
        try:
            nx, ny, nz = voxel_grid.dimensions
            
            # Prepare output lists
            points = []
            
            # Sample voxels
            for i in range(nx):
                for j in range(ny):
                    for k in range(nz):
                        # Skip based on sample rate
                        if sample_rate < 1.0 and np.random.random() > sample_rate:
                            continue
                        
                        # Skip low porosity voxels if threshold set
                        if 'porosity' in voxel_grid.properties:
                            porosity = voxel_grid.properties['porosity'][i, j, k]
                            if porosity < min_porosity:
                                continue
                        else:
                            porosity = 0.0
                        
                        # Calculate voxel center coordinates
                        x = voxel_grid.origin[0] + (i + 0.5) * voxel_grid.spacing[0]
                        y = voxel_grid.origin[1] + (j + 0.5) * voxel_grid.spacing[1]
                        z = voxel_grid.origin[2] + (k + 0.5) * voxel_grid.spacing[2]
                        
                        # Get other properties
                        rock_type = voxel_grid.data[i, j, k]
                        permeability = voxel_grid.properties.get('permeability', np.zeros_like(voxel_grid.data))[i, j, k]
                        
                        points.append({
                            'X': x,
                            'Y': y,
                            'Z': z,
                            'ROCK_TYPE': rock_type,
                            'POROSITY': porosity,
                            'PERMEABILITY': permeability
                        })
            
            # Write CSV file
            if points:
                with open(output_path, 'w') as f:
                    # Write header
                    headers = ['X', 'Y', 'Z', 'ROCK_TYPE', 'POROSITY', 'PERMEABILITY']
                    f.write(','.join(headers) + '\n')
                    
                    # Write data
                    for point in points:
                        row = [str(point[header]) for header in headers]
                        f.write(','.join(row) + '\n')
                
                print(f"Exported {len(points)} points to {output_path}")
                return True
            else:
                print("No points met the export criteria")
                return False
                
        except Exception as e:
            print(f"Error exporting point cloud: {e}")
            return False
    
    def _encode_rock_types(self, rock_type_array: np.ndarray) -> Tuple[np.ndarray, List[str]]:
        """
        Convert string rock types to integer codes for numerical processing.
        
        Returns:
            Tuple of (encoded_array, unique_rock_types)
        """
        # Get unique rock types
        unique_types = np.unique(rock_type_array.flatten())
        unique_types = [t for t in unique_types if t]  # Remove empty strings
        
        # Create mapping from type to code
        type_to_code = {rock_type: i for i, rock_type in enumerate(unique_types)}
        
        # Create encoded array
        encoded = np.zeros(rock_type_array.shape, dtype=np.int32)
        for i in range(rock_type_array.shape[0]):
            for j in range(rock_type_array.shape[1]):
                for k in range(rock_type_array.shape[2]):
                    rock_type = rock_type_array[i, j, k]
                    if rock_type in type_to_code:
                        encoded[i, j, k] = type_to_code[rock_type]
        
        return encoded, unique_types
    
    def _export_to_ascii_layers(self, voxel_grid: VoxelGrid, base_path: str) -> bool:
        """
        Fallback method to export as multiple ASCII grid layers when NetCDF is not available.
        """
        base_dir = os.path.splitext(base_path)[0] + "_layers"
        print(f"Exporting to ASCII grid layers in: {base_dir}")
        
        success = True
        success &= self.export_to_ascii_grids(voxel_grid, os.path.join(base_dir, "porosity"), 'porosity')
        success &= self.export_to_ascii_grids(voxel_grid, os.path.join(base_dir, "permeability"), 'permeability')
        success &= self.export_to_ascii_grids(voxel_grid, os.path.join(base_dir, "rock_type"), 'rock_type')
        
        return success
    
    def create_arcgis_project_file(self, output_dir: str, voxel_files: List[str]) -> bool:
        """
        Create an ArcGIS project file template that references the exported voxel data.
        
        Args:
            output_dir: Directory containing the exported files
            voxel_files: List of file paths to include in the project
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a simple text file with ArcGIS import instructions
            instructions_path = os.path.join(output_dir, "arcgis_import_instructions.txt")
            
            with open(instructions_path, 'w') as f:
                f.write("ArcGIS Import Instructions for Geologic Voxel Data\n")
                f.write("=" * 50 + "\n\n")
                
                f.write("Generated Files:\n")
                for filepath in voxel_files:
                    f.write(f"  - {os.path.basename(filepath)}\n")
                
                f.write("\nImport Steps:\n")
                f.write("1. For NetCDF files (.nc):\n")
                f.write("   - Use 'Make NetCDF Raster Layer' tool\n")
                f.write("   - Select appropriate variable (rock_type, porosity, permeability)\n")
                f.write("   - Set dimension values for 3D visualization\n\n")
                
                f.write("2. For ASCII Grid files (.asc):\n")
                f.write("   - Use 'ASCII to Raster' tool\n")
                f.write("   - Import each Z-slice as separate raster layer\n")
                f.write("   - Use 'Composite Bands' for 3D visualization\n\n")
                
                f.write("3. For Point Cloud CSV files:\n")
                f.write("   - Use 'XY Table To Point' tool\n")
                f.write("   - Set X, Y, Z coordinate fields\n")
                f.write("   - Enable Z-values for 3D visualization\n\n")
                
                f.write("4. Coordinate System:\n")
                f.write(f"   - Use coordinate system: {self.coordinate_system}\n")
                f.write("   - Ensure all layers use the same projection\n\n")
                
                f.write("5. Visualization Tips:\n")
                f.write("   - Use 3D Scene for better voxel visualization\n")
                f.write("   - Apply appropriate symbology based on rock types\n")
                f.write("   - Use transparency for better 3D viewing\n")
            
            print(f"Created import instructions: {instructions_path}")
            return True
            
        except Exception as e:
            print(f"Error creating project file: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Clean up any temporary files created during export."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        self.temp_files.clear()