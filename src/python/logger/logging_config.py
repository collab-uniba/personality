import logging


def get_logger(name=__file__, console_level=logging.INFO):
    #_format = '%(asctime)s - %(name)s - %(levelname)-8s %(message)s'
    #logging.basicConfig(format=_format, datefmt='%m/%d/%Y %I:%M:%S %p')
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to INFO
    ch = logging.StreamHandler()
    ch.setLevel(console_level)
    # create formatter
    formatter = logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s]: %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    # create error file handler and set level to WARNING
    eh = logging.FileHandler('error.log')
    eh.setLevel(logging.WARNING)
    eh.setFormatter(formatter)
    logger.addHandler(eh)

    # create debug file handler and set level to DEBUG
    dh = logging.FileHandler('debug.log')
    dh.setLevel(logging.DEBUG)
    dh.setFormatter(formatter)
    logger.addHandler(dh)

    return logger
