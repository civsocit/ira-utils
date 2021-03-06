import inspect
import logging
from statistics import export_statistics, get_statistics

import pytest
import pytest_mock

from youtube import Comment

comments = [
    Comment(
        "UC5DqQh9__HKLd_HpDAXxsVw",
        "verpkNic3SM",
        "UCv3WZQIAXeprUopgMDWLvmQ",
        "comment 1_1",
        "UgxOzzAuLUP__6ye9xx4AaABAg",
    ),
    Comment(
        "UC5DqQh9__HKLd_HpDAXxsVw",
        "verpkNic3SM",
        "UCv3WZQIAXeprUopgMDWLvmQ",
        "comment 1_2",
        "Ugye-3kXWc2wVMImx-R4AaABAg",
    ),
    Comment(
        "UC5DqQh9__HKLd_HpDAXxsVw",
        "verpkNic3SM",
        "UCSTJ4D8krCXQLq3_-V9ZYWg",
        "comment 2_1",
        "UgxxCXicAggdvs42ted4AaABAg",
    ),
    Comment(
        "UC5DqQh9__HKLd_HpDAXxsVw",
        "verpkNic3SM",
        "UC5DqQh9__HKLd_HpDAXxsVw",
        "comment 3_1",
        "UgxxCXicAggdvs42ted4AaABAg",
    ),
]


def test_comments_counter():
    stats = get_statistics(comments, [])

    assert (
        stats["UCv3WZQIAXeprUopgMDWLvmQ"]["UC5DqQh9__HKLd_HpDAXxsVw"]["verpkNic3SM"]
        == 2
    )
    assert (
        stats["UCSTJ4D8krCXQLq3_-V9ZYWg"]["UC5DqQh9__HKLd_HpDAXxsVw"]["verpkNic3SM"]
        == 1
    )


def test_ignore_channel_comments_on_itself():
    stats = get_statistics(comments, [])

    assert "UC5DqQh9__HKLd_HpDAXxsVw" not in stats


def test_ignore_comments_of_specified_users():
    stats = get_statistics(comments, ignore_users=["UCv3WZQIAXeprUopgMDWLvmQ"])

    assert "UCv3WZQIAXeprUopgMDWLvmQ" not in stats


def test_ignore_comments_of_not_specified_users():
    stats = get_statistics(comments, use_only_users=["UCSTJ4D8krCXQLq3_-V9ZYWg"])

    assert len(stats.keys()) == 1
    assert list(stats.keys())[0] == "UCSTJ4D8krCXQLq3_-V9ZYWg"


def test_export_to_csv(mocker):
    stats = get_statistics(comments, [])

    mocked_file = mocker.patch("builtins.open", mocker.mock_open())
    export_statistics(stats, "fake.csv")

    mocked_file.assert_called_with("fake.csv", "w", encoding="utf-8")
    mocked_file().write.assert_any_call("user_id\tchannel\tvideo\tcomments\r\n")
    mocked_file().write.assert_any_call(
        "UCv3WZQIAXeprUopgMDWLvmQ\tUC5DqQh9__HKLd_HpDAXxsVw\t\t2\r\n"
    )
    mocked_file().write.assert_any_call(
        "UCSTJ4D8krCXQLq3_-V9ZYWg\tUC5DqQh9__HKLd_HpDAXxsVw\t\t1\r\n"
    )
