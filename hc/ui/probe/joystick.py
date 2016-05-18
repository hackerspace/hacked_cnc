import os
import time

from PyQt5.QtCore import pyqtSignal, QThread


class Joystick(QThread):
    button_down = pyqtSignal(int)
    axis_moving = pyqtSignal(int, float)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)

        self.parent = parent
        self.exiting = False
        self.start()

    def __del__(self):
        self.exiting = True
        self.wait()

    def run(self):
        import pygame

        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        pygame.joystick.init()
        done = False
        while not done:
            # reinnitialize the joystick every loop, this is so if the contoller is turned
            # on after the loop starts, it can still be read

            #joystick_count = pygame.joystick.get_count()
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    self.button_down.emit(event.button)
                elif event.type == pygame.JOYAXISMOTION:
                    self.axis_moving.emit(event.axis, event.value)

            time.sleep(0.2)
