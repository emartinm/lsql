"""
Tests for rankings
"""

from django.test import TestCase, Client
from django.urls import reverse
from judge.models import NumSolvedCollectionAchievementDefinition, PodiumAchievementDefinition, \
    NumSolvedAchievementDefinition, AchievementDefinition
from judge.tests.test_views import create_collection, create_user, create_select_problem, create_group


def create_an_achievement_of_each(coll):
    """Create an achievement of each type: NumSolvedAchievementDefinition, PodiumAchievementDefinition and
    NumSolvedCollectionAchievementDefinition"""
    ach_podium = PodiumAchievementDefinition(name='Presidente del podio', description='Consigue entrar\
                                                    al podio', num_problems=1, position=3)
    ach_collection = NumSolvedCollectionAchievementDefinition(name='Coleccionista', description='Resuelve 1 problema\
                                                            de esta coleccion', num_problems=1, collection=coll)
    ach_solved = NumSolvedAchievementDefinition(name='Resolvista', description='Resuelve 1 problema',
                                                num_problems=1)
    ach_podium.save()
    ach_collection.save()
    ach_solved.save()


class RankingTest(TestCase):
    """Tests for the rankings"""

    def test_get_podium_achievement(self):
        """Test if get correctly a podium achievement"""
        client = Client()
        podium_achievement = PodiumAchievementDefinition(name='Top 1', description='Se el primero', num_problems=1,
                                                         position=1)
        podium_achievement.save()
        coll = create_collection('Test Podium')
        problem = create_select_problem(coll, 'Select 1')
        user = create_user('passwordmichu', 'michu')
        client.login(username='michu', password='passwordmichu')
        submit_select_url = reverse('judge:submit', args=[problem.pk])
        client.post(submit_select_url, {'code': problem.solution}, follow=True)
        achievements_url = reverse('judge:achievements', args=[user.pk])
        response = client.get(achievements_url, follow=True)
        self.assertIn('Fecha', response.content.decode('utf-8'))

    def test_get_solved_achievement(self):
        """Test if get correctly a solved achievement and check_user function"""
        client = Client()
        solved_achievement_1 = NumSolvedAchievementDefinition(name='Solo 1', description='Acierta 1', num_problems=1)
        solved_achievement_2 = NumSolvedAchievementDefinition(name='Solo 2', description='Acierta 2', num_problems=2)
        solved_achievement_1.save()
        solved_achievement_2.save()
        coll = create_collection('Test Solved')
        problem = create_select_problem(coll, 'Select 1')
        user = create_user('passwordmichu', 'michu')
        client.login(username='michu', password='passwordmichu')
        submit_select_url = reverse('judge:submit', args=[problem.pk])
        client.post(submit_select_url, {'code': problem.solution}, follow=True)
        client.post(submit_select_url, {'code': problem.solution}, follow=True)
        achievements_url = reverse('judge:achievements', args=[user.pk])
        response = client.get(achievements_url, follow=True)
        self.assertIn('Fecha', response.content.decode('utf-8'))
        self.assertIn('Logros pendientes', response.content.decode('utf-8'))

    def test_get_collection_achievement(self):
        """Test if get correctly a collection achievement"""
        client = Client()
        coll = create_collection('Test Solved')
        coll_achievement = NumSolvedCollectionAchievementDefinition(name='Solo 1', description='Acierta 1',
                                                                    num_problems=1, collection=coll)
        coll_achievement.save()
        problem = create_select_problem(coll, 'Select 1')
        user = create_user('passwordmichu', 'michu')
        client.login(username='michu', password='passwordmichu')
        submit_select_url = reverse('judge:submit', args=[problem.pk])
        client.post(submit_select_url, {'code': problem.solution}, follow=True)
        achievements_url = reverse('judge:achievements', args=[user.pk])
        response = client.get(achievements_url, follow=True)
        self.assertIn('Fecha', response.content.decode('utf-8'))

    def test_ranking_achievements(self):
        """Test if we can see the number of achievements that have an user at ranking"""
        client = Client()
        user = create_user('passwordmichu', 'michu')
        client.login(username='michu', password='passwordmichu')
        coll = create_collection('Coleccion de cartas')
        problem = create_select_problem(coll, 'Problema')
        create_an_achievement_of_each(coll)
        submit_select_url = reverse('judge:submit', args=[problem.pk])
        client.post(submit_select_url, {'code': problem.solution}, follow=True)
        ranking_url = reverse('judge:result', args=[coll.pk])
        group_a = create_group('1A')
        group_a.user_set.add(user)
        response = client.get(ranking_url, follow=True)
        self.assertIn('x3', response.content.decode('utf-8'))

    def test_not_implemented_raise_achievements(self):
        """Test if check_and_save of AchievementDefinition raise a NotImplementedError"""
        client = Client()
        user = create_user('passwordmichu', 'michu')
        client.login(username='michu', password='passwordmichu')
        achievement_definition = AchievementDefinition(name='nombre', description='descripcion')
        self.assertRaises(NotImplementedError, lambda: achievement_definition.check_and_save(user))

    def test_str_method_obtained_achievement(self):
        """Test for check if __str__ return the name of the achievement"""
        achievement_definition = AchievementDefinition(name='nombre', description='descripcion')
        self.assertEqual(str(achievement_definition), achievement_definition.name)
