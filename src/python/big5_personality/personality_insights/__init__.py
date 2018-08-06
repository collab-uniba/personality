import os

import yaml
from watson_developer_cloud import PersonalityInsightsV3

with open(os.path.join(os.getcwd(), '../big5_personality/personality_insights/cfg/watson.yaml'), 'r') as config:
    cfg = yaml.load(config)

    big5_personality = PersonalityInsightsV3(
        version=cfg['personality']['version'].strftime('%Y-%m-%d'),
        username=cfg['personality']['username'],
        password=cfg['personality']['password']
    )
