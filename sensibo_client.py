import requests
import json
from datetime import datetime
from dateutil import tz

_SERVER = 'https://home.sensibo.com/api/v2'

class SensiboClientAPI(object):
    def __init__(self, api_key):
        self._api_key = api_key

    def _get(self, path, ** params):
        params['apiKey'] = self._api_key
        response = requests.get(_SERVER + path, params = params)
        response.raise_for_status()
        return response.json()

    def _post(self, path, data, ** params):
        params['apiKey'] = self._api_key
        response = requests.post(_SERVER + path, params = params, data = data)
        response.raise_for_status()
        return response.json()

    def pod_uids(self):
        result = self._get("/users/me/pods")
        pod_uids = [x['id'] for x in result['result']]
        return pod_uids

    def pod_measurement(self, podUid):
        result = self._get("/pods/%s/measurements" % podUid)
        return result['result']

    def pod_ac_state(self, podUid):
        result = self._get("/pods/%s/acStates" % podUid, limit = 1, fields="status,reason,acState")
        return result['result'][0]
    
    def pod_lastX_ac_state(self, podUid,nb):
        result = self._get("/pods/%s/acStates" % podUid, limit = nb, fields="status,reason,time,acState")
        return result['result']	
        
    def pod_change_ac_state(self, podUid, on, target_temperature, mode, fan_level):
        self._post("/pods/%s/acStates" % podUid,
                json.dumps({'acState': {"on": on, "targetTemperature": target_temperature, "mode": mode, "fanLevel": fan_level}}))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Sensibo client example parser')
    parser.add_argument('apikey', type = str)
    args = parser.parse_args()

    client = SensiboClientAPI(args.apikey)
    pod_uids = client.pod_uids()
    print "All pod uids:", ", ".join(pod_uids)
    print "Pod measurement for first pod", client.pod_measurement(pod_uids[0])
    last_ac_state = client.pod_ac_state(pod_uids[0])
    print "Last AC change %(success)s and was caused by %(cause)s" % { 'success': 'was successful' if last_ac_state['status'] == 'Success' else 'failed', 'cause': last_ac_state['reason'] } 
    print "and set the ac to %s" % str(last_ac_state['acState'])
    print "Change AC state of %s" % pod_uids[0]
    
    #get the x last states
    # Convert the date to local timezone
    fmt = '%d/%m/%Y %H:%M:%S'
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    
    # Get the last 10 states of the AC
    last5_ac_state = client.pod_lastX_ac_state(pod_uids[0],10)
    for ac_state in last5_ac_state:
        sstring = datetime.strptime(ac_state['time']['time'],'%Y-%m-%dT%H:%M:%SZ')
        utc = sstring.replace(tzinfo=from_zone)
        localzone = utc.astimezone(to_zone)
        sdate = localzone.strftime(fmt)
        print "Command executed at %(date)s : %(state)s" % { 'date' : sdate, 'state': str(ac_state['acState'])}
    
    client.pod_change_ac_state(pod_uids[0], True, 23, 'cool', 'auto')
