import pytest
from app import main as m

# ----------------------------------------------------------------------------------------------------------------------
# TestCase for perform_chat_message() validate generated message using test_date
# ----------------------------------------------------------------------------------------------------------------------
test_date1 = [
    ('xxx', [0, 1, 2, 3, 4]),
    ('yyy', [-1, 50, 99, 0, 100])
]
@pytest.mark.parametrize('test_message, test_list', test_date1)
def test_perform_chat_message(test_message, test_list):
    msg = m.perform_chat_message(test_message, test_list)
    assert msg.find(str(test_list[0])) != -1
    assert msg.find(str(test_list[1])) != -1
    assert msg.find(str(test_list[2])) != -1
    assert msg.find(str(test_list[3])) != -1
    assert msg.find(str(test_list[4])) != -1


# ----------------------------------------------------------------------------------------------------------------------
# TestCase for perform_chat_message() validate generated message using test_date
# ----------------------------------------------------------------------------------------------------------------------
test_date2 = [
    ('xxx', 3),
    ('Message', 7)
]
@pytest.mark.parametrize('test_message, result', test_date2)
def test_utf8len(test_message, result):
    assert m.utf8len(test_message) == result
#
#
def test_utf8len_new():
    assert m.utf8len(m.perform_chat_message('test_message', [0, 1, 2, 3, 4])) == 216