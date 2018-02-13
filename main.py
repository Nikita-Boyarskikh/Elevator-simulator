#!/usr/bin/env python3
import sys
from gettext import gettext as _
from argparse import ArgumentParser, ArgumentTypeError, RawDescriptionHelpFormatter
from threading import Event

from elevator import Elevator, WrongActionError, __version__

SEPARATOR = ' '
MIN_FLOORS = 5
MAX_FLOORS = 20


def main():
    """Точка входа в программу"""
    args = parse_args()

    elevator = Elevator(**args)
    events_to_output = ['passed_floor', 'opened_doors', 'closed_doors']
    for event in events_to_output:
        elevator.subscribe(event, print_elevator_event)

    stop = Event()
    elevator.start(stop)

    for line in sys.stdin:
        try:
            name, floor = line.split(SEPARATOR, 2)
            if int(floor) not in range(1, int(args['n']) + 1):
                print(_('< ERROR: Wrong floors number: min=%d, max=%d' % (1, args['n'])))
                continue
            elevator.perform(name, int(floor))
        except ValueError:
            print(_('< ERROR: Wrong input format. Expected: action_name floor_number'))
        except WrongActionError:
            print(_('< ERROR: Wrong action'))
        else:
            print(_('< OK'))

    stop.set()


def print_elevator_event(event, floor):
    """
    Обработчик событый лифта. Выводит их в stdout
    :param event: название события лифта
    :param floor: этаж, на котором произошло событие
    """
    print('< ' + str(floor) + ': ' + str(event))


def parse_args():
    """
    Получает аргументы командной строки
    :return: возвращает словарь аргументов командной строки
    """
    parser = _get_parser()
    allowed_keys = ('n', 'h', 'v', 't')
    return permit(parser.parse_args(), *allowed_keys)


def positive(val):
    """
    Поднимает исключение ArgumentTypeError, если $val не положительное целое число
    :param val: значение для проверки
    :return: $val
    :raise ArgumentTypeError($val is not a positive number)
    """
    val = int(val)
    if val <= 0:
        raise ArgumentTypeError('%d is not a positive number' % val)
    return val


def permit(_dict, *keys):
    """
    Разрешает только ключи $keys для словаря $_dict
    :param _dict: словарь, источник данных
    :param keys: список разрешённых ключей
    :return: новый словарь из $_dict толко с ключами $keys
    """
    return dict(((i, getattr(_dict, i)) for i in keys))


def _get_parser():
    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
        description=_('This is command line program, which emulate elevator life cycle '
                      'and always waits for input from the user and '
                      'outputs the elevator actions in real time\n'
                      '\n'
                      'elevator events:\n'
                      '  elevator passed the floor\n'
                      '  elevator opened the doors\n'
                      '  elevator closed the doors\n'
                      '\n'
                      'possible user actions:\n'
                      '  Press the button inside the elevator (Example: "inside 3")\n'
                      '  Press the button on the floor (Example: "outside 1")\n'),
    )

    parser.add_argument(
        'n', choices=range(MIN_FLOORS, MAX_FLOORS + 1), type=int,
        metavar=('N{%d..%d}' % (MIN_FLOORS, MAX_FLOORS)),
        help=_('N - number of floors in entrance'),
    )
    parser.add_argument(
        'h', type=positive, metavar='h{1..}',
        help=_('h (m) - height of floor'),
    )
    parser.add_argument(
        'v', type=positive, metavar='v{1..}',
        help=_('v (m/sec) - velocity of elevator'),
    )
    parser.add_argument(
        't', type=positive, metavar='t{1..}',
        help=_('t (sec) - time before opening and closing elevator doors'),
    )
    parser.add_argument('-v', '--version', action='version', version=__version__)

    return parser


if __name__ == '__main__':
    main()
