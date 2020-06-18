from gcode_analyzer import Analyzer
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="GCode Analyzer")
    parser.add_argument('path', type=str)
    parser.add_argument('--z-acceleration', dest="z_acceleration", type=float)
    parser.add_argument('--extruder-acceleration', dest="extruder_acceleration", type=float)
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        analyzer = Analyzer(args.path, z_acceleration=args.z_acceleration,
                            extruder_acceleration=args.extruder_acceleration)
        print("Estimated Print Time: %s" % analyzer.get_formatted_time())
        print("Filament Usage: %.2f meters" % (analyzer.get_filament_usage() / 1000))
    except IOError:
        print("Error: %s does not exist" % args.path)


if __name__ == '__main__':
    main()
