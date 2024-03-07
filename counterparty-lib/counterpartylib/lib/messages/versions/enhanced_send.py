#! /usr/bin/python3

import struct
import json
import logging
logger = logging.getLogger(__name__)

from counterpartylib.lib import (config, util, exceptions, util, message_type, address, ledger)

FORMAT = '>QQ21s'
LENGTH = 8 + 8 + 21
MAX_MEMO_LENGTH = 34
ID = 2 # 0x02

def unpack(db, message, block_index):
    try:
        # account for memo bytes
        memo_bytes_length = len(message) - LENGTH
        if memo_bytes_length < 0:
            raise exceptions.UnpackError('invalid message length')
        if memo_bytes_length > MAX_MEMO_LENGTH:
            raise exceptions.UnpackError('memo too long')

        struct_format = FORMAT + f'{memo_bytes_length}s'
        asset_id, quantity, short_address_bytes, memo_bytes = struct.unpack(struct_format, message)
        if len(memo_bytes) == 0:
            memo_bytes = None

        # unpack address
        full_address = address.unpack(short_address_bytes)

        # asset id to name
        asset = ledger.generate_asset_name(asset_id, block_index)
        if asset == config.BTC:
            raise exceptions.AssetNameError(f'{config.BTC} not allowed')

    except (struct.error) as e:
        logger.warning(f"enhanced send unpack error: {e}")
        raise exceptions.UnpackError('could not unpack')

    except (exceptions.AssetNameError, exceptions.AssetIDError) as e:
        logger.warning(f"enhanced send invalid asset id: {e}")
        raise exceptions.UnpackError('asset id invalid')

    unpacked = {
        'asset': asset,
      'quantity': quantity,
      'address': full_address,
      'memo': memo_bytes,
    }
    return unpacked

def validate (db, source, destination, asset, quantity, memo_bytes, block_index):
    problems = []

    if asset == config.BTC: problems.append(f'cannot send {config.BTC}')

    if not isinstance(quantity, int):
        problems.append('quantity must be in satoshis')
        return problems

    if quantity < 0:
        problems.append('negative quantity')

    if quantity == 0:
        problems.append('zero quantity')

    # For SQLite3
    if quantity > config.MAX_INT:
        problems.append('integer overflow')

    # destination is always required
    if not destination:
        problems.append('destination is required')

    # check memo
    if memo_bytes is not None and len(memo_bytes) > MAX_MEMO_LENGTH:
        problems.append('memo is too long')

    if ledger.enabled('options_require_memo'):
        cursor = db.cursor()
        try:
            results = ledger.get_addresses(db, address=destination)
            if results:
                result = results[0]
                if result and util.active_options(result['options'], config.ADDRESS_OPTION_REQUIRE_MEMO):
                    if memo_bytes is None or (len(memo_bytes) == 0):
                        problems.append('destination requires memo')
        finally:
            cursor.close()

    return problems

def compose (db, source, destination, asset, quantity, memo, memo_is_hex):
    cursor = db.cursor()

    # Just send BTC?
    if asset == config.BTC:
        return (source, [(destination, quantity)], None)

    # resolve subassets
    asset = ledger.resolve_subasset_longname(db, asset)

    #quantity must be in int satoshi (not float, string, etc)
    if not isinstance(quantity, int):
        raise exceptions.ComposeError('quantity must be an int (in satoshi)')

    # Only for outgoing (incoming will overburn).
    balance = ledger.get_balance(db, source, asset)
    if balance < quantity:
        raise exceptions.ComposeError('insufficient funds')

    # convert memo to memo_bytes based on memo_is_hex setting
    if memo is None:
        memo_bytes = b''
    elif memo_is_hex:
        memo_bytes = bytes.fromhex(memo)
    else:
        memo = memo.encode('utf-8')
        memo_bytes = struct.pack(f">{len(memo)}s", memo)

    block_index = ledger.CURRENT_BLOCK_INDEX

    problems = validate(db, source, destination, asset, quantity, memo_bytes, block_index)
    if problems: raise exceptions.ComposeError(problems)

    asset_id = ledger.get_asset_id(db, asset, block_index)

    short_address_bytes = address.pack(destination)

    data = message_type.pack(ID)
    data += struct.pack(FORMAT, asset_id, quantity, short_address_bytes)
    data += memo_bytes

    cursor.close()
    # return an empty array as the second argument because we don't need to send BTC dust to the recipient
    return (source, [], data)

def parse (db, tx, message):
    cursor = db.cursor()

    # Unpack message.
    try:
        unpacked = unpack(db, message, tx['block_index'])
        asset, quantity, destination, memo_bytes = unpacked['asset'], unpacked['quantity'], unpacked['address'], unpacked['memo']

        status = 'valid'

    except (exceptions.UnpackError, exceptions.AssetNameError, struct.error) as e:
        asset, quantity, destination, memo_bytes = None, None, None, None
        status = f'invalid: could not unpack ({e})'
    except:
        asset, quantity, destination, memo_bytes = None, None, None, None
        status = 'invalid: could not unpack'

    if status == 'valid':
        # don't allow sends over MAX_INT at all
        if quantity and quantity > config.MAX_INT:
            status = 'invalid: quantity is too large'
            quantity = None

    if status == 'valid':
        problems = validate(db, tx['source'], destination, asset, quantity, memo_bytes, tx['block_index'])
        if problems: status = 'invalid: ' + '; '.join(problems)

    if status == 'valid':
        # verify balance is present
        balance = ledger.get_balance(db, tx['source'], asset)
        if balance == 0 or balance < quantity:
            status = 'invalid: insufficient funds'

    if status == 'valid':
        ledger.debit(db, tx['source'], asset, quantity, tx['tx_index'], action='send', event=tx['tx_hash'])
        ledger.credit(db, destination, asset, quantity, tx['tx_index'], action='send', event=tx['tx_hash'])

    # log invalid transactions
    if status != 'valid':
        if quantity is None:
            logger.warning(f"Invalid send from {tx['source']} with status {status}. ({tx['tx_hash']})")
        else:
            logger.warning(f"Invalid send of {quantity} {asset} from {tx['source']} to {destination}. status is {status}. ({tx['tx_hash']})")

    # Add parsed transaction to message-type–specific table.
    bindings = {
        'tx_index': tx['tx_index'],
        'tx_hash': tx['tx_hash'],
        'block_index': tx['block_index'],
        'source': tx['source'],
        'destination': destination,
        'asset': asset,
        'quantity': quantity,
        'status': status,
        'memo': memo_bytes,
    }
    if "integer overflow" not in status and "quantity must be in satoshis" not in status:
        sql = 'insert into sends (tx_index, tx_hash, block_index, source, destination, asset, quantity, status, memo) values(:tx_index, :tx_hash, :block_index, :source, :destination, :asset, :quantity, :status, :memo)'
        cursor.execute(sql, bindings)
    else:
        logger.warning(f"Not storing [send] tx [{tx['tx_hash']}]: {status}")
        logger.debug(f"Bindings: {json.dumps(bindings)}")

    cursor.close()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
