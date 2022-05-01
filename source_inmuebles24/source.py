#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#

from typing import Dict, Generator
from datetime import datetime
import time
import json

from . import scraper

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
            # Not Implemented

            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {str(e)}")

    def discover(self, logger: AirbyteLogger, config: json) -> AirbyteCatalog:
        streams = []

        stream_name = "Ads"
        json_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "destacado": {"type": "string"},
                "title": {"type": "string"},
                "zona": {"type": "string"},
                "ciudad": {"type": "number"},
                "provincia": {"type": "string"},
                "price": {"type": "string"},
                "currency": {"type": "string"},
                "terreno": {"type": "string"},
                "recamaras": {"type": "string"},
                "banios": {"type": "string"},
                "garage": {"type": "string"},
                "publisher": {"type": "string"},
                "whatsapp": {"type": "string"},
                "phone": {"type": "string"},
                "cellPhone": {"type": "string"},
                "url": {"type": "string"},
            },
        }

        streams.append(AirbyteStream(name=stream_name, json_schema=json_schema))
        return AirbyteCatalog(streams=streams)


    def read(
        self, logger: AirbyteLogger, config: json, catalog: ConfiguredAirbyteCatalog, state: Dict[str, any]
    ) -> Generator[AirbyteMessage, None, None]:

        filter_url = config["Filter"]
        url = scraper.parse_url(filter_url)

        message = config["Message"]

        time_start = time.time()
        print("Scrapper started")
        scraper.extract(url, message)
        print("extracted", len(scraper.posts), "ads in", time.time() - time_start, "seconds")

        airbyte_messages = [
                                AirbyteMessage(
                                    type=Type.RECORD,
                                    record=AirbyteRecordMessage(stream="Ads", data=data, emitted_at=int(datetime.now().timestamp()) * 1000),
                                )
                                for data in scraper.posts
                            ]

        with open('examples.json', "w", encoding='UTF-8') as f:
            json.dump(scraper.sending, f, indent=4, ensure_ascii=False)

        yield from airbyte_messages
