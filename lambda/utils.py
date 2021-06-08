
def init_session_attributes_for_user(session, user_id):
    session.attributes = dict()
    session.attributes["user_id"] = user_id
    session.attributes["categories"] = []
    session.attributes["flashcards"] = []
    session.attributes["current_card"] = 0
    session.attributes["test_started"] = False
    
def get_session(handler_input):
    return handler_input.request_envelope.session