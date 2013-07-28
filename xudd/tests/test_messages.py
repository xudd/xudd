from xudd.message import Message


def test_message_to_dict():
    # Test without in-reply-to
    message = Message(
        to="to-uuid",
        directive="catch_ball",
        from_id="from-uuid",
        id="catch-ball-message-id",
        body={"ball_color": "green",
              "something": "orother"},
        wants_reply=True)

    dict_message = message.to_dict()
    assert isinstance(dict_message, dict)
    assert set(dict_message.keys()) == set(
        ["to", "directive", "from_id", "id", "body", "wants_reply"])

    assert dict_message["to"] == "to-uuid"
    assert dict_message["directive"] == "catch_ball"
    assert dict_message["from_id"] == "from-uuid"
    assert dict_message["id"] == "catch-ball-message-id"
    assert dict_message["body"] == {
        "ball_color": "green",
        "something": "orother"}
    assert dict_message["wants_reply"] == True

    # Test with in-reply-to
    message = Message(
        to="to-uuid",
        directive="reply",
        from_id="from-uuid",
        in_reply_to="catch-ball-message-id",
        id="caught-ball-message-id",
        body={"i_got_it": "yeah"},
        wants_reply=False)

    dict_message = message.to_dict()
    assert isinstance(dict_message, dict)
    assert set(dict_message.keys()) == set(
        ["to", "directive", "from_id", "id", "body", "wants_reply",
         "in_reply_to"])

    assert dict_message["to"] == "to-uuid"
    assert dict_message["directive"] == "reply"
    assert dict_message["from_id"] == "from-uuid"
    assert dict_message["id"] == "caught-ball-message-id"
    assert dict_message["body"] == {
        "i_got_it": "yeah"}
    assert dict_message["wants_reply"] == False
    assert dict_message["in_reply_to"] == "catch-ball-message-id"

