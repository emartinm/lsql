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


@receiver(post_save, sender=SelectProblem)
def save_hints_select_problem(**kwargs):
    """save Hints of a SelectProblem"""
    for elem in kwargs['instance'].hints_info:
        num_sub = int(elem[0])
        description = elem[1]
        hint = Hint(text_md=description, problem=kwargs['instance'], num_submit=num_sub)
        hint.save()


@receiver(post_save, sender=ProcProblem)
def save_hints_proc_problem(**kwargs):
    """save Hints of a ProcProblem"""
    for elem in kwargs['instance'].hints_info:
        num_sub = int(elem[0])
        description = elem[1]
        hint = Hint(text_md=description, problem=kwargs['instance'], num_submit=num_sub)
        hint.save()


@receiver(post_save, sender=DiscriminantProblem)
def save_hints_discriminant_problem(**kwargs):
    """save Hints of a DiscriminantProblem"""
    for elem in kwargs['instance'].hints_info:
        num_sub = int(elem[0])
        description = elem[1]
        hint = Hint(text_md=description, problem=kwargs['instance'], num_submit=num_sub)
        hint.save()


@receiver(post_save, sender=DMLProblem)
def save_hints_dml_problem(**kwargs):
    """save Hints of a DMLProblem"""
    for elem in kwargs['instance'].hints_info:
        num_sub = int(elem[0])
        description = elem[1]
        hint = Hint(text_md=description, problem=kwargs['instance'], num_submit=num_sub)
        hint.save()


@receiver(post_save, sender=FunctionProblem)
def save_hints_function_problem(**kwargs):
    """save Hints of a FunctionProblem"""
    for elem in kwargs['instance'].hints_info:
        num_sub = int(elem[0])
        description = elem[1]
        hint = Hint(text_md=description, problem=kwargs['instance'], num_submit=num_sub)
        hint.save()


@receiver(post_save, sender=TriggerProblem)
def save_hints_trigger_problem(**kwargs):
    """save Hints of a TriggerProblem"""
    for elem in kwargs['instance'].hints_info:
        num_sub = int(elem[0])
        description = elem[1]
        hint = Hint(text_md=description, problem=kwargs['instance'], num_submit=num_sub)
        hint.save()
