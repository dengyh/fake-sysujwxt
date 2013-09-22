# -*- coding: utf-8 -*-
import fakesysujwxt
import re
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.debug('Debugging mode enabled.')

def get_table(username, password, year, term):
    cookie = fakesysujwxt.login( username, password )
    if cookie[ 0 ] == True:
        cookie = cookie[ 1 ]
    else:
        print "password mismatch!"
        return -1
    result = fakesysujwxt.get_timetable( cookie.encode('ascii'),
                                     year.encode('ascii'),
                                     term.encode('ascii'))
    if result[ 0 ] == True:
        result = result[ 1 ]
    course = re.findall( r'jc=\'(?P<jc>.*?)\'.*?kcmc=\'(?P<kcmc>.*?)\'.*?dd=\'(?P<dd>.*?)\'.*?zfw=\'(?P<zfw>.*?)\'.*?weekpos=(?P<weekpos>.*?);', result, re.S )
    ret = [ { "time": match[ 0 ] , "course_name": match[ 1 ], "location": match[ 2 ], "duration": match[ 3 ], "week_pos": match[ 4 ] } for match in course ]
    return ret

# ------------
#  generate an ics file which can be imported to calendar
#  param:
#    start_date: the first Monday of a term
#    course_list: a list containing all courses, each element is a dict with 5 keys:
#      time: when the course starts and ends. eg. 13-15节 (the Chinese charater is not necessary)
#      course_name: name of the course
#      location: in which the classroom to take the course
#      duration: on which week the course starts and ends. eg. 2-13
#      week_pos: on which day of the week to take the course
# ------------
def convert_to_ics( start_date, course_list ):
    file = open( "table.ics", "w" )
    head = ("BEGIN:VCALENDAR\n"
            "VERSION:2.0\n"
            "PRODID:-//InSysu//Course Timetable\n"
            "METHOD:PUBLISH\n")
    file.write( head )
    for course in course_list:
        logging.info( "inserting %s" % course[ "course_name" ] )
        location = course[ "location" ]
        course_name = course[ "course_name" ]
        course_time = re.search( r'([0-9]*)-([0-9]*)', course[ "time" ] )
        if course_time is None:
            course_time = ''
        first_cls = int( course_time.group(1) )
        last_cls = int( course_time.group(2) )

        week_p = re.search( r'([0-9]*)-([0-9]*)', course[ "duration" ] )
        first_week = int(week_p.group(1))
        last_week = int(week_p.group(2))
        len = last_week - first_week + 1

        week_pos = int( course[ "week_pos" ] )
        first_day = start_date + timedelta( days = week_pos - 1 + ( first_week - 1 ) * 7 )
        #format to string
        first_day_s = first_day.strftime( "%Y%m%dT%H%M%S" )

        start_time = ( first_day + timedelta( hours = 8 ) + timedelta( minutes = 55 * ( first_cls - 1 ) ) ).strftime( "%Y%m%dT%H%M%S" )
        end_time = ( first_day + timedelta( hours = 8, minutes = 45 ) + timedelta( minutes = 55 * ( last_cls - 1 ) ) ).strftime( "%Y%m%dT%H%M%S" )
        week = [ "SU", "MO", "TU", "WE", "TH", "FR" ]

        body = ("BEGIN:VEVENT\n"
                 "DTSTART:%s\n"
                 "DTEND:%s\n"
                 "DTSTAMP:%s\n"
                 "CREATE:%s\n"
                 "RRULE:FREQ=WEEKLY;COUNT=%s;WKST=SU;BYDAY=%s\n"
                 "LOCATION:%s\n"
                 "SUMMARY:%s\n"
                 "END:VEVENT\n" % ( start_time, end_time, first_day_s, first_day_s, len, week[ week_pos ], location, course_name ) )
        file.write( body )

    file.write( 'END:VCALENDAR\n' )

if __name__=="__main__":
    username = "11331168"
    password = "08061031"
    year = "2013-2014"
    term = "2"
    start_date = datetime( 2013, 9, 16 )

    course_list = get_table( username, password, year, term )
    convert_to_ics( start_date, course_list )
