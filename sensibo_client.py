import json
import logging
import requests
import time

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

    def pod_change_ac_state(self, podUid, on, target_temperature, mode, fan_level):
        self._post("/pods/%s/acStates" % podUid,
                json.dumps({'acState': {"on": on, "targetTemperature": target_temperature, "mode": mode, "fanLevel": fan_level}}))

class TemperatureLogger(object):
    def __init__(self, name=None):
        name = name if name else self.__class__.__name__
        self._logger = logging.getLogger(name)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self._logger.addHandler(ch)

    @property
    def logger(self):
        return self._logger

class TemperatureWatcher(object):
    def __init__(self, api_key=None, low_t=23, high_t=25, op_t=17):
        self.run_temperature_sanity(low_t, high_t, op_t)
        self.logger = TemperatureLogger().logger
        # proceed
        self.api_key = api_key
        self.client = SensiboClientAPI(api_key)
        self.low_t = low_t
        self.high_t = high_t
        self.op_t = op_t

    @staticmethod
    def run_temperature_sanity(low_t, high_t, op_t):
        if low_t >= high_t:
            raise ValueError('Low temperature should be lower than high temperature')
        if low_t < op_t:
            raise ValueError('Operation temperature has to be lower or equal to low temperature')
        if op_t > 27:
            raise ValueError('Operation temperature cannot exceed 27C')
        if op_t < 17:
            raise ValueError('Operation temperature cannot be lower than 17C')

    def cleanup(self, reason=None, exc=None):
        exc = 'no exception' if not exc else exc
        self.logger.warning('Cleanup after %r with %r!', reason, exc)

    def poll(self):
        pod_uids = self.client.pod_uids()
        # FIXME: individual pod temperature support
        for pod in pod_uids:
            measurement = self.client.pod_measurement(pod)[0]
            temperature = float(measurement.get('temperature', 0))
            if temperature >= self.high_t:
                self.client.pod_change_ac_state(pod, True, self.op_t, 'cool', 'high')
                self.logger.warning('Turning on AC as %s >= %s', temperature, self.high_t)
            elif temperature <= self.low_t:
                self.logger.warning('Turning off AC as %s <= %s', temperature, self.low_t)
                self.client.pod_change_ac_state(pod, False, self.op_t, 'cool', 'auto')
            else:
                self.logger.warning('Temperature %sC is within range: %s-%sC, noop', temperature,
                               self.low_t, self.high_t)

    def run_forever(self):
        while True:
            try:
                self.poll()
                time.sleep(60)
            except KeyboardInterrupt:
                reason = 'interrupt'
                exc = None
                break
            except Exception as exc:
                reason='exception'
                exc=exc
        self.cleanup(reason=reason, exc=exc)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Sensibo client example parser')
    parser.add_argument('apikey', type = str)
    parser.add_argument('-lo', '--low-temperature', type=int, dest='low_t',
                        help='AC turn off temperature')
    parser.add_argument('-hi', '--high-temperature', type=int, dest='high_t',
                        help='AC turn on temperature')
    parser.add_argument('-op', '--operation-temperature', type=int, dest='op_t',
                        help='AC operation temperature')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-b', '--basic', action='store_true',
                       help='Basic mode, print pods, temperatures and exit')
    group.add_argument('-w', '--watcher', action='store_true',
                       help='Temperature watcher mode, maintain temperature within range')
    args = parser.parse_args()

    if args.basic:
        client = SensiboClientAPI(args.apikey)
        pod_uids = client.pod_uids()
        print ("All pod uids:", ", ".join(pod_uids))
        print ("Pod measurement for first pod", client.pod_measurement(pod_uids[0]))
        last_ac_state = client.pod_ac_state(pod_uids[0])
        print ("Last AC change %(success)s and was caused by %(cause)s" % { 'success': 'was successful' if last_ac_state['status'] == 'Success' else 'failed', 'cause': last_ac_state['reason'] } )
        print ("and set the ac to %s" % str(last_ac_state['acState']))
        print ("Change AC state of %s" % pod_uids[0])
        client.pod_change_ac_state(pod_uids[0], True, 23, 'cool', 'auto')
    elif args.watcher:
        low_t = args.low_t if args.low_t else 23
        high_t = args.high_t if args.high_t else 25
        op_t = args.op_t if args.op_t else 17
        watcher = TemperatureWatcher(api_key=args.apikey, low_t=low_t,
                                     high_t=high_t, op_t=op_t)
        watcher.run_forever()
    else:
        args = parser.parse_args(['-h'])
