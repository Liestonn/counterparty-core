#! /usr/bin/python3
import pprint
import tempfile

from counterpartylib.lib import blocks
from counterpartylib.test import (
    conftest,  # noqa: F401
)

# this is require near the top to do setup of the test suite
from counterpartylib.test.fixtures.params import DEFAULT_PARAMS as DP
from counterpartylib.test.util_test import CURR_DIR

FIXTURE_SQL_FILE = CURR_DIR + "/fixtures/scenarios/parseblock_unittest_fixture.sql"
FIXTURE_DB = tempfile.gettempdir() + "/fixtures.parseblock_unittest_fixture.db"


def test_parse_block(server_db):
    test_outputs = blocks.parse_block(server_db, DP["default_block_index"], 1420914478)
    outputs = (
        "44cf374045f44caf86c7b7de61de3e712f4ba3c39523ab95bc68149ef8aede18",
        "9c2c0940e0a2a8f4c6dde1cfd69efe8e3b467fac0950b385554044ab1f863bf5",
        "90ee6aa095b1ba5d16e9902c71dcd0c6fd18550569610863b1c1c57632c1a0f7",
        None,
    )
    try:
        assert outputs == test_outputs
    except AssertionError:
        msg = (
            "expected outputs don't match test_outputs:\noutputs=\n"
            + pprint.pformat(outputs)
            + "\ntest_outputs=\n"
            + pprint.pformat(test_outputs)
        )
        raise AssertionError(msg)  # noqa: B904
