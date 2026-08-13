import uuid

from django.shortcuts import render


def home(request):
    """Serve the proctoring page with a fresh session id.

    The id names the WebSocket route and the folder its artefacts land in, so a
    reload starts a clean session rather than appending to the previous one.
    """
    return render(request, 'camera/home.html', {
        'session_id': uuid.uuid4().hex[:12],
    })
