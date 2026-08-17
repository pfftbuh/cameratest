import uuid

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# The proctoring session must belong to an identifiable student, otherwise the
# CSV log and evidence clips it produces cannot be attributed to anyone.
@login_required
def home(request):
    """Serve the proctoring page with a fresh session id.

    The id names the WebSocket route and the folder its artefacts land in, so a
    reload starts a clean session rather than appending to the previous one.
    """
    return render(request, 'camera/home.html', {
        'session_id': uuid.uuid4().hex[:12],
        'user_role': request.user.role,
        'exam_id': request.session.get('current_exam_id', None),
    })
