import sys
import argparse
import Reliable

parser = argparse.ArgumentParser()
parser.add_argument("-d", metavar='ip_address', type=str, default="127.0.0.1",
                    help="IP address of remote end (default 127.0.0.1)")
parser.add_argument("-p", metavar='local_port', type=int, default=10000, help="port for the local end (default 10000)")
parser.add_argument("-r", metavar='remote_port', type=int, default=7090,
                    help="port for the remote end (default 7090)")
parser.add_argument("-n", metavar='sequence_number', type=int, default=None,
                    help="initial sequence number in SYN (default at random)")
parser.add_argument('filename', metavar='filename', type=str, nargs=1, help='file to be transferred')
args = parser.parse_args()

reli = Reliable.Reliable(args.p)
print("Connecting...")
reli.connect(args.d, args.r, args.n)
print("Connected to %s:%d" % (args.d, args.r))

filename = sys.argv[1]
fin = open(args.filename[0], "rb")
while True:
    payload = fin.read(Reliable.PayloadSize)
    if not payload:
        break
    reli.send(payload)
fin.close()
reli.close()
