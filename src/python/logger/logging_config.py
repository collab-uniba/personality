import logging


def get_logger(name=__file__):
    logger = logging.getLogger(name)
    _format = '%(asctime)s - %(name)s - %(levelname)-8s %(message)s'

    # create console handler and set level to INFO
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(_format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # create error file handler and set level to WARNING
    handler = logging.FileHandler('error.log')
    handler.setLevel(logging.WARNING)
    #formatter = logging.Formatter(_format)
    #handler.setFormatter(formatter)
    logger.addHandler(handler)

    # create debug file handler and set level to DEBUG
    handler = logging.FileHandler('debug.log')
    handler.setLevel(logging.DEBUG)
    #formatter = logging.Formatter(_format)
    #handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
