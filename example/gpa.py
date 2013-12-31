import fakesysujwxt
import json
import sys

def toronto(s):
    if s >= 3.5:
        return 4.0
    elif s >= 3.0:
        return 3.7
    elif s >= 2.7:
        return 3.3
    elif s >= 2.3:
        return 3.0
    elif s >= 2.0:
        return 2.7

def add_score(jd, xf, score):
    jd += [toronto(float(i["jd"])) for i in score["body"]["dataStores"]["kccjStore"]["rowSet"]["primary"]]
    xf += [float(i["xf"]) for i in score["body"]["dataStores"]["kccjStore"]["rowSet"]["primary"]]

if __name__ == "__main__":
    username = sys.argv[1]
    password = sys.argv[2]
    _, cookie = fakesysujwxt.login(username, password)
    jd = []
    xf = []
    year_start = 2011
    for yy in range(2):
        for term in range(1, 4):
            year = "%d-%d" % (year_start + yy, year_start + yy + 1)
            raw_score = fakesysujwxt.get_score(cookie, username, year, term)[1]
            score = json.loads(fakesysujwxt.format_to_json(raw_score))
            add_score(jd, xf, score)
    a = sum([i * j for i, j in zip(jd, xf)])
    print a / sum(xf)
