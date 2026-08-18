import uuid

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# The proctoring session must belong to an identifiable student, otherwise the
# CSV log and evidence clips it produces cannot be attributed to anyone.
@login_required
def home(request):
    """Serve the proctoring page using the existing proctoring session id.

    If coming from exam flow, reuse the proctoring_session_id so calibration
    and exam share the same session. Otherwise generate a new id for standalone use.
    """
    # Reuse existing proctoring session if available (from exam flow)
    session_id = request.session.get('proctoring_session_id')
    
    # Generate new session only if not in exam flow
    if not session_id:
        session_id = uuid.uuid4().hex[:12]
        request.session['proctoring_session_id'] = session_id
    
    return render(request, 'camera/home.html', {
        'session_id': session_id,
        'user_role': request.user.role,
        'exam_id': request.session.get('current_exam_id', None),
    })
