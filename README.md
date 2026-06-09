# Feature To Polygon — QGIS Plugin

[![QGIS](https://img.shields.io/badge/QGIS-3.16%2B-green.svg)](https://qgis.org)
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![Version](https://img.shields.io/badge/version-1.0.0-orange.svg)](https://github.com/khalilgh33/feature-to-polygon/releases)

A QGIS Processing plugin that generates polygon features from all enclosed areas formed by combining **polygon**, **line**, and **point** layers — equivalent to the [ArcGIS Pro "Feature to Polygon" tool](https://doc.esri.com/en/arcgis-pro/latest/tool-reference/data-management/feature-to-polygon.html).

---

## What It Does

Given any combination of input layers, the plugin:

1. Extracts **boundaries** from polygon layers
2. Uses **line** layers directly as dividing edges
3. **Buffers point** layers by a user-defined radius (optional)
4. Merges and **nodes** all geometries (splits at every intersection)
5. **Polygonizes** all enclosed areas
6. Optionally **clips** the result to the original polygon extent
7. Outputs a new polygon layer with `ftp_id` and `area_m2` attributes

### Example

| Input | Output |
|-------|--------|
| 1 polygon + 1 line crossing it | 2 polygons |
| 1 polygon + 2 lines forming a cross | 4 polygons |
| 1 polygon + 1 line + 1 buffered point | 4 polygons |

---

## Requirements

- QGIS 3.16 or higher
- Python package: **Shapely >= 1.7**

### Install Shapely

**Windows (OSGeo4W Shell):**
```bash
pip install shapely
```

**Linux / macOS:**
```bash
pip3 install shapely
```

---

## Installation

### Option 1 — QGIS Plugin Repository (recommended)

1. Open QGIS
2. Go to **Plugins → Manage and Install Plugins**
3. Search for **"Feature To Polygon"**
4. Click **Install**

### Option 2 — Install from ZIP

1. Download the latest release ZIP from the [Releases page](https://github.com/khalilgh33/feature-to-polygon/releases)
2. Open QGIS
3. Go to **Plugins → Manage and Install Plugins → Install from ZIP**
4. Select the downloaded ZIP file
5. Click **Install Plugin**

### Option 3 — Manual installation

1. Clone or download this repository
2. Copy the `feature_to_polygon/` folder to your QGIS plugins directory:
   - **Windows:** `C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **macOS:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS
4. Enable the plugin under **Plugins → Manage and Install Plugins**

---

## Usage

1. Open the **Processing Toolbox** (`Ctrl+Alt+T`)
2. Navigate to **Vector Geoprocessing → Feature To Polygon**
3. Set the parameters:

| Parameter | Description | Required |
|-----------|-------------|----------|
| Input Layers | Any combination of polygon, line, point layers | Yes |
| Point buffer radius (map units) | Radius applied to point features only | Optional |
| Clip output to input polygon extent | Removes areas outside the input polygons | Yes |
| Output Polygons | Output layer path | Yes |

4. Click **Run**

---

## Important Notes

- **Lines must fully cross** the polygon boundary from one side to the other to form a closed region. A line that stops inside the polygon without reaching the other side will not produce a split.
- **Point buffer radius** is in the map units of your project CRS. Use a projected CRS (e.g. EPSG:5514 for Czech Republic) to ensure radius is in meters.
- All input layers are automatically **reprojected** to the CRS of the first layer in the list.
- If no point layers are present, the buffer radius parameter is ignored.

---

## How It Works (Technical)

The core algorithm uses:

- `shapely.ops.unary_union` — merges all line geometries and performs automatic **noding** (splitting lines at every intersection point). This is the critical step that ensures all enclosed regions are properly detected.
- `shapely.ops.polygonize` — finds all enclosed planar regions from the noded line network.
- `shapely.geometry.Polygon.intersection` — clips results to the input polygon union.

**Reference:**
- Gillies, S. et al. (2007–). *Shapely: manipulation and analysis of geometric objects*. https://github.com/shapely/shapely
- QGIS Development Team (2024). *QGIS Geographic Information System*. Open Source Geospatial Foundation. https://qgis.org

---

## Plugin Structure

```
feature_to_polygon/
├── __init__.py          # Plugin entry point
├── plugin.py            # Plugin class, registers provider
├── provider.py          # Processing provider
├── algorithm.py         # Core algorithm (Feature to Polygon)
├── metadata.txt         # QGIS plugin metadata
├── LICENSE              # GNU GPL v2
├── README.md            # This file
└── icons/
    └── icon.png         # Plugin icon
```

---

## Contributing

Contributions are welcome. Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

Please follow [PEP8](https://peps.python.org/pep-0008/) coding style and test with QGIS 3.16+.

---

## Known Limitations

- Very large or complex datasets may be slow due to `unary_union` noding. For datasets with millions of vertices, consider simplifying geometries first.
- Extremely thin or near-degenerate polygons may appear in output if input lines nearly touch without intersecting. Use **Fix Geometries** on the output if needed.

---

## Changelog

### 1.0.0 (2024)
- Initial release
- Support for polygon, line, and point input layers
- Optional point buffering with user-defined radius
- Automatic CRS reprojection
- Clip to polygon extent option

---

## Author

**Khalil Valizadeh**
PhD Candidate — Department of Applied Geoinformatics and Cartography
Faculty of Science, Charles University, Prague

- Email: khalil.gh3@gmail.com
- GitHub: [@khalilgh33](https://github.com/khalilgh33)

---

## License

This plugin is free software: you can redistribute it and/or modify it under the terms of the **GNU General Public License version 2** as published by the Free Software Foundation.

See [LICENSE](LICENSE) for full details.
