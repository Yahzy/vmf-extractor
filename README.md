# VMF Content Extractor

Content extractor for VMF (Valve Map Format) files from Source Engine with a simple and intuitive graphical interface.

## Features

- 🎯 **Graphical Interface**: Drag & drop for instant extraction
- 📁 **Path Management**: Automatic configuration of content sources
- 🔍 **Complete Extraction**: Materials (.vmt/.vtf), models (.mdl/.vvd/.vtx/.phy) and sounds (.wav/.mp3/.ogg)
- ⚡ **Automatic**: Saved configuration, no need to reconfigure
- 📊 **Real-time Tracking**: Live progress and statistics

## Installation

No external dependencies. Uses only standard Python + tkinter.

```bash
# Download files to a folder
# Double-click VMF_Extractor.bat (Windows) 
# Or run: python main.py
```

## Usage

### 🚀 Quick Method
1. **Double-click** `VMF_Extractor.bat` (Windows)
2. **Or run**: `python main.py`

### 📋 Initial Setup
1. **Add your content paths**:
   - `content`: Source game folder (`C:/Steam/.../cstrike`)
   - `addons`: Addons folder (`C:/Steam/.../garrysmod/addons`)

2. **Drag & drop** your .vmf file
3. **That's it!** Extraction starts automatically

### 🎯 Typical Workflow
```
1. First launch → Configure paths
2. Drag & drop VMF → Automatic extraction  
3. Result in extracted_[map_name]/
```



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
├── content_paths.json   # Configuration (auto-created)
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

## Supported Entity Types

### Materials
- World brushes
- Entity brushes  
- Custom textures

### Models
- `prop_static`, `prop_dynamic`, `prop_dynamic_override`
- `prop_physics`, `prop_physics_multiplayer`
- `prop_ragdoll`, `cycler`
- NPC and weapon entities

### Sounds
- `ambient_generic`, `env_soundscape`
- `func_button`, `func_door`, `func_breakable`
- Various entity sounds

## Automatic Configuration

On first launch, a `content_paths.json` file is created with default paths. You can modify it according to your needs:

```json
{
  "paths": [
    {
      "path": "C:/Steam/steamapps/common/Counter-Strike Source/cstrike",
      "type": "content"
    },
    {
      "path": "C:/Steam/steamapps/common/Half-Life 2/hl2",
      "type": "content"
    }
  ]
}
```

## Limitations

1. **Model parsing**: Material extraction from .mdl files uses sophisticated binary parsing with strict validation to prevent false positives.

2. **Audio formats**: Supports .wav, .mp3, .ogg but not proprietary Source formats.

3. **Dependencies**: Does not automatically handle dependencies between materials or inclusions.

## Troubleshooting

### "No materials/models/sounds found"
- Check that game directories are correct
- Ensure the VMF file is valid
- Verify read permissions on folders

### "Parsing error"
- The VMF file may be corrupted
- Try opening the file in Hammer Editor to verify

### "Missing files"
- Some assets may be in unspecified directories
- Add more directories to your configuration
- Check the missing.txt report to see what's missing

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

## License

[Specify your license here]

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest improvements
- Submit pull requests
- Improve documentation