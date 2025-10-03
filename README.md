# VMF Content Extractor

Content extractor for VMF (Valve Map Format) files from Source Engine with a simple and intuitive graphical interface.

## Features

- 🎯 **Graphical Interface**: Drag & drop for instant extraction
- 📁 **Path Management**: Automatic configuration of content sources
- 🔍 **Complete Extraction**: Materials (.vmt/.vtf), models (.mdl/.vvd/.vtx/.phy) and sounds (.wav/.mp3/.ogg)
- ⚡ **Automatic**: Saved configuration, no need to reconfigure
- 📊 **Real-time Tracking**: Live progress and statistics

## Usage

### 🚀 Quick Method
1. **Launch with vscode** `gui.py` (Windows)
2. **Or run**: `python gui.py`

### 📋 Initial Setup
1. **Add your content paths**:
   - `content`: Source game folder (`C:/Steam/.../cstrike`)
   - `addons`: Addons folder (`C:/Steam/.../garrysmod/addons`)

2. **Drag & drop** your .vmf file
3. **That's it!** Extraction starts automatically

## File Structure

```
vmfextractor/
├── main.py              # Main launcher 
├── gui.py               # Graphical interface
├── parser_vmf.py        # VMF parser
├── parser_mdl.py        # MDL parser
├── extract_mat.py       # Material extractor
├── extract_mdl.py       # Model extractor  
├── extract_snd.py       # Sound extractor
└── README.md           # Documentation
```

## Source Engine Directory Examples

### Counter-Strike: Source
```
C:/Steam/steamapps/common/Counter-Strike Source/cstrike
```

### Half-Life 2
```
C:/Steam/steamapps/common/Half-Life 2/hl2
```

### Team Fortress 2
```
C:/Steam/steamapps/common/Team Fortress 2/tf
```

### Garry's Mod
```
C:/Steam/steamapps/common/GarrysMod/garrysmod
```

## Content Path Types

### "content" Type 
Direct path to a Source Engine game folder containing `materials/`, `models/`, `sound/` directories.

**Example:**
```
C:/Steam/steamapps/common/Counter-Strike Source/cstrike
```

### "addons" Type
Path to a folder containing multiple addons, each with its own content structure.

**Example:**
```
C:/Steam/steamapps/common/GarrysMod/garrysmod/addons
```
Contains subdirectories like:
- `addon1/materials/`
- `addon1/models/`  
- `addon2/materials/`
- etc.

## Output Structure

```
extracted_[mapname]/
├── materials/           # .vmt and .vtf files
│   ├── models/
│   ├── maps/
│   └── ...
├── models/             # .mdl, .vvd, .vtx, .phy files
│   ├── props/
│   ├── player/
│   └── ...
├── sound/              # .wav, .mp3, .ogg files
│   ├── ambient/
│   ├── weapons/
│   └── ...
└── missing.txt         # Report of missing files (if any)
```

## Common Issues

### Output Directory Already Exists
If an `extracted_[mapname]` folder already exists, the program will display an error message. Delete or rename the existing folder.

### Paths Not Found
Check that the paths in `content_paths.json` are correct and that the directories exist.

### Insufficient Permissions
Make sure you have write permissions in the working directory.

## Development

### Code Structure

1. **parser_vmf**: Parses VMF hierarchical structure
2. **parser_mdl**: Advanced binary parser for MDL materials
3. **MaterialExtractor**: Handles material and texture extraction
4. **ModelExtractor**: Handles model extraction and their materials
5. **SoundExtractor**: Handles audio file extraction
6. **gui.py**: User interface and orchestration

### Adding a New Content Type

1. Create a new `extract_xxx.py` module
2. Implement the `XxxExtractor` class
3. Add extraction to `gui.py`
4. Update documentation

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest improvements
- Submit pull requests
- Improve documentation
