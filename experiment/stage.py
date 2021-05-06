"""
This code contains classes to control the sample positioning stages

Nick Porter
jacioneportier@gmail.com
"""
import numpy as np
import serial
import time


class StageController:
    """

    """
    def __init__(self):
        # Connect to the controller
        self.port = serial.Serial('COM3', baudrate=38400, timeout=2)
        self.port.flush()

        # The numerical index of each stage ON THE CONTROLLER
        self.x_ax = 3
        self.y_ax = 2
        self.z_ax = 1
        self.q_ax = 4

        self.axes = [self.x_ax, self.y_ax, self.z_ax, self.q_ax]
        self.ax_names = {self.x_ax: 'X', self.y_ax: 'Y', self.z_ax: 'Z', self.q_ax: 'Q'}

        # Positions are recorded as tuples: ( intended , measured )
        # These are the positions in the coordinate system of the STAGES
        self.x = 0, 0
        self.y = 0, 0
        self.z = 0, 0

        # This is the rotational position which relates the two coordinate systems
        self.q = 0, 0

        # These are the positions in the coordinate system of the BEAMLINE
        self.x0 = 0
        self.y0 = 0
        self.z0 = 0

        self.check()
        self.measure()
        pass

    def zero(self):
        # Move to zero the sample on the beamline
        # Rotate to align the y-axis parallel to the beamline
        self.command('0ZRO')
        self.measure(False)
        pass

    def home_all(self):
        self.move_to((0, 0, 0, 0))
        return

    def home_xy(self):
        cmd = f'{self.x_ax}MSA0;{self.y_ax}MSA0 \n0RUN'
        self.command(cmd)
        self.measure(False)
        pass

    def move_to(self, xyzq):
        for i, ax in enumerate(self.axes):
            self.command(f'{ax}MSA{xyzq[i]}')
        self.command('0RUN')
        self.measure(False)
        return

    def move_x0(self, x0_pos):
        # Transform the desired h-position into the xyz coordinates
        q = self.q[1] * np.pi / 180
        x = x0_pos*np.cos(q)
        y = -x0_pos*np.sin(q)
        self.command(f'{self.x_ax}MVA{x:0.6f}')
        while self.is_moving():
            time.sleep(0.1)
        self.command(f'{self.y_ax}MVA{y:0.6f}')
        self.measure(False)
        return

    def move_y0(self, y0_pos):
        # Transform the desired h-position into the xyz coordinates
        q = self.q[1] * np.pi / 180
        x = y0_pos*np.sin(q)
        y = y0_pos*np.cos(q)
        self.command(f'{self.x_ax}MVA{x:0.6f}')
        while self.is_moving():
            time.sleep(0.1)
        self.command(f'{self.y_ax}MVA{y:0.6f}')
        self.measure(False)
        return

    def move_x(self, x_pos):
        cmd = f'{self.x_ax}MVA{x_pos:0.6f}'
        self.command(cmd)
        self.measure(False)
        return

    def move_y(self, y_pos):
        cmd = f'{self.y_ax}MVA{y_pos:0.6f}'
        self.command(cmd)
        self.measure(False)
        return

    def move_z(self, z_pos):
        cmd = f'{self.z_ax}MVA{z_pos:0.6f}'
        self.command(cmd)
        self.measure(False)
        return

    def move_q(self, q_pos):
        cmd = f'{self.q_ax}MVA{q_pos:0.6f}'
        self.command(cmd)
        self.measure(False)
        pass

    def show_off(self):
        self.move_to((5, 5, 5, 10))
        self.move_to((0, 0, 0, 0))

    def measure(self, print_lines=True):
        positions = []
        lines = 'AXIS'.ljust(12) + 'CALC'.ljust(12) + 'MEAS\n'
        while self.is_moving():
            time.sleep(0.1)
        for ax in self.axes:
            pos = self.query(f'{ax}POS?')
            pos = pos.split(',')  # Parse the returned string
            pos = (float(pos[0]), float(pos[1]))
            lines = lines + self.ax_names[ax].ljust(12) + str(pos[0]).ljust(12) + str(pos[1]) + '\n'
            positions.append(pos)

        self.x, self.y, self.z, self.q = tuple(positions)

        self.x0 = self.x*np.cos(self.q) - self.y*np.sin(self.q)
        self.y0 = self.x*np.sin(self.q) + self.y*np.cos(self.q)
        self.z0 = self.z
        if print_lines:
            print(lines)
        return

    def check(self):
        for ax in self.axes:
            status = self.get_status(ax)
            print(f'{self.ax_names[ax]}-axis  (SB: {status})')
            err = self.query(f'{ax}ERR?')
            if len(err):
                for s in err.split('#'):
                    if len(s) and not s.isspace():
                        print(f'\t{s}')
            else:
                print('\tNo errors')

    def get_status(self, ax):
        s = int(self.query(f'{ax}STA?'))
        status = f'{s:b}'.rjust(8, '0')
        return status

    def is_moving(self):
        for ax in self.axes:
            if bool(int(self.get_status(ax)[1:4])):
                return True
        else:
            return False

    def command(self, cmd_str):
        self.port.write(bytes(f'{cmd_str}\n\r'.encode('utf-8')))
        pass

    def query(self, qry_str):
        self.port.write(bytes(f'{qry_str}\n\r'.encode('utf-8')))
        time.sleep(0.1)
        s = str(self.port.readline())
        s = s.replace(r'\n', '')
        s = s.replace(r'\r', '')
        s = s.removeprefix("b'")
        s = s.removesuffix("'")
        s = s[s.find('#') + 1:]
        return s


if __name__ == '__main__':
    ctrl = StageController()
    ctrl.show_off()
