"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
COMMON/VIEWS.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from django.shortcuts import render

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
HTML PAGE REQUESTS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


def not_found(request):
    return render(request, 'not_found.html')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""