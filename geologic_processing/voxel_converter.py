"""
Voxel Converter for Geologic Models

This module converts irregular geologic pblock models to regular voxel grids
suitable for use in ArcGIS and other 3D visualization tools.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from .wave_reader import GeologicBlock
import math


@dataclass
class VoxelGrid:
    """Represents a 3D voxel grid with geologic properties."""
    data: np.ndarray
    origin: Tuple[float, float, float]
    spacing: Tuple[float, float, float]
    dimensions: Tuple[int, int, int]
    properties: Dict[str, np.ndarray]  # Additional property arrays
    metadata: Dict


class VoxelConverter:
    """
    Converts geologic pblock models from wave format to regular voxel grids.
    
    The conversion process:
    1. Define a regular 3D grid that encompasses all blocks
    2. For each voxel, determine which blocks intersect it
    3. Assign voxel properties based on intersecting blocks (weighted by volume)
    """
    
    def __init__(self, voxel_size: Union[float, Tuple[float, float, float]] = 1.0):
        """
        Initialize the voxel converter.
        
        Args:
            voxel_size: Size of voxels. Can be a single value for cubic voxels
                       or tuple of (dx, dy, dz) for different spacing in each direction
        """
        if isinstance(voxel_size, (int, float)):
            self.voxel_size = (float(voxel_size), float(voxel_size), float(voxel_size))
        else:
            self.voxel_size = tuple(float(x) for x in voxel_size[:3])
    
    def convert_blocks_to_voxels(self, blocks: List[GeologicBlock], 
                               bounds: Optional[Dict[str, float]] = None,
                               buffer_factor: float = 0.1) -> VoxelGrid:
        """
        Convert a list of geologic blocks to a voxel grid.
        
        Args:
            blocks: List of GeologicBlock objects
            bounds: Optional custom bounds, otherwise calculated from blocks
            buffer_factor: Add buffer around data (fraction of data range)
            
        Returns:
            VoxelGrid object containing the converted data
        """
        if not blocks:
            raise ValueError("No blocks provided for conversion")
        
        # Calculate or use provided bounds
        if bounds is None:
            bounds = self._calculate_bounds(blocks, buffer_factor)
        
        # Calculate grid dimensions
        dimensions = self._calculate_dimensions(bounds)
        
        # Create origin point (lower-left-bottom corner)
        origin = (bounds['xmin'], bounds['ymin'], bounds['zmin'])
        
        # Initialize voxel arrays
        rock_type_grid = np.zeros(dimensions, dtype='<U20')  # String array for rock types
        porosity_grid = np.zeros(dimensions, dtype=np.float32)
        permeability_grid = np.zeros(dimensions, dtype=np.float32)
        block_count_grid = np.zeros(dimensions, dtype=np.float32)  # Track how many blocks influence each voxel
        
        print(f"Creating voxel grid with dimensions: {dimensions}")
        print(f"Voxel size: {self.voxel_size}")
        print(f"Processing {len(blocks)} blocks...")
        
        # Convert each block to voxels
        for i, block in enumerate(blocks):
            if i % 1000 == 0:
                print(f"Processing block {i}/{len(blocks)}")
            
            self._add_block_to_grid(
                block, origin, dimensions,
                rock_type_grid, porosity_grid, permeability_grid, block_count_grid
            )
        
        
        # Handle voxels with no block data (use nearest neighbor or default)
        self._fill_empty_voxels(rock_type_grid, porosity_grid, permeability_grid, block_count_grid)
        
        # Create the VoxelGrid object
        properties = {
            'porosity': porosity_grid,
            'permeability': permeability_grid,
            'block_count': block_count_grid
        }
        
        metadata = {
            'bounds': bounds,
            'original_block_count': len(blocks),
            'conversion_method': 'volume_weighted',
            'voxel_size': self.voxel_size
        }
        
        return VoxelGrid(
            data=rock_type_grid,
            origin=origin,
            spacing=self.voxel_size,
            dimensions=dimensions,
            properties=properties,
            metadata=metadata
        )
    
    def _calculate_bounds(self, blocks: List[GeologicBlock], buffer_factor: float) -> Dict[str, float]:
        """Calculate the spatial bounds of all blocks."""
        if not blocks:
            return {'xmin': 0, 'ymin': 0, 'zmin': 0, 'xmax': 1, 'ymax': 1, 'zmax': 1}
        
        # Find min/max coordinates considering block extents
        xmin = min(block.x - block.width/2 for block in blocks)
        xmax = max(block.x + block.width/2 for block in blocks)
        ymin = min(block.y - block.height/2 for block in blocks)
        ymax = max(block.y + block.height/2 for block in blocks)
        zmin = min(block.z - block.depth/2 for block in blocks)
        zmax = max(block.z + block.depth/2 for block in blocks)
        
        # Add buffer
        x_range = xmax - xmin
        y_range = ymax - ymin
        z_range = zmax - zmin
        
        x_buffer = x_range * buffer_factor
        y_buffer = y_range * buffer_factor
        z_buffer = z_range * buffer_factor
        
        return {
            'xmin': xmin - x_buffer,
            'xmax': xmax + x_buffer,
            'ymin': ymin - y_buffer,
            'ymax': ymax + y_buffer,
            'zmin': zmin - z_buffer,
            'zmax': zmax + z_buffer
        }
    
    def _calculate_dimensions(self, bounds: Dict[str, float]) -> Tuple[int, int, int]:
        """Calculate grid dimensions based on bounds and voxel size."""
        x_range = bounds['xmax'] - bounds['xmin']
        y_range = bounds['ymax'] - bounds['ymin']
        z_range = bounds['zmax'] - bounds['zmin']
        
        nx = max(1, int(math.ceil(x_range / self.voxel_size[0])))
        ny = max(1, int(math.ceil(y_range / self.voxel_size[1])))
        nz = max(1, int(math.ceil(z_range / self.voxel_size[2])))
        
        return (nx, ny, nz)
    
    def _add_block_to_grid(self, block: GeologicBlock, origin: Tuple[float, float, float],
                          dimensions: Tuple[int, int, int],
                          rock_grid: np.ndarray, porosity_grid: np.ndarray,
                          permeability_grid: np.ndarray, count_grid: np.ndarray) -> None:
        """Add a single block's contribution to the voxel grids."""
        
        # Calculate block bounds
        block_xmin = block.x - block.width / 2
        block_xmax = block.x + block.width / 2
        block_ymin = block.y - block.height / 2
        block_ymax = block.y + block.height / 2
        block_zmin = block.z - block.depth / 2
        block_zmax = block.z + block.depth / 2
        
        # Find voxel indices that overlap with this block
        i_start = max(0, int((block_xmin - origin[0]) / self.voxel_size[0]))
        i_end = min(dimensions[0], int((block_xmax - origin[0]) / self.voxel_size[0]) + 1)
        j_start = max(0, int((block_ymin - origin[1]) / self.voxel_size[1]))
        j_end = min(dimensions[1], int((block_ymax - origin[1]) / self.voxel_size[1]) + 1)
        k_start = max(0, int((block_zmin - origin[2]) / self.voxel_size[2]))
        k_end = min(dimensions[2], int((block_zmax - origin[2]) / self.voxel_size[2]) + 1)
        
        # Debug output for first few blocks (limited to reduce output)
        show_debug = False  # Disable debug for cleaner output
        
        if show_debug:
            print(f"    Block: {block.rock_type} at ({block.x}, {block.y}, {block.z}) size ({block.width}, {block.height}, {block.depth})")
        
        # Process each overlapping voxel
        voxels_processed = 0
        for i in range(i_start, i_end):
            for j in range(j_start, j_end):
                for k in range(k_start, k_end):
                    # Calculate voxel bounds
                    voxel_xmin = origin[0] + i * self.voxel_size[0]
                    voxel_xmax = voxel_xmin + self.voxel_size[0]
                    voxel_ymin = origin[1] + j * self.voxel_size[1]
                    voxel_ymax = voxel_ymin + self.voxel_size[1]
                    voxel_zmin = origin[2] + k * self.voxel_size[2]
                    voxel_zmax = voxel_zmin + self.voxel_size[2]
                    
                    # Calculate overlap volume
                    overlap_volume = self._calculate_overlap_volume(
                        block_xmin, block_xmax, block_ymin, block_ymax, block_zmin, block_zmax,
                        voxel_xmin, voxel_xmax, voxel_ymin, voxel_ymax, voxel_zmin, voxel_zmax
                    )
                    
                    voxels_processed += 1
                    
                    if overlap_volume > 0:
                        # Calculate volume fraction
                        voxel_volume = self.voxel_size[0] * self.voxel_size[1] * self.voxel_size[2]
                        weight = overlap_volume / voxel_volume
                        
                        # Update voxel properties (volume-weighted average)
                        current_count = count_grid[i, j, k]
                        total_weight = current_count + weight
                        
                        if current_count == 0:
                            # First block to influence this voxel
                            rock_grid[i, j, k] = block.rock_type
                            porosity_grid[i, j, k] = block.porosity * weight
                            permeability_grid[i, j, k] = block.permeability * weight
                        else:
                            # Weighted average with existing values
                            porosity_grid[i, j, k] = (
                                porosity_grid[i, j, k] * current_count + block.porosity * weight
                            ) / total_weight
                            permeability_grid[i, j, k] = (
                                permeability_grid[i, j, k] * current_count + block.permeability * weight
                            ) / total_weight
                            
                            # For rock type, use the block with highest influence
                            if weight > current_count:
                                rock_grid[i, j, k] = block.rock_type
                        
                        count_grid[i, j, k] = total_weight
        
        # Debug summary for first few blocks
        if show_debug:
            assigned_voxels = np.sum(count_grid > 0)
            print(f"    -> {assigned_voxels} voxels assigned data from this block")
    
    def _calculate_overlap_volume(self, b_xmin: float, b_xmax: float, b_ymin: float, b_ymax: float,
                                 b_zmin: float, b_zmax: float, v_xmin: float, v_xmax: float,
                                 v_ymin: float, v_ymax: float, v_zmin: float, v_zmax: float) -> float:
        """Calculate the overlap volume between a block and a voxel."""
        
        # Find intersection bounds
        x_overlap = max(0, min(b_xmax, v_xmax) - max(b_xmin, v_xmin))
        y_overlap = max(0, min(b_ymax, v_ymax) - max(b_ymin, v_ymin))
        z_overlap = max(0, min(b_zmax, v_zmax) - max(b_zmin, v_zmin))
        
        return x_overlap * y_overlap * z_overlap
    
    def _fill_empty_voxels(self, rock_grid: np.ndarray, porosity_grid: np.ndarray,
                          permeability_grid: np.ndarray, count_grid: np.ndarray) -> None:
        """Fill voxels that have no block data using nearest neighbor interpolation."""
        
        empty_mask = count_grid <= 0.0  # Use <= 0.0 for floating point comparison
        empty_count = np.sum(empty_mask)
        
        if empty_count == 0:
            print("All voxels have data - no empty voxels to fill!")
            return  # No empty voxels
        
        print(f"Filling {empty_count} empty voxels...")
        
        # For empty voxels, use default values or nearest neighbor
        rock_grid[empty_mask] = 'unknown'
        porosity_grid[empty_mask] = 0.0
        permeability_grid[empty_mask] = 0.0
        
        # Could implement nearest neighbor interpolation here for better results
        # For now, using simple default values
    
    def export_to_numpy(self, voxel_grid: VoxelGrid, filename_prefix: str) -> None:
        """Export voxel grid to NumPy .npz format."""
        np.savez_compressed(
            f"{filename_prefix}_voxels.npz",
            rock_types=voxel_grid.data,
            porosity=voxel_grid.properties['porosity'],
            permeability=voxel_grid.properties['permeability'],
            origin=voxel_grid.origin,
            spacing=voxel_grid.spacing,
            dimensions=voxel_grid.dimensions,
            metadata=voxel_grid.metadata
        )
        print(f"Voxel grid exported to {filename_prefix}_voxels.npz")