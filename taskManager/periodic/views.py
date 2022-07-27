import datetime, re, json, zoneinfo, pytz, os, sys
from rest_framework.views import APIView
from rest_framework import status, authentication, permissions, parsers
from rest_framework.response import Response

from django_celery_beat.models import CrontabSchedule, PeriodicTask, IntervalSchedule

# Create your views here.


class CsrfExemptSessionAuthentication(authentication.SessionAuthentication):
    def enforce_csrf(self, request):
        return

regPattern =r'^(?#minute)(\*|(?:[0-9]|(?:[1-5][0-9]))(?:(?:\-[0-9]|\-(?:[1-5][0-9]))?|(?:\,(?:[0-9]|(?:[1-5][0-9])))*)) (?#hour)(\*|(?:[0-9]|1[0-9]|2[0-3])(?:(?:\-(?:[0-9]|1[0-9]|2[0-3]))?|(?:\,(?:[0-9]|1[0-9]|2[0-3]))*)) (?#day_of_month)(\*|(?:[1-9]|(?:[12][0-9])|3[01])(?:(?:\-(?:[1-9]|(?:[12][0-9])|3[01]))?|(?:\,(?:[1-9]|(?:[12][0-9])|3[01]))*)) (?#month)(\*|(?:[1-9]|1[012]|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(?:(?:\-(?:[1-9]|1[012]|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC))?|(?:\,(?:[1-9]|1[012]|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC))*)) (?#day_of_week)(\*|(?:[0-6]|SUN|MON|TUE|WED|THU|FRI|SAT)(?:(?:\-(?:[0-6]|SUN|MON|TUE|WED|THU|FRI|SAT))?|(?:\,(?:[0-6]|SUN|MON|TUE|WED|THU|FRI|SAT))*))$'
pattern = re.compile(regPattern)

interValPeriod = dict(
    days = IntervalSchedule.DAYS,
    hours = IntervalSchedule.HOURS,
    minutes = IntervalSchedule.MINUTES,
    seconds = IntervalSchedule.SECONDS,
    microseconds = IntervalSchedule.MICROSECONDS
)
class manageCrontab(APIView):
    permission_classes = (
        permissions.AllowAny,
    )
    parser_classes = (
        parsers.JSONParser,
    )
    authentication_classes = (
        CsrfExemptSessionAuthentication, 
        authentication.SessionAuthentication, 
        authentication.BasicAuthentication
    )
    
    def post(self, request):
        '''dataFormat = {
            "crontab":"m h dM My d",
            "timeZone":"Asia/Tehran",
        }
        '''
        try:
            # get request data
            crontab = request.data.get('crontab', None)
            assert crontab, " 'crontab' key not found"
            crontab_check = re.fullmatch(pattern, crontab)
            if crontab_check:
                crontab_parser = crontab.split(' ')
                schedule, _ = CrontabSchedule.objects.get_or_create(
                    minute=crontab_parser[0],
                    hour=crontab_parser[1],
                    day_of_month=crontab_parser[2],
                    month_of_year=crontab_parser[3],
                    day_of_week=crontab_parser[4],
                    timezone=zoneinfo.ZoneInfo(request.data.get('timeZone', None))
                )
                newTask = PeriodicTask.objects.create(
                    crontab=schedule,
                    name = "save time",
                    task = 'periodic.tasks.checkDateTime'
                )
                return Response(
                    dict(task=newTask.id),
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    dict(detail="crontab format not valid"),
                    status=status.HTTP_406_NOT_ACCEPTABLE
                )
        except Exception as e:
            return Response(
                dict(detail=str(e)),
                status=status.HTTP_400_BAD_REQUEST
            )

class managerInterval(APIView):
    permission_classes = (
        permissions.AllowAny,
    )
    parser_classes = (
        parsers.JSONParser,
    )
    authentication_classes = (
        CsrfExemptSessionAuthentication, 
        authentication.SessionAuthentication, 
        authentication.BasicAuthentication
    )

    def post(self, request):
        '''
        dataFormat = {
            "every":"",
            "period":"",
        }
        IntervalSchedule.DAYS
        IntervalSchedule.HOURS
        IntervalSchedule.MINUTES
        IntervalSchedule.SECONDS
        IntervalSchedule.MICROSECONDS
        '''
        try:
            every = request.data.get('every', None)
            period = request.data.get('period', None)
            schedule, created = IntervalSchedule.objects.get_or_create(
                every = every,
                period = interValPeriod.get(period)
            )
            newTask = PeriodicTask.objects.create(
                interval=schedule,          
                name='check Number 4',          
                task='periodic.tasks.checkStatus',  
                args=json.dumps(['arg1', 'arg2']),
                kwargs=json.dumps({
                    'be_careful': True,
                }),
                expires=datetime.datetime.now() + datetime.timedelta(minutes=10)
            )
            return Response(
                dict(tasks=newTask.id),
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                dict(detail=str(e)),
                status=status.HTTP_400_BAD_REQUEST
            )

'''
Example -> Meaning

crontab() -> Execute every minute.

crontab(minute=0, hour=0) -> Execute daily at midnight.

crontab(minute=0, hour='*/3') -> Execute every three hours: midnight, 3am, 6am, 9am, noon, 3pm, 6pm, 9pm.

crontab(minute=0,hour='0,3,6,9,12,15,18,21') -> Same as previous.

crontab(minute='*/15') -> Execute every 15 minutes.

crontab(day_of_week='sunday') -> Execute every minute (!) at Sundays.

crontab(minute='*', hour='*', day_of_week='sun') -> Same as previous.

crontab(minute='*/10', hour='3,17,22', day_of_week='thu,fri') -> Execute every ten minutes, but only between 3-4 am, 5-6 pm, and 10-11 pm on Thursdays or Fridays.

crontab(minute=0, hour='*/2,*/3') -> Execute every even hour, and every hour divisible by three. This means: at every hour except: 1am, 5am, 7am, 11am, 1pm, 5pm, 7pm, 11pm

crontab(minute=0, hour='*/5') -> Execute hour divisible by 5. This means that it is triggered at 3pm, not 5pm (since 3pm equals the 24-hour clock value of “15”, which is divisible by 5).

crontab(minute=0, hour='*/3,8-17') -> Execute every hour divisible by 3, and every hour during office hours (8am-5pm).

crontab(0, 0, day_of_month='2') -> Execute on the second day of every month.

crontab(0, 0, day_of_month='2-30/2') -> Execute on every even numbered day.

crontab(0, 0, day_of_month='1-7,15-21') -> Execute on the first and third weeks of the month.

crontab(0, 0, day_of_month='11',month_of_year='5') -> Execute on the eleventh of May every year.

crontab(0, 0,month_of_year='*/3') -> Execute every day on the first month of every quarter.
'''