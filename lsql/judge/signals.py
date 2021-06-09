"""
Module for signals
"""
from logzero import logger

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import NumSolvedAchievementDefinition, PodiumAchievementDefinition,\
    NumSolvedCollectionAchievementDefinition, NumSolvedTypeAchievementDefinition,\
    NumSubmissionsProblemsAchievementDefinition, Hint, SelectProblem, ProcProblem, \
    DiscriminantProblem, DMLProblem, FunctionProblem, TriggerProblem


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


def save_hints(problem):
    """Create the hints of a problem an save them"""
    for num_sub, description in problem.hints_info:
        hint = Hint(text_md=description, problem=problem, num_submit=num_sub)
        hint.save()


@receiver(post_save, sender=SelectProblem)
def save_hints_select_problem(sender, **kwargs):
    """save Hints of a SelectProblem"""
    logger.debug('Signal post_save for %s %s', str(sender), str(kwargs['instance']))
    if hasattr(kwargs['instance'], 'hints_info'):
        save_hints(kwargs['instance'])


@receiver(post_save, sender=ProcProblem)
def save_hints_proc_problem(sender, **kwargs):
    """save Hints of a ProcProblem"""
    logger.debug('Signal post_save for %s %s', str(sender), str(kwargs['instance']))
    if hasattr(kwargs['instance'], 'hints_info'):
        save_hints(kwargs['instance'])


@receiver(post_save, sender=DiscriminantProblem)
def save_hints_discriminant_problem(sender, **kwargs):
    """save Hints of a DiscriminantProblem"""
    logger.debug('Signal post_save for %s %s', str(sender), str(kwargs['instance']))
    if hasattr(kwargs['instance'], 'hints_info'):
        save_hints(kwargs['instance'])


@receiver(post_save, sender=DMLProblem)
def save_hints_dml_problem(sender, **kwargs):
    """save Hints of a DMLProblem"""
    logger.debug('Signal post_save for %s %s', str(sender), str(kwargs['instance']))
    if hasattr(kwargs['instance'], 'hints_info'):
        save_hints(kwargs['instance'])


@receiver(post_save, sender=FunctionProblem)
def save_hints_function_problem(sender, **kwargs):
    """save Hints of a FunctionProblem"""
    logger.debug('Signal post_save for %s %s', str(sender), str(kwargs['instance']))
    if hasattr(kwargs['instance'], 'hints_info'):
        save_hints(kwargs['instance'])


@receiver(post_save, sender=TriggerProblem)
def save_hints_trigger_problem(sender, **kwargs):
    """save Hints of a TriggerProblem"""
    logger.debug('Signal post_save for %s %s', str(sender), str(kwargs['instance']))
    if hasattr(kwargs['instance'], 'hints_info'):
        save_hints(kwargs['instance'])
