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
  
def tempFromMeasurements(measurement):
    if (args.unitC):
      return (str(measurement["temperature"]) + 'C' )
    elif (args.unitF):
      return (str(round(measurement["temperature"]*(9/5)+32,1)) + 'F')

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Sensibo client example parser')
    parser.add_argument('apikey', type = str, help='Obtain from https://home.sensibo.com/me/api')
    parser.add_argument('--deviceName', type = str, help='Device name')
    parser.add_argument('--allDevices', action='store_true', help='Query all devices')
    parser.add_argument('--showState', action='store_true',help='Display the AC state')
    parser.add_argument('--showMeasurement', action='store_true',help='Display the sensor measurements')
    parser.add_argument('--showTempMeasurement', action='store_true',help='Display the sensor temperature')
    parser.add_argument('--unitF', action='store_true',help='Use Fahrenheit')
    parser.add_argument('--unitC', action='store_true',help='Use Celsius')
    args = parser.parse_args()
    #print(args)
    if (not args.unitF and not args.unitC):
      args.unitC=True 

    client = SensiboClientAPI(args.apikey)
    try:
      devices = client.devices()
      if(not args.deviceName and not args.allDevices):
        print ("-" * 10, "devices", "-" * 10)
        print (devices)
    except requests.exceptions.RequestException as exc:
      print ("Request failed with message %s" % exc)
      devices = {'living room A/C': 'ntZFS9SF', 'bedroom A/C': 'wwyyJdeY', "Megan's A/C": 'f3uEc9GG'}
      #exit(1)
 
    if(args.deviceName and not args.allDevices):
      uidList = [devices[args.deviceName]]
      deviceNameByUID = {devices[args.deviceName]:args.deviceName}
    elif(args.allDevices):
      uidList = devices.values()
      deviceNameByUID = {v:k for k,v in devices.items()}
    else:
      uidList = False

    #A specific device or all devices were requested
    if (uidList): 
      #Default to showing AC state since no particular information request was given
      if(not args.showState and not args.showMeasurement and not args.showTempMeasurement):
        args.showState=True 
      
      try: 
        for uid in uidList:
          #print ("UID {}".format(uid))
          #continue 
          if(args.showState):
            ac_state = client.pod_ac_state(uid)
            print ("-" * 10, "AC State of %s" % deviceNameByUID[uid], "-" * 10)
            print (ac_state)
          if(args.showMeasurement or args.showTempMeasurement):
            pod_measurement = client.pod_measurement(uid)
          if(args.showMeasurement):
            print ("-" * 10, "Measurement of %s" % deviceNameByUID[uid], "-" * 10)
            print (pod_measurement)
          if(args.showTempMeasurement):
            print ("-" * 10, "Temperature in %s" % deviceNameByUID[uid], "-" * 10)
            print (tempFromMeasurements(pod_measurement[0]))

          #client.pod_change_ac_state(uid, ac_state, "on", not ac_state['on']) 
      except requests.exceptions.RequestException as exc:
        print ("Request failed with message %s" % exc)
        exit(1)
