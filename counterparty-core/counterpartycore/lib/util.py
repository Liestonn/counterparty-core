import binascii
import collections
import decimal
import hashlib
import itertools
import json
import logging
import os
import random
import re
import shutil
import sys
import tempfile
import threading
import time
from operator import itemgetter

import gnupg
import requests

from counterpartycore.lib import config, exceptions

logger = logging.getLogger(config.LOGGER_NAME)

CURRENT_BLOCK_INDEX = None

D = decimal.Decimal
B26_DIGITS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# subasset contain only characters a-zA-Z0-9.-_@!
SUBASSET_DIGITS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_@!"
SUBASSET_REVERSE = {
    "a": 1,
    "b": 2,
    "c": 3,
    "d": 4,
    "e": 5,
    "f": 6,
    "g": 7,
    "h": 8,
    "i": 9,
    "j": 10,
    "k": 11,
    "l": 12,
    "m": 13,
    "n": 14,
    "o": 15,
    "p": 16,
    "q": 17,
    "r": 18,
    "s": 19,
    "t": 20,
    "u": 21,
    "v": 22,
    "w": 23,
    "x": 24,
    "y": 25,
    "z": 26,
    "A": 27,
    "B": 28,
    "C": 29,
    "D": 30,
    "E": 31,
    "F": 32,
    "G": 33,
    "H": 34,
    "I": 35,
    "J": 36,
    "K": 37,
    "L": 38,
    "M": 39,
    "N": 40,
    "O": 41,
    "P": 42,
    "Q": 43,
    "R": 44,
    "S": 45,
    "T": 46,
    "U": 47,
    "V": 48,
    "W": 49,
    "X": 50,
    "Y": 51,
    "Z": 52,
    "0": 53,
    "1": 54,
    "2": 55,
    "3": 56,
    "4": 57,
    "5": 58,
    "6": 59,
    "7": 60,
    "8": 61,
    "9": 62,
    ".": 63,
    "-": 64,
    "_": 65,
    "@": 66,
    "!": 67,
}

# Obsolete in Python 3.4, with enum module.
BET_TYPE_NAME = {0: "BullCFD", 1: "BearCFD", 2: "Equal", 3: "NotEqual"}
BET_TYPE_ID = {"BullCFD": 0, "BearCFD": 1, "Equal": 2, "NotEqual": 3}

json_dump = lambda x: json.dumps(x, sort_keys=True, indent=4)  # noqa: E731
json_print = lambda x: print(json_dump(x))  # noqa: E731


class RPCError(Exception):
    pass


# TODO: Move to `util_test.py`.
# TODO: This doesn’t timeout properly. (If server hangs, then unhangs, no result.)
def api(method, params):
    """Poll API via JSON-RPC."""
    headers = {"content-type": "application/json"}
    payload = {
        "method": method,
        "params": params,
        "jsonrpc": "2.0",
        "id": 0,
    }

    response = requests.post(config.RPC, data=json.dumps(payload), headers=headers, timeout=10)
    if response == None:  # noqa: E711
        raise RPCError(f"Cannot communicate with {config.XCP_NAME} server.")
    elif response.status_code != 200:
        if response.status_code == 500:
            raise RPCError("Malformed API call.")
        else:
            raise RPCError(str(response.status_code) + " " + response.reason)

    response_json = response.json()
    if "error" not in response_json.keys() or response_json["error"] == None:  # noqa: E711
        try:
            return response_json["result"]
        except KeyError:
            raise RPCError(response_json)  # noqa: B904
    else:
        raise RPCError(f"{response_json['error']['message']} ({response_json['error']['code']})")


def chunkify(l, n):  # noqa: E741
    n = max(1, n)
    return [l[i : i + n] for i in range(0, len(l), n)]


def flat(z):
    return [x for x in z]


def py34_tuple_append(first_elem, t):
    # Had to do it this way to support python 3.4, if we start
    # using the 3.5 runtime this can be replaced by:
    #  (first_elem, *t)

    l = list(t)  # noqa: E741
    l.insert(0, first_elem)
    return tuple(l)


def accumulate(l):  # noqa: E741
    it = itertools.groupby(l, itemgetter(0))
    for key, subiter in it:
        yield key, sum(item[1] for item in subiter)


def date_passed(date):
    """Check if the date has already passed."""
    return date <= int(time.time())


# checks and validates subassets (PARENT.SUBASSET)
#   throws exceptions for assset or subasset names with invalid syntax
#   returns (None, None) if the asset is not a subasset name
def parse_subasset_from_asset_name(asset):
    subasset_parent = None
    subasset_child = None
    subasset_longname = None
    chunks = asset.split(".", 1)
    if len(chunks) == 2:
        subasset_parent = chunks[0]
        subasset_child = chunks[1]
        subasset_longname = asset

        # validate parent asset
        validate_subasset_parent_name(subasset_parent)

        # validate child asset
        validate_subasset_longname(subasset_longname, subasset_child)

    return (subasset_parent, subasset_longname)


