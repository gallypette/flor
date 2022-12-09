from flor.filter import BloomFilter

def testouille():
    bf = BloomFilter(n=100000, p=0.01)
    with open("test_vector.txt", "r") as fp:
        for line in fp:
            bf.add(line.encode())

    with open("test_writing.bloom", "wb") as fr:
        bf.write(fr)

if __name__ == '__main__':
    testouille()
