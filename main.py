#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_inmuebles24 import SourceInmuebles24

if __name__ == "__main__":
    source = SourceInmuebles24()
    launch(source, sys.argv[1:])
