def log_on_return_code(logger, action: str, return_message: tuple, **kwargs):
    return_code = return_message[0]
    message = return_message[1]
    if return_code == 0:
        logger.info(f'{action} was skipped!')
        logger.debug(return_message)
    elif return_code == 1:
        logger.info(f'{action} performed successfully')
        logger.debug(return_message)
    elif return_code == 2:
        logger.info(f'{action} was performed partially')
        logger.debug(return_message)
    elif return_code == 3:
        logger.info(f'{action} did not performed. Failure encountered. Please check the log for details')
        logger.error(message)
    elif return_code == 4:
        logger.info(f'{action} did not performed. Exception encountered')
        logger.error(message)
