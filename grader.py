import os
import sys
import time
import json
import argparse
import subprocess

# inpath = "/autograder/submission"
# outpath = "/autograder/results"

parser = argparse.ArgumentParser()
parser.add_argument("-c", action='store_true', help="use C code")
parser.add_argument('inpath', metavar='inpath', type=str, nargs='?', default='./', help='path to the code directory')
parser.add_argument('outpath', metavar='outpath', type=str, nargs='?',
                    default='./', help='path to the result directory')
args = parser.parse_args()

if args.c:
    print("Running C code ...")
else:
    print("Running Python code ...")


def run(param):
    try:
        generator = subprocess.Popen("./generator 12582912 a.txt".split(), stdout=subprocess.DEVNULL)
        generator.wait()
        cmd = "%s/Receiver -p 50001 -s %d -d %d -f %d temp.txt" % (args.inpath,
                                                                   param["synloss"], param["dataloss"], param["finloss"])
        receiver = subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if args.c:
            cmd = "%s/Sender a.txt -p 10000 -r 50001" % args.inpath
        else:
            cmd = "python3 %s/Sender.py a.txt -p 10000 -r 50001" % args.inpath
        if "seqnum" in params:
            cmd += ' -n %d' % params["seqnum"]
        sender = subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except Exception as e:
        print(e)
        return 0

    try:
        start = time.time()
        out, err = receiver.communicate(timeout=param["timeout"])
        if len(err) != 0:
            print(err.decode())
        out, err = sender.communicate(timeout=param["timeout"])
        if len(err) != 0:
            print(err.decode())
        end = time.time()
        print("Finished in %.2f seconds" % (end-start))
    except Exception as e:
        receiver.kill()
        sender.kill()
        out, err = receiver.communicate()
        out, err = sender.communicate()
        if Exception is subprocess.TimeoutExpired:
            print("Timed out after %d seconds" % param["timeout"])
        else:
            print(e)
        return 0

    res = 1
    with subprocess.Popen(("diff -q %s/a.txt %s/temp.txt" % (args.inpath, args.inpath)).split(), stdout=subprocess.PIPE) as proc:
        out, err = proc.communicate()
        if len(out) != 0:
            res = 0
    return res


params = [
    {"dataloss": 0, "synloss": 0, "finloss": 0, "timeout": 35, 'seqnum': 0},
    {"dataloss": 0, "synloss": 0, "finloss": 0, "timeout": 35, 'seqnum': 4294967296},
    {"dataloss": 1, "synloss": 0, "finloss": 0, "timeout": 50},
    {"dataloss": 1, "synloss": 0, "finloss": 0, "timeout": 50, 'seqnum': 4294957296},
    {"dataloss": 5, "synloss": 0, "finloss": 0, "timeout": 60},
    {"dataloss": 5, "synloss": 0, "finloss": 0, "timeout": 60, 'seqnum': 4294864896},
    {"dataloss": 1, "synloss": 50, "finloss": 25, "timeout": 75},
    {"dataloss": 1, "synloss": 50, "finloss": 25, "timeout": 75, 'seqnum': 4293508096},
    {"dataloss": 5, "synloss": 50, "finloss": 25, "timeout": 90},
    {"dataloss": 5, "synloss": 50, "finloss": 25, "timeout": 90, 'seqnum': 4291637248}
]

cases = []
score = 0
i = 0
for param in params:
    i += 1
    case = {
        "score": 0,
        "max_score": 10,
        "visibility": "visible",
        "output": json.dumps(param)
    }

    print("Case %d: " % i, param)
    sc = run(param)*10
    case["score"] += sc
    cases.append(case)
    score += sc
    print("Points: %d/10\n" % sc)

print("Total: %d/100" % score)

res = {
    "score": score,
    "stdout_visibility": "visible",
    "tests": cases
}

with open('%s/results.json' % args.outpath, 'w') as fout:
    fout.write(json.dumps(res))
