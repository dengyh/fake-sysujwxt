import fakesysujwxt
import json

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

def add_score(jd, xf):
  jd += [toronto(float(i["jd"])) for i in score["body"]["dataStores"]["kccjStore"]["rowSet"]["primary"]]
  xf += [float(i["xf"]) for i in score["body"]["dataStores"]["kccjStore"]["rowSet"]["primary"]]


_,cc = fakesysujwxt.login("11331168", "")
jd = []
xf = []
score = json.loads(fakesysujwxt.format_to_json(fakesysujwxt.get_score(cc, "11331168", "2011-2012", "1")[1]))
add_score(jd, xf)
score = json.loads(fakesysujwxt.format_to_json(fakesysujwxt.get_score(cc, "11331168", "2011-2012", "2")[1]))
add_score(jd, xf)
score = json.loads(fakesysujwxt.format_to_json(fakesysujwxt.get_score(cc, "11331168", "2011-2012", "3")[1]))
add_score(jd, xf)
score = json.loads(fakesysujwxt.format_to_json(fakesysujwxt.get_score(cc, "11331168", "2012-2013", "1")[1]))
add_score(jd, xf)
score = json.loads(fakesysujwxt.format_to_json(fakesysujwxt.get_score(cc, "11331168", "2012-2013", "2")[1]))
add_score(jd, xf)
a = sum([i*j for i, j in zip(jd, xf)])
print a / sum(xf)
