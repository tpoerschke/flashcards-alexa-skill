
def init_session_attributes_for_user(session, user_id):
    session.attributes["categories"] = []
    session.attributes["flashcards"] = []
    session.attributes["current_card"] = 0
    session.attributes["test_started"] = False
