#!/usr/bin/env python3

import unittest
import time
from threading import Event

from elevator import Elevator, WrongActionError, NONE, UP, DOWN
from test_utils.stubs import stub_time_sleep, sleeps

# Globals
PRECISION = 10 ** -9
TIME_SCALE = 10 ** -5

# Times
FLOORS = 5
DELTA = 3 * TIME_SCALE
SPEED = 1 / TIME_SCALE
HEIGHT = 4

events = {}
allowed_events = ['passed_floor', 'opened_doors', 'closed_doors']


def spy_event(event, floor):
    if events.get(event) is None:
        events[event] = []
    events[event].append(floor)


class ElevatorTest(unittest.TestCase):
    @staticmethod
    def getElevator(n, h, v, t):
        elevator = Elevator(n, h, v, t)
        for event in allowed_events:
            elevator.subscribe(event, spy_event)

        stop = Event()
        elevator.start(stop)
        return elevator, stop

    def test_subscribe(self):
        elevator = Elevator(10, 1, 1, 1)

        for event in allowed_events:
            def func(): pass
            elevator.subscribe(event, func)
            self.assertEqual(elevator._subscribes[event], func, 'Event: ' + event)

        with self.assertRaises(WrongActionError) as cm:
            elevator.subscribe('some_other_event', lambda: None)
        self.assertEqual(str(cm.exception), 'some_other_event', 'WrongActionError message')

    def test_initial_values(self):
        elevator, stop = self.getElevator(9, 8, 7, 6)
        self.assertEqual(elevator.floor, 1, 'Initial floor')
        self.assertIsNone(elevator.next_floor, 'Initial next_floor')
        self.assertEqual(elevator.direction, NONE, 'Initial direction')

        stop.set()

    def test_perform(self):
        elevator, stop = self.getElevator(5, 4, 3, 2)

        with self.assertRaises(WrongActionError) as cm:
            elevator.perform('some_wrong_action', 1)
        self.assertEqual(str(cm.exception), 'some_wrong_action', 'WrongActionError message')

        elevator.perform('inside', 2)
        self.assertIn(2, elevator._target_floors.queue, 'button pressed from inside')
        elevator.perform('outside', 3)
        self.assertIn(3, elevator._target_floors.queue, 'button pressed from outside')

        stop.set()

    def test_interactive_drive(self):
        floor = 2

        elevator, stop = self.getElevator(FLOORS, HEIGHT, SPEED, DELTA)
        self._call_elevator(elevator, 1, floor, floor, 'outside')
        time.sleep(HEIGHT / SPEED)
        self.assertEqual(elevator.floor, floor, 'elevator drives to {} floor'.format(floor))
        self.assertEqual(events.get('passed_floor'), [floor], 'elevator passed floor')
        self.assertEqual(events.get('opened_doors'), [floor], 'elevator opened doors')
        time.sleep(DELTA)
        self.assertEqual(events.get('closed_doors'), [floor], 'elevator closed doors')

        stop.set()

    @stub_time_sleep
    def test_drive_down(self):
        top_floor = 5
        floors = (2, 3)

        elevator, stop = self.getElevator(FLOORS, HEIGHT, SPEED, DELTA)
        self._drive_throw_floor_with_loading_passangers(elevator, top_floor)

        for floor in floors:
            elevator.perform('outside', floor)
        # self.call_elevator(elevator, 1, floor, top_floor, 'inside')
        # self.call_elevator(elevator, 1, 1, top_floor, 'inside')
        # self.call_elevator(elevator, 1, 2, top_floor, 'outside')

        stop.set()

    def _drive_throw_floor_with_loading_passangers(self, elevator, floor):
        elevator.perform('inside', floor)
        time.sleep(PRECISION)
        self.assertEqual(elevator.floor, floor, 'elevator drives to {} floor'.format(floor))
        expected = dict(map(lambda event: (event, [floor]), ['opened_doors', 'closed_doors']))
        expected['passed_floor'] = list(range(2, floor + 1))
        self.assertDictEqual(events, expected, 'all expected events happened')
        self.assertEqual(sum(sleeps), DELTA + HEIGHT / SPEED * (floor - 1),
                         'elevator spend time to open and close doors, drives to {} floor'.format(floor))

    def _call_elevator(self, elevator, from_floor, to_floor, next_floor, position):
        elevator.perform(position, to_floor)
        time.sleep(PRECISION)
        self.assertEqual(elevator.next_floor, next_floor, 'next_floor is set')
        self.assertEqual(elevator.direction, (UP if from_floor < next_floor else DOWN), 'elevator direction')
        self.assertEqual(elevator.floor, from_floor, 'floor is still ' + str(from_floor))


if __name__ == '__main__':
    unittest.main()
