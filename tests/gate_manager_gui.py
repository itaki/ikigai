import json
import curses
import shutil
import os
from datetime import datetime
from gate_manager import Gate_Manager
from _drop.blinky_bits import hex_to_int, get_full_path, backup_file, save_file

__all__ = ["GateManagerGUI", "main"]


def center_x(width, string):
    '''Takes curses terminal width and a string and determines where to start it to center it'''
    return int((width // 2) - (len(string) // 2) - len(string) % 2)
class GateManagerGUI:
    
    def __init__(self):
        self.gm = Gate_Manager()

    def set_all_gates_angles(self):
        for gate_key in self.gm.gates.keys():
            if not self.set_min(gate_key) or not self.set_max(gate_key):
                return False
        return True

    def set_gate_angle(self, stdscr, gate_key, side):
        """Curses function for adjusting the gate angle."""
        my_gate = self.gm.gates[gate_key]
        key = None
        adjustment = 0
        flagged = True

        too_high, too_low = False, False
        
        angle = my_gate.min if side == 'min' else my_gate.max

        stdscr.clear()
        stdscr.refresh()

        curses.noecho()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

        height, width = stdscr.getmaxyx()
        start_y = int((height // 2) - 4)  # Center vertically for 8 lines of info
        cent_x = int(width // 2)

        while True:
            adjustment = 0
            if key == "KEY_DOWN":
                adjustment = -1
            elif key == "KEY_LEFT":
                adjustment = -10
            elif key == "KEY_UP":
                adjustment = 1
            elif key == "KEY_RIGHT":
                adjustment = 10
            elif key == "0":
                angle = 90
                my_gate.servo.angle = angle
            elif key == "q":
                return -1
            elif key == "s":
                my_gate.servo.angle = angle  # Ensure the servo is set to the final angle
                return int(angle)

            if adjustment != 0 or flagged:
                flagged = False
                angle = max(0, min(180, angle + adjustment))
                too_high = angle == 180
                too_low = angle == 0

                my_gate.servo.angle = angle
                print(f"Angle = {angle}")

            title = f"Set {side} angle for gate {my_gate.name} on pin {my_gate.pin}"[:width-1]
            instructions = "Use arrow keys  :  '0' to recenter  :  'q' to quit  :  's' to save"[:width-1]
            angle_reading = f"Angle: {angle}"[:width-1]
            if too_low:
                angle_reading += ' WARNING!!! TOO LOW'
            if too_high:
                angle_reading += ' WARNING!!! TOO HIGH'
            statusbarstr = f"Press 'q' to exit | Press 's' to save | Last key pressed: {key}"[:width-1]

            start_x_title = cent_x - len(title) // 2
            start_x_instructions = cent_x - len(instructions) // 2
            start_x_angle_reading = cent_x - len(angle_reading) // 2
            min_marker = cent_x + (my_gate.min - 90)
            max_marker = cent_x + (my_gate.max - 90)
            angle_marker = cent_x + (angle - 90)

            stdscr.clear()

            stdscr.attron(curses.color_pair(3))
            statusbarstr = statusbarstr[:width-1]
            stdscr.addstr(height-1, 0, statusbarstr)
            stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
            stdscr.attroff(curses.color_pair(3))

            if start_y < height:
                stdscr.addstr(start_y, start_x_title, title, curses.color_pair(2) | curses.A_BOLD)
            if start_y + 2 < height:
                stdscr.addstr(start_y + 2, start_x_instructions, instructions)
            
            min_color = curses.color_pair(2) if side == 'min' else curses.color_pair(1)
            max_color = curses.color_pair(2) if side == 'max' else curses.color_pair(1)

            if start_y + 3 < height:
                if 0 <= min_marker < width:
                    stdscr.addstr(start_y + 3, min_marker, '|', min_color | curses.A_BOLD)
                if 0 <= max_marker < width:
                    stdscr.addstr(start_y + 3, max_marker, '|', max_color | curses.A_BOLD)
                if 0 <= angle_marker < width:
                    stdscr.addstr(start_y + 3, angle_marker, '|')

            gauge_start_x = max(0, (width // 2) - 90)
            gauge_end_x = min(width, (width // 2) + 90)
            if start_y + 4 < height:
                stdscr.addstr(start_y + 4, gauge_start_x, '-' * (gauge_end_x - gauge_start_x))

            if start_y + 5 < height:
                if 0 <= cent_x - 91 < width:
                    stdscr.addstr(start_y + 5, cent_x - 91, '0', curses.color_pair(1))
                if 0 <= cent_x - 61 < width:
                    stdscr.addstr(start_y + 5, cent_x - 61, '30', curses.color_pair(1))
                if 0 <= cent_x - 31 < width:
                    stdscr.addstr(start_y + 5, cent_x - 31, '60', curses.color_pair(1))
                if 0 <= cent_x - 1 < width:
                    stdscr.addstr(start_y + 5, cent_x - 1, '90', curses.color_pair(1))
                if 0 <= cent_x + 29 < width:
                    stdscr.addstr(start_y + 5, cent_x + 29, '120', curses.color_pair(1))
                if 0 <= cent_x + 59 < width:
                    stdscr.addstr(start_y + 5, cent_x + 59, '150', curses.color_pair(1))
                if 0 <= cent_x + 89 < width:
                    stdscr.addstr(start_y + 5, cent_x + 89, '180', curses.color_pair(1))

            if start_y + 7 < height:
                stdscr.addstr(start_y + 7, start_x_angle_reading, angle_reading)

            stdscr.refresh()
            key = stdscr.getkey()

    def set_min(self, gate_key):
        gate_min = curses.wrapper(self.set_gate_angle, gate_key, 'min')
        if gate_min != -1:
            self.gm.gates[gate_key].min = gate_min
            self.gm.gates_dict['gates'][gate_key]['min'] = gate_min  # Update gates_dict with the new min value
            return True
        print("Changes abandoned")
        return False
    
    def set_max(self, gate_key):
        gate_max = curses.wrapper(self.set_gate_angle, gate_key, 'max')
        if gate_max != -1:
            self.gm.gates[gate_key].max = gate_max
            self.gm.gates_dict['gates'][gate_key]['max'] = gate_max  # Update gates_dict with the new max value
            return True
        print("Changes abandoned")
        return False

    def save_gates(self):
        self.backup_gates()
        save_file(self.gm.gates_dict, get_full_path("gates.json"))
        print("Changes saved")
    
    def backup_gates(self):
        backup_file(self.gm.gates_dict, get_full_path("gates.json"))
        print("Backup saved")

def main():
    gm_gui = GateManagerGUI()
    if gm_gui.set_all_gates_angles():
        gm_gui.save_gates()
    else:
        print("No changes were saved.")

if __name__ == "__main__":
    main()