# throws exceptions for invalid subasset names
def validate_subasset_longname(subasset_longname, subasset_child=None):
    if subasset_child is None:
        chunks = subasset_longname.split(".", 1)
        if len(chunks) == 2:
            subasset_child = chunks[1]
        else:
            subasset_child = ""

    if len(subasset_child) < 1:
        raise exceptions.AssetNameError("subasset name too short")
    if len(subasset_longname) > 250:
        raise exceptions.AssetNameError("subasset name too long")

    # can't start with period, can't have consecutive periods, can't contain anything not in SUBASSET_DIGITS
    previous_digit = "."
    for c in subasset_child:
        if c not in SUBASSET_DIGITS:
            raise exceptions.AssetNameError("subasset name contains invalid character:", c)
        if c == "." and previous_digit == ".":
            raise exceptions.AssetNameError("subasset name contains consecutive periods")
        previous_digit = c
    if previous_digit == ".":
        raise exceptions.AssetNameError("subasset name ends with a period")

    return True


# throws exceptions for invalid subasset names
def validate_subasset_parent_name(asset_name):
    if asset_name == config.BTC:
        raise exceptions.AssetNameError(f"parent asset cannot be {config.BTC}")
    if asset_name == config.XCP:
        raise exceptions.AssetNameError(f"parent asset cannot be {config.XCP}")
    if len(asset_name) < 4:
        raise exceptions.AssetNameError("parent asset name too short")
    if len(asset_name) >= 13:
        raise exceptions.AssetNameError("parent asset name too long")
    if asset_name[0] == "A":
        raise exceptions.AssetNameError("parent asset name starts with ‘A’")
    for c in asset_name:
        if c not in B26_DIGITS:
            raise exceptions.AssetNameError("parent asset name contains invalid character:", c)
    return True


