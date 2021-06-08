import requests

def init_session_attributes_for_user(session_attr, user_id):
    session_attr["user_id"] = user_id
    session_attr["categories"] = []
    session_attr["flashcards"] = []
    session_attr["current_card"] = 0
    session_attr["test_started"] = False
    
def get_session(handler_input):
    return handler_input.request_envelope.session

def get_session_attr(handler_input):
    return handler_input.attributes_manager.session_attributes

def do_get_request(full_url, session):
    headers = {'Authorization': 'Bearer ' + session.user.access_token}
    return requests.get(full_url, headers=headers)