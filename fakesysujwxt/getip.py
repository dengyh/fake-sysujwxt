#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import pycurl
import re
import StringIO
import json
import logging

__version__ = '0.2'

LOGIN_TIMEOUT = 15
REQUEST_TIMEOUT = 25

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.debug('Debugging mode enabled.')

# ----------------
# Basic functions
# ----------------
def format_to_json(unformated_json):
    # pat = r'(\w+(?=:))'
    pat = r'((?:(?<=[,{\[])\s*)(\w+)(?=:))'
    sub = r'"\1"'
    return re.sub(pat, sub, unformated_json)

def retrive_data(url, cookie, request_json):
    ch = pycurl.Curl()
    ch.setopt(pycurl.URL, url)
    ch.setopt(pycurl.POST, True)
    ch.setopt(pycurl.POSTFIELDS, request_json)
    ch.setopt(pycurl.TIMEOUT, REQUEST_TIMEOUT)
    ch.setopt(pycurl.HTTPHEADER, ['Content-Type: multipart/form-data', 'render: unieap'])
    ch.setopt(pycurl.COOKIE, "JSESSIONID="+cookie)
    ret = StringIO.StringIO()
    ch.setopt(pycurl.WRITEFUNCTION, ret.write)

    try:
        ch.perform()
    except pycurl.error, e:
        logging.error('%s, %s', e[0], e[1])
        return (False, 'timeout')

    ret_code = ch.getinfo(pycurl.HTTP_CODE)
    ret_body = ret.getvalue()
    ch.close()
    if (ret_body.startswith('THE-NODE-OF-SESSION-TIMEOUT', 5)):
        return (False, 'expired')
    else:
        return (True, ret_body)

def login(username, passward):
    url = 'https://sso.sysu.edu.cn/cas/login?service=http%3A%2F%2Fitsbm.sysu.edu.cn%2Fitsbm%2Flogin.action'

    ch = pycurl.Curl()
    ch.setopt(pycurl.URL, url)
    ch.setopt(pycurl.TIMEOUT, LOGIN_TIMEOUT)
    ch.setopt(pycurl.POST, True)
    data = urllib.urlencode({'username': username, 'password': passward,'execution':'e3s1','_eventId':'submit','submit':'LOGIN'})
    ch.setopt(pycurl.POSTFIELDS, data)
    ret = StringIO.StringIO()
    ch.setopt(pycurl.WRITEFUNCTION, ret.write)
    # add header to ret value
    ch.setopt(pycurl.HEADER, True)

    try:
        ch.perform()
    except pycurl.error, e:
        logging.error('%s, %s', e[0], e[1])
        return (False, 'timeout')

    ret_code = ch.getinfo(pycurl.HTTP_CODE)
    ch.close()
    if ret_code == 200:
        logging.debug('Login errorpass: %s %s', username, passward)
        return (False, 'errorpass')
    else:
        ret_header = ret.getvalue()
        cookies = re.findall(r'^Set-Cookie: (.*);', ret_header, re.MULTILINE)
        cookie = cookies[0][11:]
        logging.debug('Login success: %s %s', username, passward)
        return (True, cookie)

# ------------
# Score Query
# ------------
def get_score(cookie, sno, year='', term=''):
    logging.debug('Getting score: %s %s %s %s', sno, year, term, cookie)
    url = 'http://uems.sysu.edu.cn/jwxt/xscjcxAction/xscjcxAction.action?method=getKccjList'
    if not year:
        year_param = ''
    else:
        year_param = """
                    {
                        "name": "Filter_t.xn_0.3563793106347481",
                        "type": "String",
                        "value": "'%s'",
                        "condition": " = ",
                        "property": "t.xn"
                    },
                    """ %year
    if not term:
        term_param = ''
    else:
        term_param = """
                    {
                        "name": "Filter_t.xq_0.7983325881237213",
                        "type": "String",
                        "value": "'%s'",
                        "condition": " = ",
                        "property": "t.xq"
                    },
                    """ %term
    query_json = """
    {
        body: {
            dataStores: {
                kccjStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "kccjStore",
                    pageNumber: 1,
                    pageSize: 100,
                    rowSetName: "pojo_com.neusoft.education.sysu.xscj.xscjcx.model.KccjModel",
                    order: "kclb asc"
                }
            },
            parameters: {
                "kccjStore-params": [
                    {
                        "name": "Filter_t.pylbm_0.1950409999148804",
                        "type": "String",
                        "value": "'01'",
                        "condition": " = ",
                        "property": "t.pylbm"
                    },
                    %s
                    %s
                    {
                        "name": "xh",
                        "type": "String",
                        "value": "'%s'",
                        "condition": " = ",
                        "property": "t.xh"
                    }
                ],
                "args": [
                    "student"
                ]
            }
        }
    }
    """ %(year_param, term_param, sno)
    return retrive_data(url, cookie, query_json)

