"""Methods pertaining to weather data"""
from enum import IntEnum
import json
import logging
from pathlib import Path
import random
import urllib.parse
import time

import requests

#from models.producer import Producer
from producer import Producer

logger = logging.getLogger(__name__)


class Weather(Producer):
    """Defines a simulated weather model"""

    status = IntEnum(
        "status", 
        "sunny partly_cloudy cloudy windy precipitation", 
        start=0
    )

    rest_proxy_url = "http://localhost:8082"

    key_schema = None
    value_schema = None

    winter_months = set((0, 1, 2, 3, 10, 11))
    summer_months = set((6, 7, 8))

    def __init__(self, month):
        
        super().__init__(
            "com.udacity.events.weather",
            key_schema=Weather.key_schema,
            value_schema=Weather.value_schema,
            num_partitions=10,
            num_replicas=3,
        )

        self.status = Weather.status.sunny
        self.temp = 70.0
        if month in Weather.winter_months:
            self.temp = 40.0
        elif month in Weather.summer_months:
            self.temp = 85.0

        if Weather.key_schema is None:
            with open(f"{Path(__file__).parents[0]}/schemas/weather_key.json") as f:
                Weather.key_schema = json.dumps(json.load(f))

        if Weather.value_schema is None:
            with open(f"{Path(__file__).parents[0]}/schemas/weather_value.json") as f:
                Weather.value_schema = json.dumps(json.load(f))
        
        #print(json.dumps(Weather.value_schema))
        #print(Weather.key_schema)
        

    def _set_weather(self, month):
        """Returns the current weather"""
        mode = 0.0
        if month in Weather.winter_months:
            mode = -1.0
        elif month in Weather.summer_months:
            mode = 1.0
        self.temp += min(max(-20.0, random.triangular(-10.0, 10.0, mode)), 100.0)
        self.status = random.choice(list(Weather.status))

    def run(self, month):
        """Sends weather data to kafka topic via REST proxy"""
        self._set_weather(month)
        
        try:
            resp = requests.post(
                f"{Weather.rest_proxy_url}/topics/{self.topic_name}",
                headers={
                    "Content-Type": "application/vnd.kafka.avro.v2+json",
                    "Accept": "application/vnd.kafka.v2+json"},
                data=json.dumps(
                    {
                    "value_schema": Weather.value_schema,
                    "key_schema": Weather.key_schema,
                    "records": [
                        {
                            "key": self.time_millis(),
                            "value" : {
                                "temperature": self.temp,
                                "status": str(self.status)
                            }
                        }
                    ]
                    }
                )
            )
            return
        
            resp.raise_for_status()
            
            logger.debug(
                "sent weather data to kafka, temp: %s, status: %s",
                self.temp,
                self.status.name,
            )
            
        except Exception as e:
            print(e)
            logger.info("weather kafka proxy integration incomplete - skipping")
            raise
            
