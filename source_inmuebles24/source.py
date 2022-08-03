#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#

from typing import Dict, Generator
from datetime import datetime
import time
import json

from . import Scraper

from airbyte_cdk.sources.streams.core import Stream
from airbyte_cdk.logger import AirbyteLogger
from airbyte_cdk.sources import Source
from airbyte_cdk.models import (
    AirbyteCatalog,
    AirbyteConnectionStatus,
    AirbyteMessage,
    AirbyteRecordMessage,
    AirbyteStream,
    ConfiguredAirbyteCatalog,
    Status,
    Type,
)

class SourceInmuebles24(Source):

    def __init__(self) -> None:
        super().__init__()
        self.headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0"}
        self.agents_phones = {}

    def check(self, logger: AirbyteLogger, config: json) -> AirbyteConnectionStatus:
        try:
            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {str(e)}")

    def discover(self, logger: AirbyteLogger, config: json) -> AirbyteCatalog:
        streams = []

        stream_name = "Properties"

        json_schema = {
          "$schema": "http://json-schema.org/draft-07/schema#",
          "type": "object",
          "properties": {
            "id":       {"type": "string"},
            "title":    {"type": "string"},
            "price":    {"type": "string"},
            "currency": {"type": "string"},
            "type":     {"type": "string"},
            "url":      {"type": "string"},
            "location": {
              "type": "object",
              "properties": {
                  "zona":     {"type": "string"},
                  "ciudad":   {"type": "string"},
                  "provinicia":   {"type": "string"}
              }
            },
            "publisher": {
              "type": "object",
              "properties":{
                  "id":       {"type": "string"},
                  "name":     {"type": "string"},
                  "whatsapp": {"type": "string"},
                  "phone":    {"type": "string"},
                  "cellPhone":{"type": "string"},
              }
            },
            "terreno":      {"type": "integer"},
            "construido":   {"type": "integer"},
            "recamaras":    {"type": "integer"},
            "banios":       {"type": "integer"},
            "garege":       {"type": "integer"},
            "antiguedad":   {"type": "integer"}
          }
        }

        streams.append(AirbyteStream(name=stream_name, json_schema=json_schema))
        return AirbyteCatalog(streams=streams)


    def read(
        self, logger: AirbyteLogger, config: json, catalog: ConfiguredAirbyteCatalog, state: Dict[str, any]
    ) -> Generator[AirbyteMessage, None, None]:

        #Get the filters
        filter = json.loads(config["Filter"])
        print(filter)
        print(type(filter))
        message = config["Message"]

        #Run the scraper
        time_start = time.time()
        print("Scrapper started")
        posts = Scraper.get_postings(filter, message)
        print("extracted", len(posts), "properties in", time.time() - time_start, "seconds")
        #

        #Print the messages
        airbyte_messages = [
            AirbyteMessage(type=Type.RECORD,
                record=AirbyteRecordMessage(stream="Properties", data=post, emitted_at=int(datetime.now().timestamp()) * 1000),
            )
            for post in posts
        ]

        yield from airbyte_messages
