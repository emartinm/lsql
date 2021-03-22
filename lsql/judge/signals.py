"""
Module for signals
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.contrib.auth import get_user_model

from .models import NumSolvedAchievementDefinition, ObtainedAchievement, PodiumAchievementDefinition,\
    NumSolvedCollectionAchievementDefinition


@receiver(post_save, sender=NumSolvedAchievementDefinition)
def refresh_solved_achievements(sender, **_):
    """Delete and check new and old NumSolvedAchievementDefinition achievements"""
    all_achievements_definitions = sender.objects.all()
    for ach in all_achievements_definitions:
        ObtainedAchievement.objects.filter(achievement_definition=ach).delete()
    all_users = get_user_model().objects.all()
    for user in all_users:
        for achievement in all_achievements_definitions:
            if not achievement.check_user(user):
                achievement.check_and_save(user)


@receiver(post_save, sender=PodiumAchievementDefinition)
def refresh_podium_achievements(sender, **_):
    """Delete and check new and old PodiumAchievementDefinition achievements"""
    all_achievements_definitions = sender.objects.all()
    for ach in all_achievements_definitions:
        ObtainedAchievement.objects.filter(achievement_definition=ach).delete()
    all_users = get_user_model().objects.all()
    for user in all_users:
        for achievement in all_achievements_definitions:
            if not achievement.check_user(user):
                achievement.check_and_save(user)


@receiver(post_save, sender=NumSolvedCollectionAchievementDefinition)
def refresh_collection_achievements(sender, **_):
    """Delete and check new and old NumSolvedCollectionAchievementDefinition achievements"""
    all_achievements_definitions = sender.objects.all()
    for ach in all_achievements_definitions:
        ObtainedAchievement.objects.filter(achievement_definition=ach).delete()
    all_users = get_user_model().objects.all()
    for user in all_users:
        for achievement in all_achievements_definitions:
            if not achievement.check_user(user):
                achievement.check_and_save(user)
