"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
PROJECT/ROUTING.py      (urls file for channels)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from channels.routing import route

import members.consumers as MM

channel_routing = [
    
    route("websocket.connect",  MM.ws_add, path=r"^/members/global_chat/$"),
    route("websocket.receive",  MM.ws_message, path=r"^/members/global_chat/$"),
    route("websocket.disconnect",  MM.ws_drop, path=r"^/members/global_chat/$"),
    
]



