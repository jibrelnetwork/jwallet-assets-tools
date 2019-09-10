import json
import logging

from confluent_kafka import Consumer
from confluent_kafka.cimpl import Producer

from jwallet_tools.assets_validator.contract import GasValidator


class KafkaAssetValidator:
    """
    Class that processes validation requests from kafka
    """
    in_topic = 'asset_validation_request'
    out_topic = 'asset_validation_response'

    def __init__(self, host, port):
        server_params = {'bootstrap.servers': f'{host}:{port}'}
        consumer_params = {
            'group.id': 'mygroup',
            'auto.offset.reset': 'earliest'
        }
        consumer_params.update(server_params)

        self._consumer = Consumer(consumer_params)
        self._consumer.subscribe([self.in_topic])

        self._producer = Producer(server_params)

        self.logger = logging.getLogger(self.in_topic)

    def process_message(self):
        msg = self._consumer.poll(15.0)
        if msg is None:
            self.logger.warning('No messages')
            return
        if msg.error():
            self.logger.error(f'Consumer error: {msg.error()}')

        self.logger.warning('Process started')

        value = msg.value().decode('utf-8')
        data = json.loads(value)

        validator = GasValidator(node=data.get('node'))
        result = validator(data)

        response = json.dumps({
            'uuid': data.get('uuid'),
            'result': result,
            'message': validator.get_message(),
        })

        self._producer.poll(0)
        self._producer.produce(self.out_topic, response)
        self._producer.flush()
        self.logger.warning('Message processed')

        self._consumer.close()
