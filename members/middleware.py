"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
MEMBERS/MIDDLEWARE.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import threading


# adds the request object as a global variable of the current thread
# the request can then be accessed anywhere down the request-response cycle
# used to track user log in
class RequestMiddleware(object):

    thread_local = threading.local()
    
    # this is one of the methods required by a middleware class
    def process_request(self, request):
        RequestMiddleware.thread_local.request = request





