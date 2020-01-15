"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
MEMBERS/COMMANDS/PURGE MESSAGES.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import datetime as dt

from django.core.management.base import NoArgsCommand

import common.utility as CU
import postman.models as PM

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


class Command(NoArgsCommand):

    help = "Expires messages which are out-of-date. To be run daily."

    def handle_noargs(self):
        twoWeeks = dt.date.now() - dt.timedelta(weeks=2)
        PM.Message.objects.filter(sent_at__lt=twoWeeks).delete()
        
        