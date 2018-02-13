import time
from threading import Thread
from queue import Queue
from collections import deque

# =========
# Constants
# =========

# Directions
UP = 1
DOWN = -1
NONE = 0

# Priorities
INSIDE = 1
OUTSIDE = 0


# ==========
# Exceptions
# ==========
class WrongActionError(Exception):
    """
    Исключение, поднимающееся при вызове Elevator.subscribe или Elevator.perform
    в случае, когда лифт не может выполнить это действие
    """


# ========
# Elevator
# ========
class Elevator:
    """
    Класс, описывающий лифт, его реакцию на действия пассажиров и поток событий лифта
    """

    direction = NONE
    floor = 1
    next_floor = None
    _thread = None
    _target_floors = Queue()
    _subscribes = {
        'passed_floor': None,
        'opened_doors': None,
        'closed_doors': None,
    }

    def __init__(self, n, h, v, t):
        """
        Инициализация лифта его параметрами:
        :param n: Количество этажей
        :param h: Высота одного этажа
        :param v: Скорость движения лифта
        :param t: Время между открытием и закрытием дверей
        """
        self.n = n
        self.h = h
        self.v = v
        self.t = t

        self._actions = {
            'inside': self._press_button,
            'outside': self._press_button,
        }

    def subscribe(self, action, callback):
        """
        Подписывает функцию $callback на действие лифта $action
        :param action: Название типа действия
        :param callback: Функция, принимающая описание действия лифта в качестве аргумента
                         и вызываемая, когда лифт выполнит это действие:
        :raise WrongActionError: если $action - действие, которое лифт не умеет выполнять
        """
        if action in self._subscribes:
            self._subscribes[action] = callback
        else:
            raise WrongActionError(action)

    def start(self, done):
        """
        Запускает лифт в отдельном потоке
        :param done: Событие завершения потока
        """
        self._thread = Thread(target=self._start, args=(done,), daemon=True).start()

    def _start(self, done):
        while not done.is_set():
            if self.direction == NONE and \
                    self.next_floor is None and \
                    not self._target_floors.empty():
                self._set_new_direction()

            if self.floor == self.next_floor:
                self._visit_floor()
                self.next_floor = None
                self.direction = NONE
            elif self.direction == DOWN and self.floor in self._target_floors.queue:
                self._visit_floor()
            elif self.direction != NONE:
                self._drive()

    def perform(self, action, floor):
        """
        Выполнение действия $action лифтом
        :param action: Название действия, которое необходимо выполнить лифту
        :param floor: Этаж, с которого происводят действие над лифтом
        :return: Результат выполнения действия
        :raise WrongActionError: если $action - действие, которое лифт не умеет выполнять
        """
        action_function = self._actions.get(action)
        if action_function:
            return action_function(int(floor))
        else:
            raise WrongActionError(action)

    # Возможные действия лифта
    def _set_new_direction(self):
        self.direction = self._get_new_direction()

    def _get_new_direction(self):
        if self.next_floor is None:
            if self._target_floors.empty():
                return NONE
            else:
                self.next_floor = self._target_floors.get()

        if self.next_floor < self.floor:
            return DOWN
        elif self.next_floor > self.floor:
            return UP
        else:
            return NONE

    def _load_passengers(self):
        self._call_if_subscribed('opened_doors', self.floor)
        time.sleep(self.t)
        self._call_if_subscribed('closed_doors', self.floor)

    def _drive(self):
        time.sleep(float(self.h) / float(self.v))
        self.floor += int(self.direction)
        self._call_if_subscribed('passed_floor', self.floor)

    def _visit_floor(self):
        self._target_floors.queue = _remove_all(self._target_floors.queue, self.floor)
        self._load_passengers()

    # Возможные действия над лифтом
    def _press_button(self, floor):
        floor = int(floor)
        self._target_floors.put_nowait(floor)

    # Вспомогательные функции
    def _call_if_subscribed(self, name, *args, **kwargs):
        func = self._subscribes.get(name)
        if func is not None:
            func(name, *args, **kwargs)


def _remove_all(iterable, value):
    return deque(list(filter(lambda a: a != value, iterable)))
