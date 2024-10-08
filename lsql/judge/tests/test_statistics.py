# -*- coding: utf-8 -*-
"""
Unit tests for the statistics methods
"""
from datetime import datetime
from math import isnan
import pytz

from django.test import TestCase

from judge.tests.test_common import create_select_problem, create_collection, create_user, create_group, \
    create_superuser
from judge.types import VerdictCode
from judge.models import Submission
from judge.statistics import submissions_by_day, submission_count, participation_per_group


class StatisticsTest(TestCase):
    """ Tests for judge.statistics """

    def test_all_submissions(self):
        """ Test the list [epoch, count] for different types of verdicts and days, and also the counter of submissions
        """
        collection = create_collection('Test for statistics')
        problem = create_select_problem(collection, 'Dummy for statistics')
        user1 = create_user('0000', 'ana')
        user2 = create_user('0000', 'juan')

        subs = [
            Submission(verdict_code=VerdictCode.AC, user=user1, problem=problem),
            Submission(verdict_code=VerdictCode.WA, user=user2, problem=problem),
            Submission(verdict_code=VerdictCode.RE, user=user2, problem=problem),
            Submission(verdict_code=VerdictCode.TLE, user=user2, problem=problem),
            Submission(verdict_code=VerdictCode.VE, user=user1, problem=problem),
            Submission(verdict_code=VerdictCode.AC, user=user2, problem=problem),
        ]
        dates = [
            datetime(2020, 2, 12, 0, 0, 0, 0, tzinfo=pytz.utc),
            datetime(2020, 2, 12, 0, 0, 0, 0, tzinfo=pytz.utc),
            datetime(2020, 2, 15, 0, 0, 0, 0, tzinfo=pytz.utc),
            datetime(2020, 2, 15, 0, 0, 0, 0, tzinfo=pytz.utc),
            datetime(2020, 2, 16, 0, 0, 0, 0, tzinfo=pytz.utc),
            datetime(2020, 2, 20, 0, 0, 0, 0, tzinfo=pytz.utc),
        ]
        dates_epoch_ms = [int(date.timestamp()) * 1000 for date in dates]

        for (sub, date) in zip(subs, dates):
            sub.save()
            sub.creation_date = date
            sub.save()  # Overwrites date, because it is automatically set to 'now' in the first save

        count_all = submissions_by_day()
        self.assertEqual(len(count_all), (dates[-1] - dates[0]).days + 1)  # 9 days between first and last submission
        self.assertEqual(count_all[0], [dates_epoch_ms[0], 2])  # 2 submissions on 1st day (2020-2-12)
        self.assertEqual(count_all[1][1], 0)                    # 0 submissions on 2nd day
        self.assertEqual(count_all[2][1], 0)                    # 0 submissions on 3rd day
        self.assertEqual(count_all[3], [dates_epoch_ms[2], 2])  # 2 submissions on 4th day (2020-2-15)
        self.assertEqual(count_all[4], [dates_epoch_ms[4], 1])  # 1 submission on 5th day (2020-2-16)
        self.assertEqual(count_all[6][1], 0)                    # 0 submissions on 3rd day
        self.assertEqual(count_all[8], [dates_epoch_ms[5], 1])  # 1 submission on 9th day (2020-2-20)

        count_ac = submissions_by_day(verdict_code=VerdictCode.AC)
        self.assertEqual(len(count_ac), (dates[-1] - dates[0]).days + 1)  # 9 days between first and last AC submission
        self.assertEqual(count_ac[0], [dates_epoch_ms[0], 1])  # 1 AC submissions on 1st day (2020-2-12)
        self.assertEqual(count_ac[1][1], 0)                    # 0 submissions on 2nd day
        self.assertEqual(count_ac[4][1], 0)                    # 0 submission on 5th day (2020-2-16)
        self.assertEqual(count_ac[8], [dates_epoch_ms[5], 1])  # 1 submission on 9th day (2020-2-20)

        count_wa = submissions_by_day(verdict_code=VerdictCode.WA)
        self.assertEqual(len(count_wa), 1)  # Only one entry
        count_wa = submissions_by_day(verdict_code=VerdictCode.WA, start=dates_epoch_ms[0], end=dates_epoch_ms[-1])
        self.assertEqual(len(count_wa), (dates[-1] - dates[0]).days + 1)  # 9 days when forcing the start-end

        count_re = submissions_by_day(verdict_code=VerdictCode.RE)
        self.assertEqual(len(count_re), 1)  # Only one entry
        count_re = submissions_by_day(verdict_code=VerdictCode.RE, start=dates_epoch_ms[0], end=dates_epoch_ms[-1])
        self.assertEqual(len(count_re), (dates[-1] - dates[0]).days + 1)  # 9 days when forcing the start-end
        self.assertEqual(count_re[0], [dates_epoch_ms[0], 0])  # 0 RE submissions on 1st day (2020-2-12)
        self.assertEqual(count_re[3], [dates_epoch_ms[2], 1])  # 1 submissions on 4th day
        self.assertEqual(count_re[8], [dates_epoch_ms[5], 0])  # 0 RE submission on 9th day (2020-2-20)

        # Test the counter of submissions
        sub_count = submission_count()
        self.assertEqual(sub_count['all'], 6)
        self.assertEqual(sub_count[VerdictCode.AC], 2)
        self.assertEqual(sub_count[VerdictCode.WA], 1)
        self.assertEqual(sub_count[VerdictCode.RE], 1)
        self.assertEqual(sub_count[VerdictCode.TLE], 1)
        self.assertEqual(sub_count[VerdictCode.VE], 1)
        self.assertEqual(sub_count[VerdictCode.IE], 0)

    def test_participation(self):
        """ Test the count of participating users in a group """
        group = create_group('Grupo test')
        user1 = create_user(username='u1', passwd='1111')  # nosec B106
        user2 = create_user(username='u2', passwd='1111')  # nosec B106
        user3 = create_user(username='u3', passwd='1111')  # nosec B106
        user4 = create_user(username='u4', passwd='1111')  # nosec B106
        user5 = create_user(username='u5', passwd='1111')  # nosec B106
        collection = create_collection('Test for statistics')
        problem = create_select_problem(collection, 'Dummy for statistics')

        for user in [user1, user2, user3, user4, user5]:
            group.user_set.add(user)

        subs = [
            Submission(verdict_code=VerdictCode.AC, user=user1, problem=problem),
            Submission(verdict_code=VerdictCode.VE, user=user1, problem=problem),
            Submission(verdict_code=VerdictCode.WA, user=user2, problem=problem),
            Submission(verdict_code=VerdictCode.RE, user=user2, problem=problem),
            Submission(verdict_code=VerdictCode.TLE, user=user2, problem=problem),
            Submission(verdict_code=VerdictCode.AC, user=user3, problem=problem),
            Submission(verdict_code=VerdictCode.AC, user=user4, problem=problem),
            Submission(verdict_code=VerdictCode.AC, user=user5, problem=problem),
            Submission(verdict_code=VerdictCode.AC, user=user5, problem=problem),
        ]
        for sub in subs:
            sub.save()

        data = participation_per_group()
        expected = {
            'Grupo test': {
                'all': 5,
                'acc': 4,
                'total': 9,
                'participating': 5,
                'avg': 1.8,
                'stdev': 0.8366600265340756,
                'quantiles': '1 - 1.0 - 2.0 - 2.0 - 3',
            }
        }
        self.assertDictEqual(data, expected)

    def test_participacion_small_groups(self):
        """ Test that the results for empty and small groups do not fail because avg, stdev and quantiles are
            not defined """
        create_group('empty_group')  # Should not appear in results
        only_staff_group = create_group('only_staff_group')  # Should not appear in results
        group = create_group('standard_group')
        users = [create_user(username=name, passwd='1111') for name in ['u1', 'u2', 'u3', 'u4', 'u5']]  # nosec B106
        staff_user = create_superuser(username='staff_user', passwd='1111')  # nosec B106
        collection = create_collection('Test for statistics')
        problem = create_select_problem(collection, 'Dummy for statistics')

        for user in users:
            group.user_set.add(user)
        only_staff_group.user_set.add(staff_user)

        # With 0 submissions no metric is defined
        data = participation_per_group()
        self.assertEqual(set(data.keys()), {group.name})
        self.assertTrue(isnan(data[group.name]['avg']))
        self.assertTrue(isnan(data[group.name]['stdev']))
        self.assertEqual(data[group.name]['quantiles'], 'N/A')

        # With 1 submission there is avg but not stdev or quantiles
        Submission(verdict_code=VerdictCode.AC, user=users[0], problem=problem).save()
        data = participation_per_group()
        self.assertEqual(set(data.keys()), {group.name})
        self.assertEqual(data[group.name]['avg'], 1)
        self.assertTrue(isnan(data[group.name]['stdev']))
        self.assertEqual(data[group.name]['quantiles'], 'N/A')

        # With 2, 3 and 5 submissions there are avg and stdev, but not quantiles
        for sub in [Submission(verdict_code=VerdictCode.WA, user=users[1], problem=problem),
                    Submission(verdict_code=VerdictCode.AC, user=users[2], problem=problem),
                    Submission(verdict_code=VerdictCode.AC, user=users[3], problem=problem)]:
            sub.save()
            data = participation_per_group()
            self.assertEqual(set(data.keys()), {group.name})
            self.assertEqual(data[group.name]['avg'], 1)
            self.assertEqual(data[group.name]['stdev'], 0)
            self.assertEqual(data[group.name]['quantiles'], 'N/A')

        # With 5 submissions all metrics are valid
        Submission(verdict_code=VerdictCode.AC, user=users[4], problem=problem).save()
        data = participation_per_group()
        self.assertEqual(set(data.keys()), {group.name})
        self.assertEqual(data[group.name]['avg'], 1)
        self.assertEqual(data[group.name]['stdev'], 0)
        self.assertEqual(data[group.name]['quantiles'], '1 - 1.0 - 1.0 - 1.0 - 1')
