"""Variables prefixed with `DEFAULT` should be able to be overridden by
configuration file and command‐line arguments."""

UNIT = 100000000  # The same across assets.


# Semantic Version
__version__ = "10.1.2"  # for hatch
VERSION_STRING = __version__
version = VERSION_STRING.split("-")[0].split(".")
VERSION_MAJOR = int(version[0])
VERSION_MINOR = int(version[1])
VERSION_REVISION = int(version[2])
VERSION_PRE_RELEASE = "-".join(VERSION_STRING.split("-")[1:])

ADDRINDEXRS_VERSION = "0.4.6"

# When updating to a new verion, we are making a rollback if major version changes.
# If minor version changes and if needed, we are making a reparse from a given block.
# Fo example:
# NEED_REPARSE_IF_MINOR_IS_LESS_THAN = (1, 800000)
# means that we need to reparse from block 800000 if database minor version is less than 1
NEED_REPARSE_IF_MINOR_IS_LESS_THAN = (1, 835500)
NEED_REPARSE_IF_MINOR_IS_LESS_THAN_TESTNET = None
# Counterparty protocol
TXTYPE_FORMAT = ">I"
SHORT_TXTYPE_FORMAT = "B"

TWO_WEEKS = 2 * 7 * 24 * 3600
MAX_EXPIRATION = 4 * 2016  # Two months

MEMPOOL_BLOCK_HASH = "mempool"
MEMPOOL_BLOCK_INDEX = 9999999


# SQLite3
MAX_INT = 2**63 - 1


# Bitcoin Core
OP_RETURN_MAX_SIZE = 80  # bytes


# Currency agnosticism
BTC = "BTC"
XCP = "XCP"

BTC_NAME = "Bitcoin"
XCP_NAME = "Counterparty"
APP_NAME = XCP_NAME.lower()
FULL_APP_NAME = "Counterparty Core"
LOGGER_NAME = APP_NAME

DEFAULT_API_PORT_REGTEST = 24000
DEFAULT_API_PORT_TESTNET = 14000
DEFAULT_API_PORT = 4000

DEFAULT_RPC_PORT_REGTEST = 24100
DEFAULT_RPC_PORT_TESTNET = 14100
DEFAULT_RPC_PORT = 4100

DEFAULT_BACKEND_PORT_REGTEST = 28332
DEFAULT_BACKEND_PORT_TESTNET = 18332
DEFAULT_BACKEND_PORT = 8332

DEFAULT_INDEXD_PORT_REGTEST = 28432
DEFAULT_INDEXD_PORT_TESTNET = 18432
DEFAULT_INDEXD_PORT = 8432

UNSPENDABLE_REGTEST = "mvCounterpartyXXXXXXXXXXXXXXW24Hef"
UNSPENDABLE_TESTNET = "mvCounterpartyXXXXXXXXXXXXXXW24Hef"
UNSPENDABLE_MAINNET = "1CounterpartyXXXXXXXXXXXXXXXUWLpVr"

ADDRESSVERSION_TESTNET = b"\x6f"
P2SH_ADDRESSVERSION_TESTNET = b"\xc4"
PRIVATEKEY_VERSION_TESTNET = b"\xef"
ADDRESSVERSION_MAINNET = b"\x00"
P2SH_ADDRESSVERSION_MAINNET = b"\x05"
PRIVATEKEY_VERSION_MAINNET = b"\x80"
ADDRESSVERSION_REGTEST = b"\x6f"
P2SH_ADDRESSVERSION_REGTEST = b"\xc4"
PRIVATEKEY_VERSION_REGTEST = b"\xef"
MAGIC_BYTES_TESTNET = b"\xfa\xbf\xb5\xda"  # For bip-0010
MAGIC_BYTES_MAINNET = b"\xf9\xbe\xb4\xd9"  # For bip-0010
MAGIC_BYTES_REGTEST = b"\xda\xb5\xbf\xfa"

BLOCK_FIRST_TESTNET_TESTCOIN = 310000
BURN_START_TESTNET_TESTCOIN = 310000
BURN_END_TESTNET_TESTCOIN = 4017708  # Fifty years, at ten minutes per block.

BLOCK_FIRST_TESTNET = 310000
BLOCK_FIRST_TESTNET_HASH = "000000001f605ec6ee8d2c0d21bf3d3ded0a31ca837acc98893876213828989d"
BURN_START_TESTNET = 310000
BURN_END_TESTNET = 4017708  # Fifty years, at ten minutes per block.