# ----------------
# Timetable Query
# ----------------
def get_timetable(cookie, year, term):
    logging.debug('Getting timetable: %s %s %s', year, term, cookie)
    url = 'http://uems.sysu.edu.cn/jwxt/sysu/xk/xskbcx/xskbcx.jsp'

    ch = pycurl.Curl()
    ch.setopt(pycurl.URL, url + '?' + urllib.urlencode({'xnd':year, 'xq':term}))
    ch.setopt(pycurl.COOKIE, "JSESSIONID="+cookie)
    ret = StringIO.StringIO()
    ch.setopt(pycurl.WRITEFUNCTION, ret.write)

    try:
        ch.perform()
    except pycurl.error, e:
        logging.error('%s, %s', e[0], e[1])
        return (False, 'timeout')

    ret_code = ch.getinfo(pycurl.HTTP_CODE)
    ret_body = ret.getvalue()
    ch.close()

    if (ret_body.startswith('THE-NODE-OF-SESSION-TIMEOUT', 5)):
        return (False, 'expired')
    else:
        # add course time to schedule table
        pat = r'^var jcshowdata.*$'
        sub = """var jcshowdata=["","第一节<br>08:00-08:45","第二节<br>08:55-09:40","第三节<br>09:50-10:35","第四节<br>10:45-11:30","第五节<br>11:40-12:25","第六节<br>12:35-13:20","第七节<br>13:30-14:15","第八节<br>14:25-15:10","第九节<br>15:20-16:05","第十节<br>16:15-17:00","第十一节<br>17:10-17:55","第十二节<br>18:05-18:50","第十三节<br>19:00-19:45","第十四节<br>19:55-20:40","第十五节<br>20:50-21:35"];\r"""
        html = re.sub(pat, sub, ret_body, flags=re.M)
        return (True, html)

# --------------------
# Personal info Query
# --------------------
def get_info(cookie):
    logging.debug('Getting info: %s', cookie)
    url = "http://uems.sysu.edu.cn/jwxt/WhzdAction/WhzdAction.action?method=getGrwhxxList"
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                xsxxStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "xsxxStore",
                    pageNumber: 1,
                    pageSize: 10,
                    recordCount: 0,
                    rowSetName: "pojo_com.neusoft.education.sysu.xj.grwh.model.Xsgrwhxx"
                }
            },
            parameters: {
                "args": [""]
            }
        }
    }
    """
    return retrive_data(url, cookie, query_json)

# -----------------------
# Course Selecting Query
# -----------------------
def get_available_courses(cookie, year, term, course_type, campus):
    logging.debug('Getting available course: %s %s %s %s %s', year, term, course_type, campus, cookie)
    url = 'http://uems.sysu.edu.cn/jwxt/xsxk/xsxk.action?method=getJxbxxFunc'
    if course_type == '30':
        campus_para = """
        {
            "name": "curxiaoqu",
            "type": "String",
            "value": "'%s'",
            "condition": " = ",
            "property": "A.SKJSSZXQ"
        }
        """ %(campus)
    else:
        campus_para = ""

    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                table1kxkcStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "table1kxkcStore",
                    pageNumber: 1,
                    pageSize: 280,
                    recordCount: 9,
                    rowSetName: "pojo_com.neusoft.education.sysu.xk.zxxkgg.model.KkblbModel"
                }
            },
            parameters: {
                "table1kxkcStore-params": [%s],
                "args": [
                    "%s",
                    "%s",
                    "%s"
                ]
            }
        }
    }
    """ %(campus_para, year, term, course_type)
    return retrive_data(url, cookie, query_json)

