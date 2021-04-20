"""
Module for signals
"""
from logzero import logger

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import NumSolvedAchievementDefinition, PodiumAchievementDefinition,\
    NumSolvedCollectionAchievementDefinition, NumSolvedTypeAchievementDefinition,\
    NumSubmissionsProblemsAchievementDefinition


@receiver(post_save, sender=NumSolvedAchievementDefinition)
def refresh_solved_achievements(sender, **kwargs):
    """Delete and check new and old NumSolvedAchievementDefinition achievements"""
    logger.debug('Signal post_save for %s %s', str(sender), str(kwargs['instance']))
    kwargs['instance'].refresh()


@receiver(post_save, sender=PodiumAchievementDefinition)
def refresh_podium_achievements(sender, **kwargs):
    """Delete and check new and old PodiumAchievementDefinition achievements"""
    logger.debug('Signal post_save for %s %s', str(sender), str(kwargs['instance']))
    kwargs['instance'].refresh()


@receiver(post_save, sender=NumSolvedCollectionAchievementDefinition)
def refresh_collection_achievements(sender, **kwargs):
    """Delete and check new and old NumSolvedCollectionAchievementDefinition achievements"""
    logger.debug('Signal post_save for %s %s', str(sender), str(kwargs['instance']))
    kwargs['instance'].refresh()


@receiver(post_save, sender=NumSolvedTypeAchievementDefinition)
def refresh_type_achievements(sender, **kwargs):
    """Delete and check new and old NumSolvedCollectionAchievementDefinition achievements"""
    logger.debug('Signal post_save for %s %s', str(sender), str(kwargs['instance']))
    kwargs['instance'].refresh()


@receiver(post_save, sender=NumSubmissionsProblemsAchievementDefinition)
def refresh_sub_prob_achievements(sender, **kwargs):
    """Delete and check new and old NumSolvedCollectionAchievementDefinition achievements"""
    logger.debug('Signal post_save for %s %s', str(sender), str(kwargs['instance']))
    kwargs['instance'].refresh()
