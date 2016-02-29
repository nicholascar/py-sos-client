from datetime import timedelta
from lxml import etree
from furl import furl
import requests
from requests.auth import HTTPProxyAuth
import json


def make_timespan(is_latest=True, date_start=None, date_end=None):
    if is_latest:
        return 'latest'
    else:
        # include/exclude exact time by minusing 1 second from start and end
        d = timedelta(seconds=1)
        ds = date_start - d
        de = date_end - d

        return ds.strftime('%Y-%m-%dT%H:%M:%S') + '+10:00/' + de.strftime('%Y-%m-%dT%H:%M:%S%Z') + '+10:00'


def parse_OM_Observation(obs):
    x = etree.fromstring(obs)
    c = x.getchildren()
    return etree.tostring(c)


def parse_observation(sos_xml):
    # remove the unicode declaration
    obs = etree.fromstring(sos_xml.replace('<?xml version="1.0" encoding="UTF-8"?>', ''))
    observations = []

    # for each OM_Observation
    for ob in obs.xpath('//om:OM_Observation', namespaces={'om': 'http://www.opengis.net/om/2.0'}):
        # get the procedure name for this Observation

        # TODO: why do I have to do this? why can't I just loop through XPath against ob?
        obb = etree.fromstring(etree.tostring(ob))
        for proc in obb.xpath('//om:procedure', namespaces={'om': 'http://www.opengis.net/om/2.0', 'xlink': 'http://www.w3.org/1999/xlink/href'}):
            proc_urn = ''
            for attr_name, attr_value in proc.items():
                proc_urn = attr_value

        for proc in obb.xpath('//om:observedProperty', namespaces={'om': 'http://www.opengis.net/om/2.0', 'xlink': 'http://www.w3.org/1999/xlink/href'}):
            op_urn = ''
            for attr_name, attr_value in proc.items():
                op_urn = attr_value

        # get the tvps for this Observation
        tvps = []
        for tvp in obb.xpath('//wml2:MeasurementTVP', namespaces={'om': 'http://www.opengis.net/om/2.0', 'wml2': 'http://www.opengis.net/waterml/2.0'}):
            tvps.append({
                'time': tvp[0].text,
                'value': tvp[1].text
            })

        observations.append({
            'procedure': proc_urn,
            'observedProperty': op_urn,
            'timeseries': tvps
        })

    return observations


def get_observation(query_uri_base, aws_urn, procedure, date_start, date_end, mimetype='application/xml'):
    # make timespan
    if date_end == 'latest':
        timespan = make_timespan(is_latest=True)
    else:
        timespan = make_timespan(is_latest=False, date_start=date_start, date_end=date_end)

    # build SOS GET query
    q = furl(query_uri_base + '/sos/kvp').add({
        'service': 'SOS',
        'version': '2.0.0',
        'request': 'GetObservation',
        #'namespaces': 'xmlns(om,http://www.opengis.net/om/2.0)',
        'featureOfInterest': aws_urn,
        #'temporalFilter': 'om:phenomenonTime,' + timespan,
        'procedure': procedure,
        #'responseFormat': 'http://www.opengis.net/waterml/2.0'
    }).url

    # run the query request
    creds = json.load(open('creds.json'))
    auth = HTTPProxyAuth(creds['username'], creds['password'])
    ga_proxy = {"http": creds['proxy']}
    r = requests.get(q, headers={'Accept': mimetype}, proxies=ga_proxy, auth=auth)

    # handle the SOS response
    if r.status_code == 200:
        # TODO: convert XML response to a Python object
        return [True, r.text]
    else:
        # TODO: handle error better
        return [False, r.text]


def get_featureOfInterest(query_uri_base, aws_urn=None):
    # assemble SOS query string for one or all stations
    q = None
    if aws_urn is not None:
        q = furl(query_uri_base + '/service').add({
            'service': 'SOS',
            'version': '2.0.0',
            'request': 'GetFeatureOfInterest',
            'featureOfInterest': aws_urn
        }).url
    else:
        q = furl(query_uri_base + '/sos/kvp').add({
            'service': 'SOS',
            'version': '2.0.0',
            'request': 'GetFeatureOfInterest',
        }).url

    # run the query request
    creds = json.load(open('creds.json'))
    auth = HTTPProxyAuth(creds['username'], creds['password'])
    ga_proxy = {"http": creds['proxy']}
    headers = {'accept': 'application/json'}
    r = requests.get(q, headers=headers, proxies=ga_proxy, auth=auth)

    results = json.loads(r.text)

    # return one or all
    if aws_urn is not None:
        return results['featureOfInterest'][0]
    else:
        #return sorted(results['featureOfInterest'], key=lambda k: k['name'])
        return sorted(results['featureOfInterest'])