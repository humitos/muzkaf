import os
import sys
import random

# http://docs.python.org/library/select.html
import select

# http://pygame.org
import pygame

WIDTH = 640
HEIGHT = 480

pygame.init()

fpsClock = pygame.time.Clock()

window = pygame.display.set_mode((WIDTH, HEIGHT))

# color definitions
black = pygame.Color(0, 0, 0)
gray = pygame.Color(128, 128, 128)
white = pygame.Color(255, 255, 255)
green = pygame.Color(0, 255, 0)
red = pygame.Color(255, 0, 0)
blue = pygame.Color(0, 0, 255)
pink = pygame.Color(255, 0, 255)
darkGreen = pygame.Color(0, 128, 0)
darkRed = pygame.Color(128, 0, 0)
darkBlue = pygame.Color(0, 0, 128)
darkPink = pygame.Color(128, 0, 128)

intervalColors = [
    blue,   # octave
    red,    # 2nd m
    pink,   # 2nd M
    green,  # 3rd m
    green,  # 3rd M
    blue,   # 4th P
    red,    # 4th A/5th D
    blue,   # 5th P
    green,  # 6th m
    green,  # 6th M
    pink,   # 7th m
    red,    # 7th M
]

inactiveColors = [
    darkBlue,   # octave
    darkRed,    # 2nd m
    darkPink,   # 2nd M
    darkGreen,  # 3rd m
    darkGreen,  # 3rd M
    darkBlue,   # 4th P
    darkRed,    # 4th A/5th D
    darkBlue,   # 5th P
    darkGreen,  # 6th m
    darkGreen,  # 6th M
    darkPink,   # 7th m
    darkRed,    # 7th M
]

# open MIDI device
# It could be /dev/midi1 or /dev/midi2
# What's about Windows?
fd = os.open('/dev/midi2', os.O_RDONLY)

poll = select.poll()

poll.register(fd, select.POLLIN)

step = 0
notes = []


def add_intervals(new_note):
    global notes

    for n in notes:
        if n.active:
            n.intervals.append(new_note)


class Note(object):
    def __init__(self, step, pitch):
        self.pitch = pitch
        self.step = step
        self.active = True
        self.intervals = []

        self._draw_data = {
            'circles': {
                'radio': 2,
                'radio_random': 2,
                'width': 10,
                },
            'x': {
                'width': 2,
                'x_pos': 0,
                'y_pos': 0,
                'times': 0,
                }
            }

    @property
    def x(self):
        return WIDTH - (step - self.step)

    @property
    def y(self):
        return HEIGHT - 4 * self.pitch

    def color(self, other):
        if n.active and other.active:
            colorArray = intervalColors
        else:
            colorArray = inactiveColors
        color = colorArray[(other.pitch - self.pitch) % 12]
        color = colorArray[self.pitch % 12]
        return color

    def _draw_point(self, window):
        color = white if self.active else gray
        pygame.draw.circle(window, color, (self.x, self.y), 2)

    def _draw_line(self, window):
        for other in self.intervals:
            color = self.color(other)
            pygame.draw.aaline(window, color, (self.x, self.y),
                               (other.x, other.y), 1)

    def _draw_circle(self, window, random_center=False):
        if self._draw_data['circles']['radio'] < WIDTH:
            color = self.color(self)
            if random_center:
                x_pos = random.randint(0, HEIGHT)
                y_pos = random.randint(0, WIDTH)
                radio_value = 'radio_random'
                radio_increase = 1
            else:
                x_pos = WIDTH / 2
                y_pos = HEIGHT / 2
                radio_value = 'radio'
                radio_increase = 5

            if self._draw_data['circles'][radio_value] > \
                    self._draw_data['circles']['width']:
                width = self._draw_data['circles']['width']
            else:
                width = 1

            pygame.draw.circle(window, color, (x_pos, y_pos),
                               self._draw_data['circles'][radio_value], width)
            self._draw_data['circles'][radio_value] += radio_increase

    def _draw_random_circle(self, window):
        self._draw_circle(window, random_center=True)

    def _draw_random_x(self, window):
        if self._draw_data['x']['width'] < WIDTH:
            color = self.color(self)
            width = self._draw_data['x']['width']

            y_pos = random.randint(0, HEIGHT)
            x_pos = random.randint(0, WIDTH)

            rect = pygame.Rect(x_pos, y_pos, 15, 15)
            pygame.draw.rect(window, color, rect, width)
            self._draw_data['x']['width'] += 10

    def draw(self, window):
        self._draw_point(window)
        self._draw_line(window)
        self._draw_circle(window)
        self._draw_random_circle(window)
        self._draw_random_x(window)


while True:
    step = step + 1
    data = poll.poll(0)

    while data:
        code = ord(os.read(fd, 1))
        if code in (144, 128):
            pitch, force = [ord(x) for x in os.read(fd, 2)]
            if code == 144:
                new_note = Note(step, pitch)
                notes.append(new_note)
                add_intervals(new_note)
            else:
                # !!Use a dict for pitches
                for n in notes:
                    if n.pitch == pitch:
                        n.active = False
        data = poll.poll(0)

    # remove innecesary notes
    notes = [x for x in notes if x.step > step - WIDTH]

    # fill the window with black color
    window.fill(black)

    # draw all the notes
    for n in notes:
        n.draw(window)

    # refresh the pygame window
    pygame.display.update()

    # handle pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # next step
    fpsClock.tick(30)
