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

        time_start = time.time()
        print("Scrapper started")
        scraper.extract(url)
        print("extracted", len(scraper.posts), "ads in", time.time() - time_start, "seconds")

        airbyte_messages = [
                                AirbyteMessage(
                                    type=Type.RECORD,
                                    record=AirbyteRecordMessage(stream="Ads", data=data, emitted_at=int(datetime.now().timestamp()) * 1000),
                                )
                                for data in scraper.posts
                            ]

        yield from airbyte_messages
        """
        for f in filters:
            print("Filter {}".format(f))
            url_parsed = "https://www.lamudi.com.mx/{filter}/?sorting=newest&currency=mxn&page=1".format(filter=f)
            s = requests.get(url_parsed, headers=self.headers)
            s = self.scrape_number_pages(s.text)

            for i in range(0,s):
                airbyte_messages = []
                print("Page {}".format(i+1))
                url_parsed = "https://www.lamudi.com.mx/{filter}/?sorting=newest&currency=mxn&page={page}".format(filter=f,page = i+1)
                s = requests.get(url_parsed, headers=self.headers)
                ls = self.scrape_list_page(s.text)
                ls = self.get_phones(ls)



                yield from airbyte_messages
            """
