# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2021

Methods for obtaining statistical information about submissions
"""
from collections import Counter
from statistics import mean, stdev, quantiles

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.contrib.auth.models import Group

from .models import Submission
from .types import VerdictCode


def submissions_by_day(start=None, end=None, verdict_code=None):
    """ Returns a list [[epoch in milliseconds, count of submissions]] summing the number of submissions of some
        verdict in the range of days [start, end] expressed as epoch in milliseconds. *Used for drawing charts*
        If verdict_code is None, it counts all the submissions independently of the verdict code.
        If start is None, begins with the first submission os that verdict. If end is None, finishes with the last
        submission of that verdict. Returns an element [[epoch, 0]] for those days without submissions of that
        verdict. Ignores submissions by staff or inactive users.
    """
    active_students = get_user_model().objects.filter(is_staff=False, is_active=True)
    codes = VerdictCode.values if verdict_code is None else [verdict_code]
    subs = Submission.objects.filter(verdict_code__in=codes, user__in=active_students).order_by("pk")

    # List of epochs at 00:00 (in milliseconds) of each day for every submission
    days = list(map(lambda d: int(d.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()) * 1000,
                    subs.values_list('creation_date', flat=True)))
    if not days:
        # No submissions
        return []

    first = days[0] if start is None else start
    last = days[-1] if end is None else end
    counter = Counter(days)
    # counter[day] returns 0 if 'day' does not appear in the counter
    return [[day, counter[day]] for day in range(first, last + 1, 24 * 60 * 60 * 1000)]


def submission_count():
    """ Counts the number of submission grouped by verdict_code and also the total. Ignores submissions by staff
        or inactive users. Return a dictionary {verdict_code: int, 'all': int} considering all the verdict codes
        defined, even if they are not related to any submission (value of 0)
    """
    active_students = get_user_model().objects.filter(is_staff=False, is_active=True)
    counter = (Submission.objects.filter(user__in=active_students)
               .values('verdict_code').annotate(count=Count('verdict_code')))
    result = {k: 0 for k in VerdictCode.values}
    counts = {entry['verdict_code']: entry['count'] for entry in counter}
    result.update(counts)  # Keep all verdict_codes, even those withouth submissions (value of 0)
    result['all'] = sum(result.values())
    return result


def participation_per_group():
    """ Returns a dictionary with information for each group
        {
            group: {
                'participating': int,  # number of participating users
                'acc': int,            # no. users with at least one AC submission
                'all': int             # total no. users
                'total': int           # total number of submissions,
                'avg': float           # avg. submission per participating user
                'stdev': float         # stdev of submissions per participating user
                'quantiles': float     # cut points 0%-25%-50%-75%-100% of submissions per participating user
            }
        }
        Users are considered "participating" if they have sent one submission, and only non-staff and active users
        are counted.
    """
    participating = {}
    for group in Group.objects.all():
        users = group.user_set.filter(is_staff=False, is_active=True)
        if len(users) == 0:
            # Do not compute statistics for groups without students (non-staff active accounts)
            continue
        participating_count = Submission.objects.filter(user__in=users).order_by('user').distinct('user').count()
        acc_count = (Submission.objects.filter(verdict_code=VerdictCode.AC, user__in=users).order_by('user')
                     .distinct('user').count())
        # Statistics of submissions per user
        subs_per_user = (Submission.objects.filter(user__in=users).values('user').annotate(count=Count('user')))
        list_num_subs = [entry['count'] for entry in subs_per_user]
        participating[group.name] = {
            'participating': participating_count,
            'all': users.count(),
            'total': sum(list_num_subs),
            'acc': acc_count,
            'avg': mean(list_num_subs) if list_num_subs else float('nan'),
            'stdev': stdev(list_num_subs) if len(list_num_subs) >= 2 else float('nan'),
            'quantiles': ' - '.join(map(str, [min(list_num_subs)] + quantiles(list_num_subs, n=4, method='inclusive') +
                                        [max(list_num_subs)])) if len(list_num_subs) >= 5 else "N/A",
        }
    return participating
