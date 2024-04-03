#! /usr/bin/python3
import pprint
import tempfile
from counterpartylib.test import conftest  # this is require near the top to do setup of the test suite
from counterpartylib.test.fixtures.params import DEFAULT_PARAMS as DP
from counterpartylib.test.util_test import CURR_DIR

from counterpartylib.lib import (blocks)


FIXTURE_SQL_FILE = CURR_DIR + '/fixtures/scenarios/parseblock_unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.parseblock_unittest_fixture.db'


def test_parse_block(server_db):
    test_outputs = blocks.parse_block(server_db, DP['default_block_index'], 1420914478)
    outputs = ('44cf374045f44caf86c7b7de61de3e712f4ba3c39523ab95bc68149ef8aede18',
               '9c2c0940e0a2a8f4c6dde1cfd69efe8e3b467fac0950b385554044ab1f863bf5',
               '8875bc0743553317f0c964c01a0b6af4b561646009e19f9324238735e6412adb',
               None)
    try:
        assert outputs == test_outputs
    except AssertionError:
        msg = "expected outputs don't match test_outputs:\noutputs=\n" + pprint.pformat(outputs) + "\ntest_outputs=\n" + pprint.pformat(test_outputs)
        raise AssertionError(msg)
