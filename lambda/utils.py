
def init_session_attributes_for_user(session, user_id):
    session.attributes["categories"] = []
    session.attributes["flashcards"] = []
    current_card = 0
    test_started = False
