
import argparse
import datetime
import logging
import logging.handlers
import sys
import traceback

def _update_logger(verbosity):
    if verbosity == 0:
        _log.setLevel(logging.ERROR)
    elif verbosity == 1:
        _log.setLevel(logging.INFO)
    elif verbosity >= 2:
        _log.setLevel(logging.DEBUG)

def _initialize_logger():
    logger = logging.getLogger(__name__)
    logging.captureWarnings(True)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    #handler = logging.handlers.TimedRotatingFileHandler(config_file.log_file,
    #                                                    when="midnight",
    #                                                    interval=1,
    #                                                    backupCount=7)
    #handler.setFormatter(formatter)
    #logger.addHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

_log = _initialize_logger()

_DATE_CONVERSION_FMT = '%Y-%m-%d'

def _from_date(value, include_weekday=False):
    if not include_weekday:
        fmt_str = '{0:' + _DATE_CONVERSION_FMT + '}'
        return fmt_str.format(value)
    else:
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        fmt_str = '{0:' + _DATE_CONVERSION_FMT + '} ({1})'
        return fmt_str.format(value, weekdays[value.weekday()])

def _to_date(value):
    return datetime.datetime.strptime(value, _DATE_CONVERSION_FMT).date()

def _is_date(date_str):
    try:
        if date_str.lower() == 'today':
            return datetime.date.today()
        elif date_str.lower() == 'yesterday':
            return datetime.date.today() - datetime.timedelta(days=1)
        elif date_str.lower() == 'tomorrow':
            return datetime.date.today() + datetime.timedelta(days=1)
        else:
            return _to_date(date_str)
    except:
        raise argparse.ArgumentTypeError('date value is invalid')

def _is_percentage(percentage_str):
    try:
        percentage = int(percentage_str)
        if percentage < 1 or percentage > 100:
            raise 'error'
        return percentage_str
    except:
        raise argparse.ArgumentTypeError('percentage value is invalid (try a number between 1 and 100)')

def _parse_args():
    description = 'Calculate prescription refill date'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-d', '--days', metavar='<NUMBER>', default=30, type=int,
                        help='total number of days in prescription')
    parser.add_argument('-s', '--start_date', metavar='<YYYY-MM-DD>', default=datetime.date.today(), type=_is_date,
                        help='date of the usage')
    parser.add_argument('-p', '--percentage', metavar='<NUMBER>', default='80', type=_is_percentage,
                        help='percentage of prescription before a refill')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='output verbose debugging information')

    args = parser.parse_args()
    _update_logger(args.verbose)
    _log.info('verbose: %d, days: %d, start date: %s, percentage: %s',
              args.verbose, args.days, _from_date(args.start_date), args.percentage)
    return args.days, args.start_date, int(args.percentage)

def _get_refill_date(days, start_date, percentage):
    num_days = (days * percentage) / 100
    return start_date + datetime.timedelta(days=num_days)

def main():
    days, start_date, percentage = _parse_args()

    try:
        print('Refill date: {0}'.format(_from_date(_get_refill_date(days, start_date, percentage), True)))
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
