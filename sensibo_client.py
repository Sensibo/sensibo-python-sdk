import requests
import json

_SERVER = 'https://home.sensibo.com/api/v2'

class SensiboClientAPI(object):
    def __init__(self, api_key):
        self._api_key = api_key

    def _get(self, path, ** params):
        params['apiKey'] = self._api_key
        response = requests.get(_SERVER + path, params = params)
        response.raise_for_status()
        return response.json()

    def _patch(self, path, data, ** params):
        params['apiKey'] = self._api_key
        response = requests.patch(_SERVER + path, params = params, data = data)
        response.raise_for_status()
        return response.json()

    def devices(self):
        result = self._get("/users/me/pods", fields="id,room")
        return {x['room']['name']: x['id'] for x in result['result']}

    def pod_measurement(self, podUid):
        result = self._get("/pods/%s/measurements" % podUid)
        return result['result']

    def pod_ac_state(self, podUid):
        result = self._get("/pods/%s/acStates" % podUid, limit = 1, fields="status,reason,acState")
        return result['result'][0]['acState']

    def pod_change_ac_state(self, podUid, currentAcState, propertyToChange, newValue):
        self._patch("/pods/%s/acStates/%s" % (podUid, propertyToChange),
                json.dumps({'currentAcState': currentAcState, 'newValue': newValue}))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Sensibo client example parser')
    parser.add_argument('apikey', type = str, help='Obtain from https://home.sensibo.com/me/api')
    parser.add_argument('--deviceName', type = str, help='Device name')
    parser.add_argument('--showState', action='store_true',help='Display the AC state')
    parser.add_argument('--showMeasurement', action='store_true',help='Display the sensor measurements')
    args = parser.parse_args()
    #print(args)

    client = SensiboClientAPI(args.apikey)
    try:
      devices = client.devices()
      print ("-" * 10, "devices", "-" * 10)
      print (devices)
    except requests.exceptions.RequestException as exc:
      print ("Request failed with message %s" % exc)
      exit(1)
 
    if(args.deviceName):
      try: 
        uid = devices[args.deviceName]
        #Default to showing AC state since a device was specified without a clear reason
        if(not args.showState and not args.showMeasurement):
          args.showState=True 
     
        if(args.showState and uid):
          ac_state = client.pod_ac_state(uid)
          print ("-" * 10, "AC State of %s" % args.deviceName, "-" * 10)
          print (ac_state)
        if(args.showMeasurement and uid):
          pod_measurement = client.pod_measurement(uid)
          print ("-" * 10, "Measurement of %s" % args.deviceName, "-" * 10)
          print (pod_measurement)

        #client.pod_change_ac_state(uid, ac_state, "on", not ac_state['on']) 
      except requests.exceptions.RequestException as exc:
        print ("Request failed with message %s" % exc)
        exit(1)
