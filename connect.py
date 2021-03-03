#!/usr/bin/python3

import logging
import os
from pathlib import Path

import requests
from yaml import Loader, load
from zk import ZK
from zk.exception import ZKError, ZKErrorConnection, ZKNetworkError


class ZkConnect:
    
    def __init__(self, host, port, endpoint, transmission=True):
        """
        Connect to a ZK Teco device and monitor real-time data.
        
        :param host: The public/private IP address of ZK Teco device
        :param port: The port of ZK Teco device, usually 4370
        :param endpoint: The API endpoint of an external service, where the client will transmit real-time data
        :param transmission: Toggle the transmission of real-time data, True by default
        """
        try:
            self.host = host
            self.port = port
            self.endpoint = endpoint
            self.transmission = transmission
            self.connection = None
            self._connect()
        except (ZKNetworkError, ZKErrorConnection, ZKError) as error:
            logging.error(error)
        except Exception as error:
            logging.error(error)
    
    def _connect(self, reconnect=False):
        """
        Attempt to establish a connection to a ZK Teco device.
        
        :param reconnect: Whether it is an attempt to reconnect
        """
        zk = ZK(ip=self.host, port=self.port, verbose=True)
        self.connection = zk.connect()
        if reconnect:
            logging.debug('initiating reconnection...')
        logging.info(
            'connection established: host: {}, port: {}'.format(self.host, self.port))
    
    def _transmit(self, data):
        """
        Transmit real-time data to the specified endpoint.
        
        :param data: The HTTP payload
        :return: requests.models.Response
        """
        try:
            logging.debug('Initiating transmission for ' + str(data))
            response = requests.post(self.endpoint, data)
            response.raise_for_status()
            jsonResponse = response.json()
            logging.debug("HTTP Response: {}, data: {}".format(jsonResponse.get('message'), jsonResponse.get('log')))
            return response
        except requests.exceptions.HTTPError as error:
            logging.error("HTTP Error: {}, message: {}, data: {}".format(error, error.response.text, str(data)))
        except Exception as error:
            logging.error("Error: {}, data: {}".format(error, str(data)))
        finally:
            if not self.connection.is_enabled:
                self.connection.enable_device()
    
    def _healthcheck(self):
        """
        Check connection health, in case of failure attempt re-establishment.
        """
        try:
            # This should ensure that the device is still connected
            print('Getting device time: {}'.format(self.connection.get_time()))
        except Exception as error:
            logging.error(error)
            self._connect(reconnect=True)
    
    def monitor(self):
        """
        Start monitoring and transmitting real-time data.
        """
        if not self.connection:
            raise ZKErrorConnection('Connection is not established!')
        
        for log in self.connection.live_capture():
            if log is None:
                self._healthcheck()
            else:
                if self.transmission:
                    self._transmit({
                        'device_user_id': log.user_id,
                        'timestamp': log.timestamp
                    })
                else:
                    print('Received data: {}'.format(log))
    
    def disconnect(self):
        """
        Disconnect from the connected ZK Teco device.
        """
        self.connection.disconnect()


class ParseConfig:
    
    @classmethod
    def _validate(cls, config):
        """
        Validate the dictionary structure of config.
        
        :param config: The dictionary containing device config and endpoint
        """
        if not all(key in config.keys() for key in ['device', 'endpoint']):
            raise Exception('device or endpoint key is missing!')
        
        device = config.get('device')
        if not all(key in device.keys() for key in ['host', 'port']):
            raise Exception('host or port key is missing in device!')
        if None in device.values():
            raise Exception('host or port key is empty in device!')
        
        if config.get('endpoint') is None:
            raise Exception('endpoint cannot be empty!')
        
        if 'transmission' in config.keys() and type(config.get('transmission')) is not bool:
            raise Exception('transmission key must have to be either true or false!')
    
    @classmethod
    def parse(cls, stream):
        """
        Parse a yaml file to a dictionary.
        
        :param stream: The stream of data
        :return: dict
        """
        config = load(stream, Loader=Loader)
        cls._validate(config)
        return config


def init():
    """
    Initiate the ZK Teco monitoring client.
    """
    try:
        logging.basicConfig(
            format='%(asctime)s/%(name)s/%(levelname)s/%(lineno)d: %(message)s',
            filename='transaction_log.txt',
            level=logging.DEBUG
        )
        configPath = Path(os.path.abspath(__file__)).parent / 'config.yaml'
        stream = open(configPath, 'r')
        config = ParseConfig.parse(stream)
        device = config.get('device')
        endpoint = config.get('endpoint')
        transmission = config.get(
            'transmission') if 'transmission' in config.keys() else True
        zk = ZkConnect(
            host=device.get('host'),
            port=device.get('port'),
            endpoint=endpoint,
            transmission=transmission
        )
        zk.monitor()
    except Exception as e:
        print(e)
        logging.warning(e)
        # Restart process
        # init()


if __name__ == "__main__":
    init()
