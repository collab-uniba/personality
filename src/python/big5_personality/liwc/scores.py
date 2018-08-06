from datetime import datetime
from requests import *
import os
import sys
import random
import uuid
import json
import yaml
from liwc.orm.liwc_tables import LiwcScores
#sys.path.append('../')
#from db.setup import SessionWrapper

def load_liwc_config():
    with open(os.path.join(os.getcwd(), 'liwc/cfg/setup.yaml'), 'r') as config:
        cfg = yaml.load(config)
    
    return cfg['liwc']['baseurl'], cfg['liwc']['api_key'], cfg['liwc']['api_secret_key']

def get_content_data(content):
    attribs = {
        "language_content": content,
        "content_source": 3,
        "content_handle": None,
        "content_date": datetime.now().isoformat(),
        "recipient_id": None,
        "content_tags": None,
        'language': 'english'
        }
    return attribs

def api_base_url(baseurl):
    return "{}/v3/api".format(baseurl)

def get_content_api_url(baseurl):
    return "{}/content".format(api_base_url(baseurl))

def get_auth_headers(apikey, apisecret):
    header = {}
    if apikey:
        header['X-API-KEY'] = apikey
    if apisecret:
        header['X-API-SECRET-KEY'] = apisecret
    return header

def import_result(session, result, uid, p_name, month, email_count):
    ls = LiwcScores(dev_uid = uid, project_name = p_name, month = month, email_count = email_count, wc = result["wc"], sixltr = result["sixLtr"], clout = result["clout"], wps = result["wps"], analytic = result["analytic"], tone = result["tone"], 
                    dic = result["dic"], authentic = result["authentic"], family = result["categories"]["family"], feel = result["categories"]["feel"], money = result["categories"]["money"], insight = result["categories"]["insight"], number = result["categories"]["number"],
                    parenth = result["categories"]["Parenth"], cogproc = result["categories"]["cogproc"], otherp = result["categories"]["OtherP"], female = result["categories"]["female"], negate = result["categories"]["negate"],
                    negemo = result["categories"]["negemo"], differ = result["categories"]["differ"], death = result["categories"]["death"], adverb = result["categories"]["adverb"], informal = result["categories"]["informal"],
                    ipron = result["categories"]["ipron"], percept = result["categories"]["percept"], quant = result["categories"]["quant"], exclam = result["categories"]["Exclam"], adj = result["categories"]["adj"],
                    prep = result["categories"]["prep"], achieve = result["categories"]["achieve"], function = result["categories"]["function"], bio = result["categories"]["bio"], risk = result["categories"]["risk"],
                    leisure = result["categories"]["leisure"], quote = result["categories"]["Quote"], verb = result["categories"]["verb"], hear = result["categories"]["hear"], they = result["categories"]["they"],
                    affect = result["categories"]["affect"], you = result["categories"]["you"], work = result["categories"]["work"], period = result["categories"]["Period"], friend = result["categories"]["friend"],
                    focusfuture = result["categories"]["focusfuture"], auxverb = result["categories"]["auxverb"], male = result["categories"]["male"], shehe = result["categories"]["shehe"], semic = result["categories"]["SemiC"],
                    relig = result["categories"]["relig"], compare = result["categories"]["compare"], pronoun = result["categories"]["pronoun"], qmark = result["categories"]["QMark"], certain = result["categories"]["certain"],
                    assent = result["categories"]["assent"], we = result["categories"]["we"], sad = result["categories"]["sad"], affiliation = result["categories"]["affiliation"], see = result["categories"]["see"],
                    anger = result["categories"]["anger"], home = result["categories"]["home"], conj = result["categories"]["conj"], sexual = result["categories"]["sexual"], ppron = result["categories"]["ppron"],
                    motion = result["categories"]["motion"], space = result["categories"]["space"], filler = result["categories"]["filler"], anx = result["categories"]["anx"], focuspresent = result["categories"]["focuspresent"],
                    netspeak = result["categories"]["netspeak"], health = result["categories"]["health"], discrep = result["categories"]["discrep"], relativ = result["categories"]["relativ"], colon = result["categories"]["Colon"],
                    nonflu = result["categories"]["nonflu"], cause = result["categories"]["cause"], body = result["categories"]["body"], tentat = result["categories"]["tentat"], power = result["categories"]["power"],
                    interrog = result["categories"]["interrog"], social = result["categories"]["social"], drives = result["categories"]["drives"], focuspast = result["categories"]["focuspast"], article = result["categories"]["article"],
                    allpunc = result["categories"]["AllPunc"], apostro = result["categories"]["Apostro"], i = result["categories"]["i"], posemo = result["categories"]["posemo"], ingest = result["categories"]["ingest"],
                    dash = result["categories"]["Dash"], swear = result["categories"]["swear"], comma = result["categories"]["Comma"], time = result["categories"]["time"], reward= result["categories"]["reward"])
    
    session.add(ls)
    session.commit()
    
def get_scores(logger, session, uid, p_name, month, content, email_count):
    
    baseurl, apikey, apisecret = load_liwc_config()
    content_data = get_content_data(content)
    content_api_url = get_content_api_url(baseurl)
    auth_headers = get_auth_headers(apikey, apisecret)
    
    response = post(content_api_url, json=content_data, headers=auth_headers)
    if response.status_code == 200:
        response_json = json.loads(response.content)
        import_result(session, response_json["liwc_scores"], uid, p_name, month, email_count)
        return True;
    else: 
        logger.error('Connection error, retrying')
        return False;
