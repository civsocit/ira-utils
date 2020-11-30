import pytest
import logging

from statistics import get_statistics
from youtube import Comment

comments = [
    Comment('UC5DqQh9__HKLd_HpDAXxsVw', 'verpkNic3SM', 'UCv3WZQIAXeprUopgMDWLvmQ', 'comment 1_1', 'UgxOzzAuLUP__6ye9xx4AaABAg'),
    Comment('UC5DqQh9__HKLd_HpDAXxsVw', 'verpkNic3SM', 'UCv3WZQIAXeprUopgMDWLvmQ', 'comment 1_2', 'Ugye-3kXWc2wVMImx-R4AaABAg'),
    Comment('UC5DqQh9__HKLd_HpDAXxsVw', 'verpkNic3SM', 'UCSTJ4D8krCXQLq3_-V9ZYWg', 'comment 2_1', 'UgxxCXicAggdvs42ted4AaABAg')
]

def test_comments_counter():
    stats = get_statistics(comments, [])

    assert stats['UCv3WZQIAXeprUopgMDWLvmQ']['UC5DqQh9__HKLd_HpDAXxsVw'] == 2
    assert stats['UCSTJ4D8krCXQLq3_-V9ZYWg']['UC5DqQh9__HKLd_HpDAXxsVw'] == 1

def test_igore_users_comments():
    stats = get_statistics(comments, ['UCv3WZQIAXeprUopgMDWLvmQ'])

    assert 'UCv3WZQIAXeprUopgMDWLvmQ' not in stats