def add_course(cookie, resource_id, year, term):
    logging.debug('Adding course: %s %s %s %s', resource_id, year, term, cookie)
    url = 'http://uems.sysu.edu.cn/jwxt/xsxk/xsxk.action?method=selectCoursesChanged'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {},
            parameters: {
                "args": [
                    "%s",
                    "",
                    "",
                    "%s",
                    "%s",
                    "",
                    "",
                    "",
                    "",
                    "",
                    ""
                ],
                "responseParam": "dataSave"
            }
        }
    }
    """ %(resource_id, year, term)
    return retrive_data(url, cookie, query_json)

# --------------------
# Course Result Query
# --------------------
def get_course_result(cookie, year, term):
    logging.debug('Getting course result: %s %s %s', year, term, cookie)
    url = 'http://uems.sysu.edu.cn/jwxt/xstk/xstk.action?method=getXkxkjglistByxh'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                xsxkjgStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "xsxkjgStore",
                    pageNumber: 1,
                    pageSize: 100,
                    recordCount: 0,
                    rowSetName: "pojo_com.neusoft.education.sysu.xk.drxsxkjg.entity.XkjgEntity",
                    order: "xnd desc,xq desc,kclbm asc"
                }
            },
            parameters: {
                "xsxkjgStore-params": [
                    {
                        "name": "xnd",
                        "type": "String",
                        "value": "'%s'",
                        "condition": " = ",
                        "property": "xnd"
                    },
                    {
                        "name": "xq",
                        "type": "String",
                        "value": "'%s'",
                        "condition": " = ",
                        "property": "xq"
                    }
                ],
                "args": []
            }
        }
    }
    """ %(year, term)
    return retrive_data(url, cookie, query_json)

def get_course_result_by_type(cookie, year, term, course_type):
    logging.debug('Getting course result by type: %s %s %s %s', year, term, course_type, cookie)
    url = 'http://uems.sysu.edu.cn/jwxt/xsxk/xsxk.action?method=getTab1YxkcByxndxqkclbmpylbmxh'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                table1yxkcStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "table1yxkcStore",
                    pageNumber: 1,
                    pageSize: 100,
                    recordCount: 0,
                    rowSetName: "pojo_com.neusoft.education.sysu.xk.drxsxkjg.entity.XkjgAndSsjhModel"
                }
            },
            parameters: {
                "args": [
                    "01",
                    "%s",
                    "%s",
                    "%s"
                ]
            }
        }
    }
    """ %(course_type, year, term)
    return retrive_data(url, cookie, query_json)

def remove_course(cookie, resource_id):
    logging.debug('Removing course: %s %s', resource_id, cookie)
    url = 'http://uems.sysu.edu.cn/jwxt/xsxk/xsxk.action?method=delXsxkjgFuncChanged'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {},
            parameters: {
                "args": ["%s"],
                "responseParam": "dataSave"
            }
        }
    }
    """ %(resource_id)
    return retrive_data(url, cookie, query_json)

def reset_password(cookie, new_password):
    logging.debug('Resetting passward: %s %s', new_password, cookie)
    url = 'http://uems.sysu.edu.cn/jwxt/GbmmAction/GbmmAction.action?method=gbmm'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {

            },
            parameters: {
                "args": [
                    "%s"
                ],
                "responseParam": "rs"
            }
        }
    }
    """ %(new_password)
    return retrive_data(url, cookie, query_json)

def get_tno(cookie):
    """
    获取[学号], [年级], [教学号]
    """
    logging.debug('Getting tno: %s', cookie)
    url = 'http://uems.sysu.edu.cn/jwxt/xscjcxAction/xscjcxAction.action?method=judgeStu'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                tempStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "tempStore",
                    pageNumber: 1,
                    pageSize: 2147483647,
                    recordCount: 0,
                    rowSetName: "pojo_com.neusoft.education.sysu.xy.xyjy.model.OnecolumModel"
                }
            },
            parameters: {
                "args": [],
                "responseParam": "result"
            }
        }
    }
    """
    return retrive_data(url, cookie, query_json)

