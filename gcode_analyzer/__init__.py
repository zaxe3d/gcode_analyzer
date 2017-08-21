import math
import datetime


class GCode(object):
    def __init__(self, line):
        self.__line = line
        self.__params = {}
        self.__process()

    def __process(self):
        for parameter in self.__line.split(";")[0].split():
            try:
                self.__params[parameter[0]] = parameter[1:]
            except IndexError:
                pass

    def get(self, parameter, return_type=None, default=None):
        try:
            if return_type is None:
                return self.__params[parameter]
            else:
                return return_type(self.__params[parameter])
        except KeyError:
            return default

    def __str__(self):
        return self.__line


class Analyzer(object):

    def __init__(self, file_path, extruder_acceleration=None, z_acceleration=None):
        super(Analyzer, self).__init__()
        self.__file_path = file_path
        self.__pos = {"X": 0, "Y": 0, "Z": 0, "E": 0}
        self.__relative = False
        self.__relative_extrusion = False
        self.__gcode = None
        self.__time = 0.0
        self.__acceleration = 1000
        self.__extruder_acceleration = extruder_acceleration or 2000
        self.__z_acceleration = z_acceleration or 250
        self.__velocity = 5000
        self.__process()

    def get_time(self):
        return self.__time

    def get_filament_usage(self):
        return self.__pos["E"]

    def get_formatted_time(self):
        return datetime.timedelta(seconds=self.__time)

    def __process(self):
        with open(self.__file_path, "r") as fp:
            while True:
                line = fp.readline()
                if not line:
                    break
                self.__gcode = GCode(line)
                self.__process_gcode()

    def __process_gcode(self):
        self.__update_velocity()
        self.__calculate_time()
        self.__update_move_type()
        self.__update_pos()
        self.__update_acceleration()
        self.__handle_g92()
        self.__home()

    def __update_velocity(self):
        f = self.__gcode.get("F", float, None)
        if f is not None:
            self.__velocity = f / float(60.0)

    def __is_move(self):
        return self.__gcode.get("G", int) == 1 or self.__gcode.get("G", int) == 0

    def __update_move_type(self):
        if self.__gcode.get("G", int) == 91:
            self.__relative = True
            self.__relative_extrusion = True
        elif self.__gcode.get("G", int) == 90:
            self.__relative = False
            self.__relative_extrusion = False
        elif self.__gcode.get("M", int) == 83:
            self.__relative_extrusion = True
        elif self.__gcode.get("M", int) == 82:
            self.__relative_extrusion = False

    def __update_acceleration(self):
        s = self.__gcode.get("S", float, None)
        p = self.__gcode.get("P", float, None)
        if self.__gcode.get("M", int) == 204 and (s is not None or p is not None):
            self.__acceleration = s or p

    def __get_dist_xy(self):
        x1 = self.__gcode.get("X", float, None)
        y1 = self.__gcode.get("Y", float, None)
        x2 = self.__pos["X"]
        y2 = self.__pos["Y"]
        if self.__is_move() and x1 is not None and y1 is not None:
            if self.__relative:
                x1 = x1 + self.__pos["X"]
                y1 = y1 + self.__pos["Y"]
            return math.sqrt(((x2 - x1) ** 2) + ((y2 - y1) ** 2))
        return 0.0

    def __get_dist_z(self):
        if self.__is_move():
            if not self.__relative:
                z = self.__gcode.get("Z", float, None)
                if z is not None:
                    dist_z = self.__pos["Z"] - z
                else:
                    dist_z = 0.0
            else:
                dist_z = self.__gcode.get("Z", float, 0.0)
            return abs(dist_z)
        return 0.0

    def __get_dist_e(self):
        if self.__is_move():
            if not self.__relative_extrusion:
                e = self.__gcode.get("E", float, None)
                if e is not None:
                    dist_e = self.__pos["E"] - e
                else:
                    dist_e = 0.0
            else:
                dist_e = self.__gcode.get("E", float, 0.0)
            return abs(dist_e)
        return 0.0

    def __calculate_time(self):
        if not self.__is_move():
            return
        if self.__get_dist_xy() != 0.0:
            self.__time += self.__accelerated_move(self.__get_dist_xy(), self.__acceleration)
        else:
            self.__time += self.__accelerated_move(self.__get_dist_e(), self.__extruder_acceleration)
        self.__time += self.__accelerated_move(self.__get_dist_z(), self.__z_acceleration)

    def __accelerated_move(self, length, acceleration):
        # for half of the move, there are 2 zones, where the speed is increasing/decreasing and
        # where the speed is constant.
        # Since the slowdown is assumed to be uniform, calculate the average velocity for half of the
        # expected displacement.
        # final velocity v = a*t
        # displacement dx = 0.5 * a * t^2
        # v_avg = 0.5v => 2*v_avg = v
        # d_x = v_avg*t => t = d_x / v_avg
        half_length = length / float(2)
        t_init = self.__velocity / acceleration  # time to final velocity
        dx_init = 0.5 * acceleration * (t_init ** 2)  # initial displacement for the time to get to final velocity
        t = 0.0
        if half_length >= dx_init:
            half_length -= dx_init
            t += t_init
        t += half_length / self.__velocity  # rest of the time is constant speed
        return t * 2.0  # cut in half before, so double to get full time spent.

    def __update_pos(self):
        if self.__is_move():
            if self.__relative:
                self.__pos["X"] += self.__gcode.get("X", float, 0.0)
                self.__pos["Y"] += self.__gcode.get("Y", float, 0.0)
                self.__pos["Z"] += self.__gcode.get("Z", float, 0.0)
            else:
                for coordinate in ["X", "Y", "Z"]:
                    value = self.__gcode.get(coordinate, float, None)
                    if value is not None:
                        self.__pos[coordinate] = value
            if self.__relative_extrusion:
                self.__pos["E"] += self.__gcode.get("E", float, 0.0)
            else:
                e = self.__gcode.get("E", float, None)
                if e is not None:
                    self.__pos["E"] = e

    def __handle_g92(self):
        if self.__gcode.get("G", int) == 92:
            for coordinate in ["X", "Y", "Z", "E"]:
                value = self.__gcode.get(coordinate, float, None)
                if value is not None:
                    self.__pos[coordinate] = value

    def __home(self):
        if self.__gcode.get("G", int) == 28:
            all_none = True
            for coordinate in ["X", "Y", "Z"]:
                value = self.__gcode.get(coordinate, float, None)
                if value is not None:
                    self.__pos[coordinate] = value
                    all_none = False
            if all_none:
                self.__pos["X"] = 0.0
                self.__pos["Y"] = 0.0
                self.__pos["Z"] = 0.0
