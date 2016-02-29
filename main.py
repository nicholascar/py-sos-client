import json
import functions_sos
from datetime import date
from datetime import timedelta
import requests
from requests.auth import HTTPProxyAuth


def main():
    #fois = functions_sos.get_featureOfInterest('http://52.62.205.218:8080/52n-sos-webapp')
    #print fois
    #creds = json.load(open('creds.json'))
    #auth = HTTPProxyAuth(creds['username'], creds['password'])
    #ga_proxy = {"http": creds['proxy']}
    #r = requests.get('http://www.google.com.au', proxies=ga_proxy, auth=auth)
    #print r.status_code
    #print r.text

    date_start = date(2009, 1, 1)
    date_end = date(2015, 1, 1)
    obs = functions_sos.get_observation('http://52.62.205.218:8080/52n-sos-webapp',
                                        'A351',
                                        'Node record',
                                        date_start,
                                        date_end,
                                        mimetype='application/json')
    print obs[1]

#    obs_json = json.loads(obs)
    #print obs_json


if __name__ == "__main__":
    main()