def get_required_credit(cookie, grade, tno):
    """
    获取要求总学分
    """
    logging.debug('Getting required credit: %s %s %s', grade, tno, cookie)
    url = 'http://uems.sysu.edu.cn/jwxt/xscjcxAction/xscjcxAction.action?method=getZyxf'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                zxzyxfStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "zxzyxfStore",
                    pageNumber: 1,
                    pageSize: 2147483647,
                    recordCount: 0,
                    rowSetName: "pojo_com.neusoft.education.sysu.djks.ksgl.model.TwoColumnModel"
                }
            },
            parameters: {
                "zxzyxfStore-params": [
                    {
                        "name": "pylbm",
                        "type": "String",
                        "value": "'01'",
                        "condition": " = ",
                        "property": "x.pylbm"
                    },
                    {
                        "name": "nj",
                        "type": "String",
                        "value": "'%s'",
                        "condition": " = ",
                        "property": "x.nj"
                    },
                    {
                        "name": "zyh",
                        "type": "String",
                        "value": "'%s'",
                        "condition": " = ",
                        "property": "x.zyh"
                    }
                ],
                "args": []
            }
        }
    }
    """ %(grade, tno)
    return retrive_data(url, cookie, query_json)

def get_earned_credit(cookie, sno, year='', term=''):
    """
    获取已取得的学分
    """
    logging.debug('Getting earned credit: %s %s %s %s', sno, year, term, cookie)
    url = 'http://uems.sysu.edu.cn//jwxt/xscjcxAction/xscjcxAction.action?method=getAllXf'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                xfStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "xfStore",
                    pageNumber: 1,
                    pageSize: 2147483647,
                    recordCount: 0,
                    rowSetName: "pojo_com.neusoft.education.sysu.djks.ksgl.model.TwoColumnModel"
                }
            },
            parameters: {
                "args": [
                    "%s",
                    "%s",
                    "%s",
                    "01"
                ]
            }
        }
    }
    """ %(sno, year, term)
    return retrive_data(url, cookie, query_json)

def get_gpa(cookie, sno, year='', term=''):
    """
    获取已取得的总基点: 专必 公必 公选 专选
    """
    logging.debug('Getting gpa: %s %s %s %s', sno, year, term, cookie)
    url = 'http://uems.sysu.edu.cn/jwxt/xscjcxAction/xscjcxAction.action?method=getAllJd'
    query_json = """
    {
        header: {
            "code": -100,
            "message": {
                "title": "",
                "detail": ""
            }
        },
        body: {
            dataStores: {
                jdStore: {
                    rowSet: {
                        "primary": [],
                        "filter": [],
                        "delete": []
                    },
                    name: "jdStore",
                    pageNumber: 1,
                    pageSize: 2147483647,
                    recordCount: 0,
                    rowSetName: "pojo_com.neusoft.education.sysu.djks.ksgl.model.TwoColumnModel"
                }
            },
            parameters: {
                "args": [
                    "%s",
                    "%s",
                    "%s",
                    ""
                ]
            }
        }
    }
    """ %(sno, year, term)
    return retrive_data(url, cookie, query_json)


def get_evaluateList(cookie):
    url = 'http://uems.sysu.edu.cn/jwxt/xspjaction/xspjaction.action?method=getXspjlist'
    query_json = """
{header:{"code": -100, "message": {"title": "", "detail": ""}},body:{dataStores:{},parameters:{"args": [], "responseParam": "xfms"}}}
    """
    return retrive_data(url, cookie, query_json)
# all following methods left for future usage
def get_aaa(cookie):
    url = 'http://uems.sysu.edu.cn/jwxt/xsxk/xsxk.action?method=getJxjhByxh'
    query_json = """
{header:{"code": -100, "message": {"title": "", "detail": ""}},body:{dataStores:{},parameters:{"args": [], "responseParam": "xfms"}}}
    """
    return retrive_data(url, cookie, query_json)

def get_bbb(cookie):
    url = 'http://uems.sysu.edu.cn/jwxt/xsxk/xsxk.action?method=getKclb'
    query_json = """
{header:{"code": -100, "message": {"title": "", "detail": ""}},body:{dataStores:{fkclbStore:{rowSet:{"primary":[],"filter":[],"delete":[]},name:"fkclbStore",pageNumber:1,pageSize:2147483647,recordCount:0,rowSetName:"pojo_com.neusoft.education.sysu.xk.zxxk.entity.KclbxxModel"}},parameters:{"args": ["2012-2013", "1", "02"]}}}
    """
    return retrive_data(url, cookie, query_json)

