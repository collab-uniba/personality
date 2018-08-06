from personality_insights import big5_personality

def get_profile_insights(logger, email_content):
    try:
        try:
            json_profile = big5_personality.profile(email_content, content_type='text/html',  # text/plain
                                                    raw_scores=True,
                                                    consumption_preferences=True)
        except (ConnectionError, ConnectTimeout):
            logger.error('Connection error, retrying')
            try:
                json_profile = big5_personality.profile(email_content, content_type='text/html',  # text/plain
                                                        raw_scores=True,
                                                        consumption_preferences=True)
            except (ConnectionError, ConnectTimeout):
                logger.error('Connection error on retry, skipping')
                json_profile = ''
    except (WatsonException, WatsonInvalidArgument) as e:
        logger.error(e)
        json_profile = ''

    return json_profile