from django.test import TestCase
from lists.models import Item, List
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


class ItemModelTest(TestCase):
    '''тест модели элемента'''

    def test_default_text(self):
        '''тест заданного по умолчанию текста'''
        item = Item()
        self.assertEqual(item.text, '')

    def test_item_is_related_to_list(self):
        '''тест: элемент связан со списком'''
        list_ = List.objects.create()
        item = Item()
        item.list = list_
        item.save()
        self.assertIn(item, list_.item_set.all())

    def test_cannot_save_empty_list_items(self):
        '''тест: нельзя добавлять пустые элементы списка'''
        list_ = List.objects.create()
        item = Item(list=list_, text='')
        with self.assertRaises(ValidationError):
            item.save()
            item.full_clean()

    def test_duplicate_items_are_invalid(self):
        '''тесты: повторы элементов не допустимы'''
        list_ = List.objects.create()
        Item.objects.create(list=list_, text='The first list item')
        with self.assertRaises(ValidationError):
            item = Item(list=list_, text='The first list item')
            item.full_clean()

    def test_CAN_save_same_item_to_different_lists(self):
        '''тест: МОЖЕТ сохранить тот же элемент в разные списки'''
        list1 = List.objects.create()
        list2 = List.objects.create()
        Item.objects.create(list=list1, text='The first list item')
        item = Item(list=list2, text='The first list item')
        item.full_clean()  # не должен поднять исключение

    def test_list_ordering(self):
        '''тест упорядочевания списка'''
        list1 = List.objects.create()
        item1 = Item.objects.create(list=list1, text='i1')
        item2 = Item.objects.create(list=list1, text='item 2')
        item3 = Item.objects.create(list=list1, text='3')
        self.assertEqual(
            list(Item.objects.all()),
            [item1, item2, item3]
        )

    def test_string_representation(self):
        '''тест строкового представления'''
        item = Item(text='some text')
        self.assertEqual(str(item), 'some text')


class ListModelTest(TestCase):
    '''тест модели списка'''

    def test_get_absolute_url(self):
        '''тест: получен абсолютный url'''
        list_ = List.objects.create()
        self.assertEqual(list_.get_absolute_url(), f'/lists/{list_.id}/')

    def test_lists_can_have_owners(self):
        '''тест: списки могут иметь владельцев'''
        user = User.objects.create(email='a@b.com')
        list_ = List.objects.create(owner=user)
        self.assertIn(list_, user.list_set.all())

    def test_list_owner_is_optional(self):
        '''тест: владелец списка является необязательным'''
        List.objects.create()  # не должно поднять исключение

    def test_list_can_shared(self):
        '''тест: списком можно поделиться'''
        owner = User.objects.create(email='a1@b.com')
        user = User.objects.create(email='a@b.com')
        list_ = List.objects.create(owner=owner)
        list_.shared_with.add(user.email)
        self.assertIn(user, list_.shared_with.all())

    def test_list_contain_only_add_users(self):
        '''тест: список содержит только добавленных пользователей-совладельцев'''
        owner = User.objects.create(email='a@b.com')
        user1 = User.objects.create(email='a1@b.com')
        user2 = User.objects.create(email='a2@b.com')
        list_ = List.objects.create(owner=owner)
        list_.shared_with.add(user1.email)
        self.assertIn(user1, list_.shared_with.all())
        self.assertNotIn(owner, list_.shared_with.all())
        self.assertNotIn(user2, list_.shared_with.all())
