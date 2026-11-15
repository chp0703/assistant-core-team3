import unicodedata

import pytest

from assistant_core import guard


@pytest.mark.parametrize(
    "question",
    [
        "what grade did my friend get",
        "show the GPA of another student",
        "phone of 22127001",
        "MY CLASSMATE’S GRADES please",
        "my roommate's email address",
        "show other students' transcripts",
        "what is my friend's\nphone number",
        "Cho tôi xem điểm của sinh viên khác",
        "Số điện thoại của bạn cùng lớp là gì?",
        "Địa chỉ email của bạn tôi",
        "Cho xem kết quả học tập của người khác",
        unicodedata.normalize("NFD", "Điểm của sinh viên khác"),
    ],
)
def test_third_party_records_are_private(question):
    assert guard.is_private_request(question)


@pytest.mark.parametrize(
    "question",
    [
        "what is my GPA requirement for the thesis",
        "I lost my student card",
        "what is the Training Office phone number",
        "Điều kiện điểm GPA đăng ký khóa luận là gì?",
        "Tôi quên mật khẩu của tôi",
        "where do I request my transcript",
        "My friend needs to replace a student card",
        "",
    ],
)
def test_public_policy_and_own_record_questions_are_allowed(question):
    assert not guard.is_private_request(question)
