# SpringFull - FreeCAD Compression Spring Macro

Version 1.4.2

## Description

SpringFull is a comprehensive FreeCAD macro for designing compression springs according to EN 13906-1 standards. It provides an integrated solution combining spring calculations, 3D geometry generation, and parameter management within FreeCAD.

## Features

- Spring calculation according to EN 13906-1
- Detailed 3D helix geometry or simplified tube representation
- All data stored in FreeCAD Body properties (no external files needed)
- Built-in material database with stress limits
- Multiple representation modes: free, loaded, solid height, custom
- LCS (Local Coordinate System) for assembly constraints
- Multi-language support (English, French)

## Installation

1. Copy the `SpringFull` folder to your FreeCAD Macro directory:
   - Windows: `%APPDATA%\FreeCAD\Macro\`
   - Linux: `~/.local/share/FreeCAD/Macro/`
   - macOS: `~/Library/Application Support/FreeCAD/Macro/`

2. Copy `RunSpringFull.FCMacro` to the same Macro directory

3. Run the macro from FreeCAD: Menu > Macro > Macros... > RunSpringFull

## File Structure

```
SpringFull/
├── SpringFull.FCMacro          # Main macro
├── __init__.py                 # Package init
├── SpringFullDataModule.py     # Data management
├── SpringFullDialogsModule.py  # User dialogs
├── SpringFullModule.py         # 3D geometry generation
├── SpringFullHelixModule.py    # Helix creation
├── SpringFullCalculatorModule.py # Spring calculator
├── SpringFullI18nModule.py     # Internationalization
├── Translate_on.txt            # Language control file
├── Translate_off.txt           # Language control file
├── locales/
│   ├── en.json                 # English translations
│   ├── fr.json                 # French translations
│   ├── materials_en.json       # Material names (English)
│   └── materials_fr.json       # Material names (French)
├── templates/
│   └── default.json            # Default spring parameters
└── utils/
    ├── spring_materials_database.json
    ├── wire_diameters_database.json
    └── end_types_database.json
```

## Version History

### v1.4.2 (2025-02-05)
- **Bug fix**: New spring without modifications now correctly builds geometry
- Added `isBodyEmpty()` function to detect Bodies without geometry
- Initial spring construction now works even without changing template parameters

### v1.4.1
- Language selection controlled by file timestamps
- Automatic language detection from FreeCAD/system settings

### v1.4.0
- Visible properties grouped in "Spring Params" (read-only)
- Added calculated properties: internalDiameter (Di), externalDiameter (De)
- Internal properties hidden in "Internal" group

## Usage

1. Run the macro in FreeCAD
2. Select an existing spring or create a new one
3. Use the Calculator button to modify spring parameters
4. Choose representation type (free, loaded, solid, custom)
5. Choose display mode (detailed helix or simplified tube)
6. Click OK to generate the 3D geometry

## License

GPL License

## Author

Yves Guillou
