import random
import string
from bot import utils, bot

# instantiate the bot
bot = bot.Bot()

# Payload for test repo
# https://github.com/Bioinformatics-Research-Network/test-bot/pull/1
payload = {
    "sender": {
        "login": "millerh1",
    },
    "comment": {
        "body": "@brnbot hello",
    },
    "installation": {
        "id": 25533349,
    },
    "issue": {
        "number": 1,
        "pull_request": {
            "url": "https://api.github.com/repos/brn-test-assessment/test-millerh1/pulls/1"
        },
    },
    "repository": {
        "owner": {
            "login": "brn-test-assessment",
        },
        "name": "test-millerh1",
    },
}


def test_get_last_commit():
    """
    Test the bot's get_last_commit command
    """
    kwarg_dict = bot.parse_comment_payload(payload)
    last_commit = utils.get_last_commit(
        owner=kwarg_dict["owner"],
        repo_name=kwarg_dict["repo_name"],
        access_token=kwarg_dict["access_token"],
    )
    # Commit should be "5859532a05b2523593ee4059c01b3ec06e3f5827" for the test repo
    assert last_commit == "5859532a05b2523593ee4059c01b3ec06e3f5827"


def test_get_assessment_name():
    """
    Test the bot's get_assessment_name command
    """
    assessment_name = utils.get_assessment_name(payload)
    # Assessment should be "test" for the test repo
    assert assessment_name == "Test"


def test_forbot():
    """
    Test the bot's forbot command
    """
    assert utils.forbot(payload)
    payload["comment"]["body"] = "@brnbottt"
    assert not utils.forbot(payload)


def test_get_recent_comments():
    """
    Test the bot's post_comment command
    """
    ## Success
    kwarg_dict = bot.parse_comment_payload(payload)
    text = "test " + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=20)
    )
    response = utils.post_comment(text=text, **kwarg_dict)
    # Comment should be posted to the test repo
    assert response.status_code == 201
    # Comment should be "test" for the test repo
    assert response.json()["body"] == text
    # Get last comment and check if it is the same as the one we posted
    comments = utils.get_recent_comments(**kwarg_dict)
    assert comments.json()[-1]["body"] == text

    ## Confirm ordering of comments is correct
    kwarg_dict = bot.parse_comment_payload(payload)
    text = "test 1 " + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=20)
    )
    utils.post_comment(text=text, **kwarg_dict)
    text2 = "test 2 " + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=20)
    )
    utils.post_comment(text=text2, **kwarg_dict)

    # Get last comment and check if it is the same as the one we posted
    comments = utils.get_recent_comments(**kwarg_dict)
    assert comments.status_code == 200
    assert comments.json()[-1]["body"] == text2
    assert comments.json()[-2]["body"] == text


def test_delete_comment():
    """
    Test the bot's delete_comment command
    """
    ## Success
    kwarg_dict = bot.parse_comment_payload(payload)
    text = "del " + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=20)
    )
    response = utils.post_comment(text=text, **kwarg_dict)
    comment_id = response.json()["id"]
    # Check if the comment was posted
    comments = utils.get_comment_by_id(comment_id, **kwarg_dict)
    assert comments.status_code == 404
    # Delete the comment
    response = utils.delete_comment(comment_id, **kwarg_dict)
    assert response.status_code == 204
    # Check if the comment is deleted
    comments = utils.get_comment_by_id(comment_id, **kwarg_dict)
    assert comments.status_code == 404

    ## Failure to delete because comment does not exist
    response = utils.delete_comment(comment_id, **kwarg_dict)
    assert response.status_code == 404


def test_reviewer_ops():
    """
    Test the bot's assign_reviewer command
    """
    kwarg_dict = bot.parse_comment_payload(payload)
    reviewer_username = "bioresnet"

    ## Remove reviewer if already assigned
    response = utils.remove_reviewer(reviewer_username=reviewer_username, **kwarg_dict)

    ## Assign reviewer
    response = utils.assign_reviewer(reviewer_username=reviewer_username, **kwarg_dict)
    # Check if the reviewer was assigned
    assert response.status_code == 201
    # Check if the reviewer is assigned
    response = utils.get_reviewer(**kwarg_dict)
    assert response.status_code == 200
    assert response.json()["users"][0]["login"] == reviewer_username
    ## Delete reviewer
    response = utils.remove_reviewer(reviewer_username=reviewer_username, **kwarg_dict)
    assert response.status_code == 200
    response = utils.get_reviewer(**kwarg_dict)
    assert response.status_code == 200
    assert response.json()["users"] == []
