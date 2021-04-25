# ZKConnect

ZK Connect is a python micro-service designed to work as a client to relay real-time attendance data from ZK Teco devices to an external API. It is designed to run using a service like Supervisor. I wrote it to work alongside with Laravel applications built at my workplace.

### Requirements

- python >= 3.5
- pyzk == 0.9
- requests == 2.25.1
- pyyaml == 5.4.1

### Supported Devices

This script uses [pyzk](https://github.com/fananimi/pyzk) library to communicate with devices, hence it should support any device supported by pyzk. However, it is explicitly tested with ZKTeco F18 and K40 models. If you get it working with more devices, let me know.

## Usage

### Dependency Install

After creating and activating a virtual environment for the script, install the required libraries by running:

```bash
pip install -r requirements.txt
```

### Config File

A `config.example.yaml` file is provided in this repository. Rename/create a new one as `config.yaml` and fill up following keys:

```yaml
device:
  host: XXX.XXX.XXX.XXX # your device's ip address
  port: 4370 # usually 4370 is used by most of the devices
endpoint: http://my-app.test/log # a post API route to your app
transmission: true # whether or not to transmit data to API, useful for debugging purpose
log:
  filename: transaction # name of log file
  split: true # splits log file for each day if enabled, else writes into one file
```

### Running

After configuring, you can run `python connect.py` to start sending realtime attendance log to your application. The request payload is:

```json
{
  "device_user_id": 21,
  "timestamp": "2021-02-17 18:23:00"
}
```

The server response should contain two keys:

```
{
  "log": {...}, // the saved object
  "message": "A response message"
}
```

> Note: You should use a service like Supervisor to keep the script running and restarting automatically in case of any exception. An example supervisor config file is also provided.


### Debugging

The script keeps all necessary log information within the directory which may come handy for debugging. The log files can be split into several files for each day or can be written into one file. See the [Config File](#config-file) section for configuration.


### Known Issues

The script can detect any disruption in connectivity and hence exits so that supervisor can rerun the script reconnecting to the device. The reconnection attempt might take a few seconds and during this time nothing will be transmitted.