def compact_subasset_longname(string):
    """Compacts a subasset name string into an array of bytes to save space using a base68 encoding scheme.
    Assumes all characters provided belong to SUBASSET_DIGITS.
    """
    name_int = 0
    for i, c in enumerate(string[::-1]):
        name_int += (68**i) * SUBASSET_REVERSE[c]
    return name_int.to_bytes((name_int.bit_length() + 7) // 8, byteorder="big")


def expand_subasset_longname(raw_bytes):
    """Expands an array of bytes into a subasset name string."""
    integer = int.from_bytes(raw_bytes, byteorder="big")
    if integer == 0:
        return ""
    ret = ""
    while integer != 0:
        ret = SUBASSET_DIGITS[integer % 68 - 1] + ret
        integer //= 68
    return ret


def generate_random_asset():
    # Standard pseudo-random generators are suitable for our purpose.
    return "A" + str(random.randint(26**12 + 1, 2**64 - 1))  # nosec B311  # noqa: S311


def parse_options_from_string(string):
    """Parse options integer from string, if exists."""
    string_list = string.split(" ")
    if len(string_list) == 2:
        try:
            options = int(string_list.pop())
        except:  # noqa: E722
            raise exceptions.OptionsError("options not an integer")  # noqa: B904
        return options
    else:
        return False


def validate_address_options(options):
    """Ensure the options are all valid and in range."""
    if (options > config.MAX_INT) or (options < 0):
        raise exceptions.OptionsError("options integer overflow")
    elif options > config.ADDRESS_OPTION_MAX_VALUE:
        raise exceptions.OptionsError("options out of range")
    elif not active_options(config.ADDRESS_OPTION_MAX_VALUE, options):
        raise exceptions.OptionsError("options not possible")


def active_options(config, options):
    """Checks if options active in some given config."""
    return config & options == options


class QuantityError(Exception):
    pass


def value_input(quantity, asset, divisible):
    if asset == "leverage":
        return round(quantity)

    if asset in ("value", "fraction", "price", "odds"):
        return float(quantity)  # TODO: Float?!

    if divisible:
        quantity = D(quantity) * config.UNIT
        if quantity == quantity.to_integral():
            return int(quantity)
        else:
            raise QuantityError("Divisible assets have only eight decimal places of precision.")
    else:
        quantity = D(quantity)
        if quantity != round(quantity):
            raise QuantityError("Fractional quantities of indivisible assets.")
        return round(quantity)


def value_output(quantity, asset, divisible):
    def norm(num, places):
        """Round only if necessary."""
        num = round(num, places)
        fmt = "{:." + str(places) + "f}"
        # pylint: disable=C0209
        num = fmt.format(num)
        return num.rstrip("0") + "0" if num.rstrip("0")[-1] == "." else num.rstrip("0")

    if asset == "fraction":
        return str(norm(D(quantity) * D(100), 6)) + "%"

    if asset in ("leverage", "value", "price", "odds"):
        return norm(quantity, 6)

    if divisible:
        quantity = D(quantity) / D(config.UNIT)
        if quantity == quantity.to_integral():
            return str(quantity) + ".0"  # For divisible assets, display the decimal point.
        else:
            return norm(quantity, 8)
    else:
        quantity = D(quantity)
        if quantity != round(quantity):
            raise QuantityError("Fractional quantities of indivisible assets.")
        return round(quantity)


class GetURLError(Exception):
    pass


def get_url(url, abort_on_error=False, is_json=True, fetch_timeout=5):
    """Fetch URL using requests.get."""
    try:
        r = requests.get(url, timeout=fetch_timeout)
    except Exception as e:
        raise GetURLError(f"Got get_url request error: {e}")  # noqa: B904
    else:
        if r.status_code != 200 and abort_on_error:
            raise GetURLError(
                f"Bad status code returned: '{r.status_code}'. result body: '{r.text}'."
            )
        result = json.loads(r.text) if is_json else r.text
    return result


def dhash(text):
    if not isinstance(text, bytes):
        text = bytes(str(text), "utf-8")

    return hashlib.sha256(hashlib.sha256(text).digest()).digest()


def dhash_string(text):
    return binascii.hexlify(dhash(text)).decode()


# Why on Earth does `binascii.hexlify()` return bytes?!
def hexlify(x):
    """Return the hexadecimal representation of the binary data. Decode from ASCII to UTF-8."""
    return binascii.hexlify(x).decode("ascii")


def unhexlify(hex_string):
    return binascii.unhexlify(bytes(hex_string, "utf-8"))


ID_SEPARATOR = "_"


def make_id(hash_1, hash_2):
    return hash_1 + ID_SEPARATOR + hash_2


def parse_id(match_id):
    assert match_id[64] == ID_SEPARATOR
    return match_id[:64], match_id[65:]  # UTF-8 encoding means that the indices are doubled.


def sizeof(v):
    if isinstance(v, dict) or isinstance(v, DictCache):
        s = 0
        for dk, dv in v.items():
            s += sizeof(dk)
            s += sizeof(dv)

        return s
    else:
        return sys.getsizeof(v)


class DictCache:
    """Threadsafe FIFO dict cache"""

    def __init__(self, size=100):
        if int(size) < 1:
            raise AttributeError("size < 1 or not a number")
        self.size = size
        self.dict = collections.OrderedDict()
        self.lock = threading.Lock()

    def __getitem__(self, key):
        with self.lock:
            return self.dict[key]

    def __setitem__(self, key, value):
        with self.lock:
            while len(self.dict) >= self.size:
                self.dict.popitem(last=False)
            self.dict[key] = value

    def __delitem__(self, key):
        with self.lock:
            del self.dict[key]

    def __len__(self):
        with self.lock:
            return len(self.dict)

    def __contains__(self, key):
        with self.lock:
            return key in self.dict

    def refresh(self, key):
        with self.lock:
            self.dict.move_to_end(key, last=True)


URL_USERNAMEPASS_REGEX = re.compile(".+://(.+)@")


def clean_url_for_log(url):
    m = URL_USERNAMEPASS_REGEX.match(url)
    if m and m.group(1):
        url = url.replace(m.group(1), "XXXXXXXX")

    return url


def verify_signature(public_key_data, signature_path, snapshot_path):
    temp_dir = tempfile.mkdtemp()
    verified = False

    try:
        gpg = gnupg.GPG(gnupghome=temp_dir)

        gpg.import_keys(public_key_data)

        with open(signature_path, "rb") as s:
            verified = gpg.verify_file(s, snapshot_path, close_file=False)

    finally:
        shutil.rmtree(temp_dir)

    return verified


# ORACLES
def satoshirate_to_fiat(satoshirate):
    return round(satoshirate / 100.0, 2)


#############################
#     PROTOCOL CHANGES      #
#############################

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
with open(CURR_DIR + "/../protocol_changes.json") as f:
    PROTOCOL_CHANGES = json.load(f)


def enabled(change_name, block_index=None):
    """Return True if protocol change is enabled."""
    if config.REGTEST:
        return True  # All changes are always enabled on REGTEST

    if config.TESTNET:
        index_name = "testnet_block_index"
    else:
        index_name = "block_index"

    enable_block_index = PROTOCOL_CHANGES[change_name][index_name]

    if not block_index:
        block_index = CURRENT_BLOCK_INDEX

    if block_index >= enable_block_index:
        return True
    else:
        return False


def get_value_by_block_index(change_name, block_index=None):
    if not block_index:
        block_index = CURRENT_BLOCK_INDEX

    max_block_index = -1

    if config.REGTEST:
        for key, value in PROTOCOL_CHANGES[change_name]["testnet"]:  # noqa: B007
            if int(key) > int(max_block_index):
                max_block_index = key
        return PROTOCOL_CHANGES[change_name]["testnet"][max_block_index]["value"]

    if config.TESTNET:
        index_name = "testnet"
    else:
        index_name = "mainnet"

    for key in PROTOCOL_CHANGES[change_name][index_name]:
        if int(key) > int(max_block_index) and block_index >= int(key):
            max_block_index = key

    return PROTOCOL_CHANGES[change_name][index_name][max_block_index]["value"]
