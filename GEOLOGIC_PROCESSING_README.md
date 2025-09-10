# Geologic Pblock Wave-to-Voxel Converter

A Python tool for converting geologic pblock models from wave format to voxel format compatible with ArcGIS workflows.

## Overview

This tool addresses the need to convert irregular geologic pblock models (stored in wave format) into regular voxel grids that can be easily imported and visualized in ArcGIS. The conversion process maintains geologic properties while creating a structured 3D grid suitable for spatial analysis and visualization.

## Features

- **Wave Format Support**: Reads geologic pblock models in both binary and text-based wave formats
- **Voxel Conversion**: Converts irregular blocks to regular 3D voxel grids with customizable resolution
- **Multiple Export Formats**:
  - NetCDF (.nc) for 3D visualization in ArcGIS
  - ASCII Grid (.asc) for 2D slice analysis
  - CSV Point Cloud for 3D point analysis
- **Property Preservation**: Maintains rock type, porosity, permeability, and other geologic properties
- **ArcGIS Integration**: Includes detailed import instructions for ArcGIS workflows

## Installation

1. Clone or download this repository
2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Create an Example File
```bash
python convert_wave_to_voxel.py --create-example
```

### 2. Convert to Voxels
```bash
python convert_wave_to_voxel.py example_geologic_model.wave
```

### 3. Import to ArcGIS
- Open ArcGIS Pro or ArcMap
- Follow the instructions in `output/arcgis_import_instructions.txt`
- Use the exported files for 3D visualization and analysis

## Usage

### Basic Conversion
```bash
python convert_wave_to_voxel.py input_file.wave
```

### Advanced Options
```bash
python convert_wave_to_voxel.py input_file.wave \
    --output ./my_output \
    --voxel-size 5.0 \
    --format netcdf \
    --coordinate-system EPSG:3857
```

### Available Options
- `--output`: Output directory (default: ./output)
- `--voxel-size`: Voxel size in model units (default: 10.0)
- `--format`: Output format - netcdf, ascii, csv, or all (default: all)
- `--sample-rate`: Sampling rate for point cloud (0.0-1.0, default: 1.0)
- `--coordinate-system`: Coordinate reference system (default: EPSG:4326)

## Wave Format Specification

The tool supports both binary and text-based wave formats:

### Text Format
```
# WAVE_FORMAT v1.0
# BOUNDS: xmin ymin zmin xmax ymax zmax
# BLOCKS: count
# Format: X Y Z WIDTH HEIGHT DEPTH ROCK_TYPE POROSITY PERMEABILITY
100.0 200.0 50.0 20.0 20.0 10.0 sandstone 0.15 1.5e-12
150.0 220.0 55.0 25.0 25.0 12.0 limestone 0.08 2.3e-14
...
```

### Binary Format
- 4-byte signature: 'WAVE'
- 4-byte version number
- 48-byte bounding box (6 doubles)
- 4-byte block count
- Block data (variable format)

## Output Formats

### NetCDF (.nc)
- 3D array format with X, Y, Z dimensions
- Multiple variables: rock_type, porosity, permeability
- Suitable for 3D visualization in ArcGIS
- Compatible with ArcGIS "Make NetCDF Raster Layer" tool

### ASCII Grid (.asc)
- 2D raster format for each Z-slice
- Standard ESRI ASCII Grid format
- One file per elevation slice
- Compatible with ArcGIS "ASCII to Raster" tool

### CSV Point Cloud
- Point-based format with X, Y, Z coordinates
- Includes all geologic properties as attributes
- Suitable for 3D point analysis
- Compatible with ArcGIS "XY Table To Point" tool

## ArcGIS Integration

### Importing NetCDF Files
1. Use "Make NetCDF Raster Layer" tool
2. Select variable (rock_type, porosity, or permeability)
3. Set appropriate dimension values
4. Configure 3D visualization in Scene view

### Importing ASCII Grids
1. Use "ASCII to Raster" tool for each slice
2. Use "Composite Bands" for 3D visualization
3. Apply appropriate symbology for rock types

### Importing Point Clouds
1. Use "XY Table To Point" tool
2. Set X, Y, Z coordinate fields
3. Enable Z-values for 3D display
4. Apply symbology based on rock type or properties

## Technical Details

### Voxel Conversion Algorithm
1. **Spatial Analysis**: Determine bounding box of all geologic blocks
2. **Grid Generation**: Create regular 3D grid with specified voxel size
3. **Intersection Calculation**: For each voxel, find intersecting geologic blocks
4. **Property Assignment**: Use volume-weighted averaging for properties
5. **Gap Filling**: Handle empty voxels using nearest neighbor or default values

### Coordinate Systems
- Default: WGS84 (EPSG:4326)
- Supports any EPSG coordinate reference system
- Maintains spatial reference through conversion process
- Exports coordinate system information in output files

## Applications

### Hydrogeological Modeling
- Convert subsurface geologic models for groundwater flow analysis
- Maintain permeability and porosity distributions
- Support heterogeneous aquifer characterization

### Resource Exploration
- Process geologic models from mining or petroleum exploration
- Visualize ore body distributions
- Analyze geological structure continuity

### Environmental Analysis
- Model contaminant transport pathways
- Assess geological barrier effectiveness
- Support environmental impact studies

## Troubleshooting

### Common Issues

**"netCDF4 not available" Warning**
- Install netCDF4: `pip install netCDF4`
- Or use alternative formats (ASCII, CSV)

**Large Memory Usage**
- Increase voxel size to reduce grid resolution
- Use sampling for point cloud exports
- Process subsets of large models

**Coordinate System Issues**
- Verify input data coordinate system
- Use appropriate EPSG codes
- Check spatial reference in ArcGIS

### Performance Tips
- Use appropriate voxel size for your analysis needs
- Consider model complexity vs. resolution trade-offs
- Use point cloud format for very large models
- Process models in sections for memory efficiency

## Contributing

This tool is part of ongoing hydrogeological data analysis work. Contributions and improvements are welcome, particularly:

- Additional wave format parsers
- Enhanced interpolation methods  
- Performance optimizations
- ArcGIS toolbox integration

## Contact

For questions or collaboration on water resources applications:
- Email: kylian.robinson@env.nm.gov
- GitHub: @Waterister

## License

This project is developed for water resources research and analysis applications.