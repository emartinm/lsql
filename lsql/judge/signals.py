"""
Module for signals
"""
from logzero import logger

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import NumSolvedAchievementDefinition, PodiumAchievementDefinition,\
    NumSolvedCollectionAchievementDefinition, NumSolvedTypeAchievementDefinition,\
    NumSubmissionsProblemsAchievementDefinition, Hint, SelectProblem, ProcProblem, \
    DiscriminantProblem, DMLProblem, FunctionProblem, TriggerProblem, Collection


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
    if hasattr(kwargs['instance'], 'hints_info'):
        logger.debug('Saving hints: %s %s', str(sender), str(kwargs['instance']))
        save_hints(kwargs['instance'])


@receiver(post_save, sender=ProcProblem)
def save_hints_proc_problem(sender, **kwargs):
    """save Hints of a ProcProblem"""
    if hasattr(kwargs['instance'], 'hints_info'):
        logger.debug('Saving hints: %s %s', str(sender), str(kwargs['instance']))
        save_hints(kwargs['instance'])


@receiver(post_save, sender=DiscriminantProblem)
def save_hints_discriminant_problem(sender, **kwargs):
    """save Hints of a DiscriminantProblem"""
    if hasattr(kwargs['instance'], 'hints_info'):
        logger.debug('Saving hints: %s %s', str(sender), str(kwargs['instance']))
        save_hints(kwargs['instance'])


@receiver(post_save, sender=DMLProblem)
def save_hints_dml_problem(sender, **kwargs):
    """save Hints of a DMLProblem"""
    if hasattr(kwargs['instance'], 'hints_info'):
        logger.debug('Saving hints: %s %s', str(sender), str(kwargs['instance']))
        save_hints(kwargs['instance'])


@receiver(post_save, sender=FunctionProblem)
def save_hints_function_problem(sender, **kwargs):
    """save Hints of a FunctionProblem"""
    if hasattr(kwargs['instance'], 'hints_info'):
        logger.debug('Saving hints: %s %s', str(sender), str(kwargs['instance']))
        save_hints(kwargs['instance'])


@receiver(post_save, sender=TriggerProblem)
def save_hints_trigger_problem(sender, **kwargs):
    """save Hints of a TriggerProblem"""
    if hasattr(kwargs['instance'], 'hints_info'):
        logger.debug('Saving hints: %s %s', str(sender), str(kwargs['instance']))
        save_hints(kwargs['instance'])


@receiver(post_save, sender=Collection)
def add_problems_to_collection(sender, **kwargs):
    """ Adds the problems loaded from the ZIP file to the saved collection """
    collection = kwargs['instance']
    logger.debug('Signal post_save for %s %s', str(sender), collection)
    if hasattr(collection, 'problems_from_zip'):
        for problem in collection.problems_from_zip:
            problem.collection = collection
            problem.author = collection.author
            # Problems have been already cleaned when loading from the collection ZIP
            problem.save()
            logger.debug('Added problem %s "%s" from ZIP (batch) to collection %s',
                         type(problem), problem, kwargs['instance'])
