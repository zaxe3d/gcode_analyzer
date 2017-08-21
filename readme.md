# GCode Analyzer

## Install

`pip install gcode_analyzer`

## CLI Usage

`python -m gcode_analyzer.analyze [--z-acceleration Z_ACCELERATION] [--extruder-acceleration EXTRUDER_ACCELERATION] GCODE_FILE_PATH`

### Example:

`python -m gcode_analyzer.analyze ~/marvin.gcode`

`python -m --extruder-acceleration 2000 gcode_analyzer.analyze ~/marvin.gcode`

## API

     from gcode_analyzer import Analyzer
     analyzer = Analyzer("/Users/cangelis/example.gcode")
     print analyzer.get_time() # in seconds
     print analyzer.get_formatted_time()
     print analyzer.get_filament_usage() # in mm
