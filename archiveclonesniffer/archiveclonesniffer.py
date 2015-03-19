# -*- coding: utf-8 -*-

import hashlib, zlib

def getSHA1(filename):
    filehash = hashlib.sha1()
    with open(filename, 'rb') as fp:
        buf = fp.read()
        filehash.update(buf)
    sha1 = filehash.hexdigest().rjust(40,'0')
    return sha1

def getCRC32(filename):
    value = 0
    with open(filename, 'rb') as file:
        buf = file.read()
        value = zlib.crc32(buf, value)
    crc32int = value & 0XFFFFFFFF
    crc32 = "{:08X}".format(crc32int).lower()
    return crc32