BLOCK_FIRST_MAINNET_TESTCOIN = 278270
BURN_START_MAINNET_TESTCOIN = 278310
BURN_END_MAINNET_TESTCOIN = 2500000  # A long time.

BLOCK_FIRST_MAINNET = 278270
BLOCK_FIRST_MAINNET_HASH = "00000000000000017bac9a8e85660ad348050c789922d5f8fe544d473368be1a"
BURN_START_MAINNET = 278310
BURN_END_MAINNET = 283810

BLOCK_FIRST_REGTEST = 0
BLOCK_FIRST_REGTEST_HASH = "0f9188f13cb7b2c71f2a335e3a4fc328bf5beb436012afca590b1a11466e2206"
BURN_START_REGTEST = 101
BURN_END_REGTEST = 150000000

BLOCK_FIRST_REGTEST_TESTCOIN = 0
BURN_START_REGTEST_TESTCOIN = 101
BURN_END_REGTEST_TESTCOIN = 150

# Protocol defaults
# NOTE: If the DUST_SIZE constants are changed, they MUST also be changed in counterblockd/lib/config.py as well
DEFAULT_REGULAR_DUST_SIZE = 546  # TODO: Revisit when dust size is adjusted in bitcoin core
DEFAULT_MULTISIG_DUST_SIZE = 1000  # OMFG: We been overpaying by 10x for years (7800!=780) <https://bitcointalk.org/index.php?topic=528023.msg7469941#msg7469941>
DEFAULT_OP_RETURN_VALUE = 0
DEFAULT_FEE_PER_KB_ESTIMATE_SMART = 1024
DEFAULT_FEE_PER_KB = 25000  # sane/low default, also used as minimum when estimated fee is used
ESTIMATE_FEE_PER_KB = (
    True  # when True will use `estimatesmartfee` from bitcoind instead of DEFAULT_FEE_PER_KB
)
ESTIMATE_FEE_CONF_TARGET = 3
ESTIMATE_FEE_MODE = "CONSERVATIVE"

# UI defaults
DEFAULT_FEE_FRACTION_REQUIRED = 0.009  # 0.90%
DEFAULT_FEE_FRACTION_PROVIDED = 0.01  # 1.00%


DEFAULT_REQUESTS_TIMEOUT = 20  # 20 seconds
DEFAULT_RPC_BATCH_SIZE = 20  # A 1 MB block can hold about 4200 transactions.

# Custom exit codes
EXITCODE_UPDATE_REQUIRED = 5

BACKEND_RAW_TRANSACTIONS_CACHE_SIZE = 20000
BACKEND_RPC_BATCH_NUM_WORKERS = 6

DEFAULT_UTXO_LOCKS_MAX_ADDRESSES = 1000
DEFAULT_UTXO_LOCKS_MAX_AGE = 3.0  # in seconds

ADDRESS_OPTION_REQUIRE_MEMO = 1
ADDRESS_OPTION_MAX_VALUE = ADDRESS_OPTION_REQUIRE_MEMO  # Or list of all the address options
OLD_STYLE_API = True

API_LIMIT_ROWS = 1000

MPMA_LIMIT = 1000

PROTOCOL_CHANGES_URL = "https://counterparty.io/protocol_changes.json"
BOOTSTRAP_URL_MAINNET = "https://bootstrap.counterparty.io/counterparty.latest.tar.gz"
BOOTSTRAP_URL_MAINNET_SIG = "https://bootstrap.counterparty.io/counterparty.latest.sig"
BOOTSTRAP_URL_TESTNET = "https://bootstrap.counterparty.io/counterparty-testnet.latest.tar.gz"
BOOTSTRAP_URL_TESTNET_SIG = "https://bootstrap.counterparty.io/counterparty-testnet.latest.sig"

API_MAX_LOG_SIZE = (
    10 * 1024 * 1024
)  # max log size of 20 MB before rotation (make configurable later)
API_MAX_LOG_COUNT = 10

NO_TELEMETRY = False
TELEMETRY_INTERVAL = 5 * 60
INFLUX_DB_URL = "http://telemetry.counterparty.io:8086"
INFLUX_DB_TOKEN = (
    "7iViyy6TEVwmpH-YPE7shO36fzfGsyVYm0DC2tuLv0ZDTLp5uqRTW2Zv9IBcujF5zQRV6mauGdb1W3n7UrUu6A=="  # noqa: S105
)
INFLUX_DB_ORG = "counterparty"
INFLUX_DB_BUCKET = "node-telemetry"
