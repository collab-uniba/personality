from .orm.liwc_tables import LiwcScores, LiwcProjectMonth


def get_openness(score):
    # missing: first person, positive feelings, sensory processes, other references, humans, inclusive, sports,
    # physical states, sleep, grooming
    return (
                - 0.21 * score.pronoun - 0.16 * score.i - 0.1 * score.we - 0.12 * score.you - 0.13 * score.negate - 0.11 * score.assent
                + 0.2 * score.article + 0.17 * score.prep - 0.12 * score.affect - 0.15 * score.posemo - 0.09 * score.cogproc
                - 0.12 * score.discrep - 0.08 * score.hear - 0.14 * score.social - 0.17 * score.family - 0.22 * score.time
                - 0.16 * score.focuspast - 0.16 * score.focuspresent - 0.11 * score.space - 0.22 * score.motion - 0.17 * score.leisure
                - 0.2 * score.home + 0.15 * score.death - 0.15 * score.ingest)


def get_conscientiousness(score):
    # missing: sensory processes, humans, exclusive, music
    return (
                - 0.17 * score.negate - 0.18 * score.negemo - 0.19 * score.anger - 0.11 * score.sad - 0.11 * score.cogproc - 0.12 * score.cause
                - 0.13 * score.discrep - 0.1 * score.tentat - 0.1 * score.certain - 0.12 * score.hear + 0.09 * score.time + 0.14 * score.achieve
                - 0.12 * score.death - 0.14 * score.swear)


def get_extraversion(score):
    # missing: positive feelings, sensory processes, communication, other references, humans, inclusive, occupation, music,
    # physical states
    return (
                0.11 * score.we + 0.16 * score.you - 0.12 * score.number + 0.1 * score.posemo - 0.09 * score.cause - 0.11 * score.tentat
                + 0.1 * score.certain + 0.12 * score.hear + 0.15 * score.social + 0.15 * score.friend + 0.09 * score.family
                - 0.08 * score.work - 0.09 * score.achieve + 0.08 * score.leisure + 0.11 * score.relig + 0.1 * score.body
                + 0.17 * score.sexual)


def get_agreeableness(score):
    # missing: positive feelings, other references, inclusive, music, physical states, sleep
    return (
                0.11 * score.pronoun + 0.18 * score.we + 0.11 * score.number + 0.18 * score.posemo - 0.15 * score.negemo - 0.23 * score.anger
                - 0.11 * score.cause + 0.09 * score.see + 0.1 * score.feel + 0.13 * score.social + 0.11 * score.friend + 0.19 * score.family
                + 0.12 * score.time + 0.1 * score.focuspast + 0.16 * score.space + 0.14 * score.motion + 0.15 * score.leisure + 0.19 * score.home
                - 0.11 * score.money - 0.13 * score.death + 0.09 * score.body + 0.08 * score.sexual - 0.21 * score.swear)


def get_neuroticism(score):
    # missing: first person, other references, exclusive, sleep
    return (
                0.12 * score.i - 0.15 * score.you + 0.11 * score.negate - 0.11 * score.article + 0.16 * score.negemo + 0.17 * score.anx
                + 0.13 * score.anger + 0.1 * score.sad + 0.13 * score.cogproc + 0.11 * score.cause + 0.13 * score.discrep
                + 0.12 * score.tentat + 0.13 * score.certain + 0.1 * score.feel - 0.08 * score.friend - 0.09 * score.space + 0.11 + score.swear)


def get_profile_liwc(session, logger):
    scores = session.query(LiwcScores)
    logger.info('Getting personality scores')
    for score in scores:
        big5 = {}
        # controlla i nomi dei 5 tratti
        big5['openness'] = get_openness(score)
        big5['conscientiousness'] = get_conscientiousness(score)
        big5['extraversion'] = get_extraversion(score)
        big5['agreeableness'] = get_agreeableness(score)
        big5['neuroticism'] = get_neuroticism(score)

        lpm = LiwcProjectMonth(dev_uid=score.dev_uid, project_name=score.project_name, month=score.month,
                               email_count=score.email_count, word_count=score.wc, scores=big5)
        session.add(lpm)
        session.commit()
