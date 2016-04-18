# sensibo-python-sdk
Sensibo Python SDK

Requirements:
requests: http://www.python-requests.org/en/latest/

# Usage

## Basic mode

```
python ./sensibo_client.py -b YOUR_API_KEY
```


## Temperature watcher (maintain inner temperature within range)

```
python ./sensibo_client.py -w -lo 23 -hi 25 -op 17 YOUR_API_KEY
```
