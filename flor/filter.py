# DCSO - Flor
# Copyright (c) 2016, 2017, DCSO GmbH. All rights reserved.

import math
import pickle
from struct import unpack, pack
from .fnv import fnv_1
from roaringbitmap import (RoaringBitmap)
import pdb

m = 18446744073709551557
g = 18446744073709550147

class BloomFilter(object):

    class CapacityError(BaseException):
        pass

    def __init__(self, n=100000, p=0.001, data=b''):
        self.p = p
        self.n = n
        self.N = 0
        self.m = int(abs(math.ceil(float(n) * math.log(float(p)) / math.pow(math.log(2.0), 2.0))))
        # M repurposed
        self.M = 0
        self.k = int(math.ceil(math.log(2) * float(self.m) / float(n)))
        # self._bytes = bytearray([0 for i in range(self.M)])
        self._bytes = RoaringBitmap()
        self.data = data

    def __contains__(self, value):
        return self.check(value)

    def read(self, input_file):

        bs8 = input_file.read(8)
        if len(bs8) != 8:
            raise IOError("Invalid filter!")
        flags = unpack('<Q', bs8)[0]

        if flags & 0xFF != 1:
            raise IOError("Invalid version flag!")

        bs8 = input_file.read(8)
        if len(bs8) != 8:
            raise IOError("Invalid filter!")
        self.n = unpack('<Q', bs8)[0]

        bs8 = input_file.read(8)
        if len(bs8) != 8:
            raise IOError("Invalid filter!")
        self.p = unpack('<d', bs8)[0]

        bs8 = input_file.read(8)
        if len(bs8) != 8:
            raise IOError("Invalid filter!")
        self.k = unpack('<Q', bs8)[0]

        bs8 = input_file.read(8)
        if len(bs8) != 8:
            raise IOError("Invalid filter!")
        self.m = unpack('<Q', bs8)[0]

        bs8 = input_file.read(8)
        if len(bs8) != 8:
            raise IOError("Invalid filter!")
        self.N = unpack('<Q', bs8)[0]

        bs8 = input_file.read(8)
        if len(bs8) != 8:
            raise IOError("Invalid filter!")
        self.M = unpack('<Q', bs8)[0]

        self._bytes = pickle.loads(input_file.read(self.M))

        # we read any data that might be attached to the file
        self.data = input_file.read()

    def write(self, output_file):
        p = pickle.dumps(self._bytes)
        self.M = len(p)
        output_file.write(pack('<Q', 1))
        output_file.write(pack('<Q', self.n))
        output_file.write(pack('<d', self.p))
        output_file.write(pack('<Q', self.k))
        output_file.write(pack('<Q', self.m))
        output_file.write(pack('<Q', self.N))
        output_file.write(pack('<Q', self.M))
        output_file.write(p)
        output_file.write(bytes(self.data))

    def add(self, value):
        fp = self.fingerprint(value)
        new_value = False
        for fpe in fp:
            try:
                if self._bytes.index(fpe) != None: 
                    break
            except IndexError: 
                new_value = True
        if new_value:
            if (self.N+1) >= self.n:
                raise BloomFilter.CapacityError("Bloom filter is full!")
            else:
                self.N+=1
                for fpe in fp:
                    self._bytes.add(fpe)

    def check(self, value):
        fp = self.fingerprint(value)
        for fpe in fp:
            try:
                if self._bytes.index(fpe) != None :
                    continue
            except IndexError:
                return False
        return True

    def fingerprint(self, value):
        bvalue = bytes(value)
        hn = fnv_1(bvalue) % m
        fp = []
        for i in range(self.k):
            hn = (hn*g & 0xFFFFFFFFFFFFFFFF) % m
            fp.append((hn % self.m) & 0xFFFFFFFFFFFFFFFF)
        return fp