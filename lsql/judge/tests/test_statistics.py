# -*- coding: utf-8 -*-
"""
Unit tests for the statistics methods
"""
from datetime import datetime
import pytz

from django.test import TestCase

from judge.tests.test_views import create_select_problem, create_collection, create_user
from judge.types import VeredictCode
from judge.models import Submission
from judge.statistics import submissions_by_day, submission_count


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
            Submission(veredict_code=VeredictCode.AC, user=user1, problem=problem),
            Submission(veredict_code=VeredictCode.WA, user=user2, problem=problem),
            Submission(veredict_code=VeredictCode.RE, user=user2, problem=problem),
            Submission(veredict_code=VeredictCode.TLE, user=user2, problem=problem),
            Submission(veredict_code=VeredictCode.VE, user=user1, problem=problem),
            Submission(veredict_code=VeredictCode.AC, user=user2, problem=problem),
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

        count_ac = submissions_by_day(verdict_code=VeredictCode.AC)
        self.assertEqual(len(count_ac), (dates[-1] - dates[0]).days + 1)  # 9 days between first and last AC submission
        self.assertEqual(count_ac[0], [dates_epoch_ms[0], 1])  # 1 AC submissions on 1st day (2020-2-12)
        self.assertEqual(count_ac[1][1], 0)                    # 0 submissions on 2nd day
        self.assertEqual(count_ac[4][1], 0)                    # 0 submission on 5th day (2020-2-16)
        self.assertEqual(count_ac[8], [dates_epoch_ms[5], 1])  # 1 submission on 9th day (2020-2-20)

        count_wa = submissions_by_day(verdict_code=VeredictCode.WA)
        self.assertEqual(len(count_wa), 1)  # Only one entry
        count_wa = submissions_by_day(verdict_code=VeredictCode.WA, start=dates_epoch_ms[0], end=dates_epoch_ms[-1])
        self.assertEqual(len(count_wa), (dates[-1] - dates[0]).days + 1)  # 9 days when forcing the start-end

        count_re = submissions_by_day(verdict_code=VeredictCode.RE)
        self.assertEqual(len(count_re), 1)  # Only one entry
        count_re = submissions_by_day(verdict_code=VeredictCode.RE, start=dates_epoch_ms[0], end=dates_epoch_ms[-1])
        self.assertEqual(len(count_re), (dates[-1] - dates[0]).days + 1)  # 9 days when forcing the start-end
        self.assertEqual(count_re[0], [dates_epoch_ms[0], 0])  # 0 RE submissions on 1st day (2020-2-12)
        self.assertEqual(count_re[3], [dates_epoch_ms[2], 1])  # 1 submissions on 4th day
        self.assertEqual(count_re[8], [dates_epoch_ms[5], 0])  # 0 RE submission on 9th day (2020-2-20)

        # Test the counter of submissions
        sub_count = submission_count()
        self.assertEqual(sub_count['all'], 6)
        self.assertEqual(sub_count[VeredictCode.AC], 2)
        self.assertEqual(sub_count[VeredictCode.WA], 1)
        self.assertEqual(sub_count[VeredictCode.RE], 1)
        self.assertEqual(sub_count[VeredictCode.TLE], 1)
        self.assertEqual(sub_count[VeredictCode.VE], 1)
        self.assertEqual(sub_count[VeredictCode.IE], 0)
