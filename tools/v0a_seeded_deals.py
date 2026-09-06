"""Reproducible bounded dealer schedules; this tool never launches poker."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

ALGORITHM = 'sha256-counter-fisher-yates-v1'
REQUEST_VERSION = 'pontius-v0a-seeded-deals-request-v1'
RESULT_VERSION = 'pontius-v0a-seeded-deals-result-v1'


class Refusal(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(condition, code='input_invalid'):
    if not condition:
        raise Refusal(code)


def _seed(seed):
    require(type(seed) is str and re.fullmatch('[0-9a-f]{64}', seed) is not None)
    return bytes.fromhex(seed)


def _words(seed, hand_index):
    prefix = b'pontius-v0a-seeded-deals-v1\x00' + seed + hand_index.to_bytes(4, 'big')
    for counter in range(128):
        block = hashlib.sha256(prefix + counter.to_bytes(4, 'big')).digest()
        for offset in range(0, 32, 4):
            yield int.from_bytes(block[offset:offset+4], 'big')


def _index(words, bound):
    limit = 2**32 - (2**32 % bound)
    for word in words:
        if word < limit:
            return word % bound
    raise Refusal('generation_limit')


def _deck(seed, hand_index):
    deck = list(range(52))
    words = _words(seed, hand_index)
    for index in range(51, 0, -1):
        other = _index(words, index + 1)
        deck[index], deck[other] = deck[other], deck[index]
    return deck


def deal_for_hand(seed, hand_index):
    seed_bytes = _seed(seed)
    require(type(hand_index) is int and 0 <= hand_index <= 15)
    deck = _deck(seed_bytes, hand_index)
    hands = [None]*6
    for offset in range(6):
        hands[(hand_index + 1 + offset) % 6] = sorted([deck[offset], deck[offset + 6]])
    return {'private_hands': hands, 'board_runout': deck[12:17]}


def generate_session(seed, hand_count):
    _seed(seed)
    require(type(hand_count) is int and 1 <= hand_count <= 16)
    return {'version': 'pontius-v0a-table-session-v1', 'button': 0, 'controlled_seat': 3,
            'starting_stacks': [200]*6, 'small_blind': 1, 'big_blind': 2,
            'opponents': ['passive', 'passive', 'passive', None, 'passive', 'passive'],
            'hands': [deal_for_hand(seed, h) for h in range(hand_count)]}


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
            + '\n').encode('utf-8')


def decode_request(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            require(key not in value)
            value[key] = item
        return value

    def integer(token):
        require(len(token) <= 2)
        return int(token)

    def forbidden(_):
        raise Refusal('input_invalid')

    try:
        require(type(raw) is bytes and 0 < len(raw) <= 1024
                and not raw.startswith(b'\xef\xbb\xbf') and b'\r' not in raw)
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                           parse_int=integer, parse_float=forbidden, parse_constant=forbidden)
        require(type(value) is dict and set(value) == {'version', 'seed', 'hand_count'})
        require(value['version'] == REQUEST_VERSION)
        _seed(value['seed'])
        require(type(value['hand_count']) is int and 1 <= value['hand_count'] <= 16)
        return value
    except (ValueError, RecursionError) as error:
        raise Refusal('input_invalid') from error


def _absolute(path, code):
    require(path.is_absolute() and path.drive.upper() == 'D:' and '..' not in path.parts, code)


def _regular(path, directory, code):
    _absolute(path, code)
    for current in (*path.parents, path):
        info = current.lstat()
        require(not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                and (stat.S_ISDIR(info.st_mode) if current != path or directory
                     else stat.S_ISREG(info.st_mode)), code)
    return info


def _identity(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def _read(path, limit, code):
    try:
        before = _identity(_regular(path, False, code))
        require(0 < before[2] <= limit, code)
        with path.open('rb') as stream:
            require(_identity(os.fstat(stream.fileno())) == before, code)
            raw = stream.read(limit + 1)
            require(_identity(os.fstat(stream.fileno())) == before, code)
        after = _identity(_regular(path, False, code))
        require(before == after and len(raw) == before[2] and 0 < len(raw) <= limit, code)
        return raw, after
    except (OSError, ValueError) as error:
        raise Refusal(code) from error


def _revalidate(path, snapshot):
    require(_read(path, 1024, 'input_invalid') == snapshot)


def _publish(path, raw):
    code = 'output_failed'
    try:
        _absolute(path, code)
        _regular(path.parent, True, code)
        require(not os.path.lexists(path), code)
        # Single exclusive write; any later failure leaves this invocation's file intact.
        with path.open('xb') as stream:
            require(stream.write(raw) == len(raw), code)
            stream.flush()
            os.fsync(stream.fileno())
            identity = _identity(os.fstat(stream.fileno()))
        require(_read(path, 16384, code) == (raw, identity), code)
    except (OSError, ValueError) as error:
        raise Refusal(code) from error


def _run(request_path, output_path):
    require(os.name == 'nt' and sys.implementation.name == 'cpython'
            and sys.dont_write_bytecode and sys.flags.safe_path, 'environment_invalid')
    request = _read(request_path, 1024, 'input_invalid')
    value = decode_request(request[0])
    raw = encode(generate_session(value['seed'], value['hand_count']))
    require(len(raw) <= 16384, 'generation_limit')
    _revalidate(request_path, request)
    _publish(output_path, raw)
    _revalidate(request_path, request)
    receipt = encode({'version': RESULT_VERSION, 'status': 'generated', 'algorithm': ALGORITHM,
                      'seed': value['seed'], 'hand_count': value['hand_count'],
                      'request_sha256': hashlib.sha256(request[0]).hexdigest(),
                      'session_sha256': hashlib.sha256(raw).hexdigest(), 'session_bytes': len(raw)})
    try:
        require(len(receipt) <= 4096 and os.write(1, receipt) == len(receipt), 'output_failed')
    except OSError as error:
        raise Refusal('output_failed') from error


def main(argv=None):
    try:
        parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
        parser.add_argument('--request', required=True, type=Path)
        parser.add_argument('--output', required=True, type=Path)
        args = parser.parse_args(argv)
        _run(args.request, args.output)
        return 0
    except KeyboardInterrupt:
        code, status = 'interrupted', 130
    except Refusal as error:
        code, status = error.code, 1
    except Exception:
        code, status = 'internal_error', 1
    try:
        os.write(2, ('REFUSED '+code+'\n').encode('ascii'))
    except (Exception, KeyboardInterrupt):
        pass
    return status


if __name__ == '__main__':
    raise SystemExit(main())
