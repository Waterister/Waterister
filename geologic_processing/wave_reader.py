"""
Wave Format Reader for Geologic Pblock Models

This module handles reading and parsing geologic pblock models stored in wave format.
"""

import numpy as np
import struct
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class GeologicBlock:
    """Represents a single geologic block with properties and spatial coordinates."""
    x: float
    y: float
    z: float
    width: float
    height: float
    depth: float
    rock_type: str
    porosity: float
    permeability: float
    properties: Dict[str, float]


class WaveReader:
    """
    Reader for geologic pblock models in wave format.
    
    Wave format typically stores 3D geologic data as irregular blocks
    with varying sizes and properties.
    """
    
    def __init__(self, file_path: str):
        """
        Initialize the wave reader.
        
        Args:
            file_path: Path to the wave format file
        """
        self.file_path = file_path
        self.blocks: List[GeologicBlock] = []
        self.metadata: Dict = {}
        
    def read_wave_file(self) -> bool:
        """
        Read and parse the wave format file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.file_path, 'rb') as f:
                # Read header information
                self._read_header(f)
                
                # Read block data
                self._read_blocks(f)
                
            return True
            
        except Exception as e:
            print(f"Error reading wave file: {e}")
            return False
    
    def _read_header(self, file_handle) -> None:
        """Read the wave file header containing metadata."""
        # Wave format header typically contains:
        # - File version
        # - Coordinate system information  
        # - Bounding box
        # - Number of blocks
        
        # Read file signature (first 4 bytes)
        signature = file_handle.read(4)
        if signature != b'WAVE':
            # Try text-based wave format
            file_handle.seek(0)
            self._read_text_header(file_handle)
        else:
            self._read_binary_header(file_handle)
    
    def _read_binary_header(self, file_handle) -> None:
        """Read binary wave format header."""
        # Version (4 bytes)
        version = struct.unpack('I', file_handle.read(4))[0]
        self.metadata['version'] = version
        
        # Bounding box (6 doubles: xmin, ymin, zmin, xmax, ymax, zmax)
        bbox = struct.unpack('6d', file_handle.read(48))
        self.metadata['bounds'] = {
            'xmin': bbox[0], 'ymin': bbox[1], 'zmin': bbox[2],
            'xmax': bbox[3], 'ymax': bbox[4], 'zmax': bbox[5]
        }
        
        # Number of blocks (4 bytes)
        num_blocks = struct.unpack('I', file_handle.read(4))[0]
        self.metadata['num_blocks'] = num_blocks
    
    def _read_text_header(self, file_handle) -> None:
        """Read text-based wave format header."""
        file_handle.seek(0)
        first_line = file_handle.readline().decode('utf-8').strip()
        
        if first_line.startswith('# WAVE_FORMAT'):
            # Parse text header
            while True:
                line = file_handle.readline().decode('utf-8').strip()
                if not line.startswith('#'):
                    file_handle.seek(file_handle.tell() - len(line.encode('utf-8')) - 1)
                    break
                    
                if 'BOUNDS:' in line:
                    bounds = [float(x) for x in line.split(':')[1].split()]
                    self.metadata['bounds'] = {
                        'xmin': bounds[0], 'ymin': bounds[1], 'zmin': bounds[2],
                        'xmax': bounds[3], 'ymax': bounds[4], 'zmax': bounds[5]
                    }
                elif 'BLOCKS:' in line:
                    self.metadata['num_blocks'] = int(line.split(':')[1].strip())
    
    def _read_blocks(self, file_handle) -> None:
        """Read individual geologic blocks from the file."""
        num_blocks = self.metadata.get('num_blocks', 0)
        
        # Check if we're in text mode based on first line
        current_pos = file_handle.tell()
        test_line = file_handle.readline()
        file_handle.seek(current_pos)
        
        is_text_format = test_line.decode('utf-8', errors='ignore').strip().replace('#', '').strip() != ''
        
        if is_text_format:
            # Read text format
            for line in file_handle:
                line = line.decode('utf-8').strip()
                if not line or line.startswith('#'):
                    continue
                    
                block = self._parse_text_line(line)
                if block:
                    self.blocks.append(block)
        else:
            # Read binary format
            for i in range(num_blocks):
                block = self._read_single_block(file_handle)
                if block:
                    self.blocks.append(block)
    
    def _parse_text_line(self, line: str) -> Optional[GeologicBlock]:
        """Parse a single text line into a GeologicBlock."""
        parts = line.split()
        if len(parts) < 8:
            return None
            
        try:
            return GeologicBlock(
                x=float(parts[0]),
                y=float(parts[1]),
                z=float(parts[2]),
                width=float(parts[3]),
                height=float(parts[4]),
                depth=float(parts[5]),
                rock_type=parts[6],
                porosity=float(parts[7]),
                permeability=float(parts[8]) if len(parts) > 8 else 0.0,
                properties={}
            )
        except (ValueError, IndexError):
            return None
    
    def _read_single_block(self, file_handle) -> Optional[GeologicBlock]:
        """Read a single geologic block from the file."""
        try:
            # Try binary format first
            data = file_handle.read(64)  # Assume fixed block size for now
            if len(data) < 64:
                return None
                
            # Unpack block data (adjust format based on actual wave format spec)
            unpacked = struct.unpack('8d', data)
            
            return GeologicBlock(
                x=unpacked[0],
                y=unpacked[1], 
                z=unpacked[2],
                width=unpacked[3],
                height=unpacked[4],
                depth=unpacked[5],
                rock_type=f"type_{int(unpacked[6])}",
                porosity=unpacked[7],
                permeability=0.0,  # Will be in properties
                properties={}
            )
            
        except:
            # Fallback to text parsing
            return self._read_text_block(file_handle)
    
    def _read_text_block(self, file_handle) -> Optional[GeologicBlock]:
        """Read a block from text format."""
        line = file_handle.readline().decode('utf-8').strip()
        if not line:
            return None
            
        parts = line.split()
        if len(parts) < 8:
            return None
            
        try:
            return GeologicBlock(
                x=float(parts[0]),
                y=float(parts[1]),
                z=float(parts[2]),
                width=float(parts[3]),
                height=float(parts[4]),
                depth=float(parts[5]),
                rock_type=parts[6],
                porosity=float(parts[7]),
                permeability=float(parts[8]) if len(parts) > 8 else 0.0,
                properties={}
            )
        except ValueError:
            return None
    
    def get_bounds(self) -> Dict[str, float]:
        """Get the spatial bounds of the model."""
        return self.metadata.get('bounds', {})
    
    def get_block_count(self) -> int:
        """Get the total number of blocks."""
        return len(self.blocks)
    
    def get_blocks(self) -> List[GeologicBlock]:
        """Get all geologic blocks."""
        return self.blocks