from django.test import TestCase
from lists.models import Item, List
from django.utils.html import escape
from lists.forms import (ItemForm, EMPTY_ITEM_ERROR, DUPLICATE_ITEM_ERROR,
                         ExistingListItemForm)
from django.contrib.auth import get_user_model

User = get_user_model()


class HomePageTest(TestCase):
    '''тест домашней страницы'''

    def test_home_page_returns_correct_html(self):
        '''тест: используется домашний шаблон'''
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')

    def test_home_page_uses_item_form(self):
        '''тест: домашняя страница использует форму для элемента'''
        response = self.client.get('/')
        self.assertIsInstance(response.context['form'], ItemForm)


class ListViewTest(TestCase):
    '''тест представления списка'''

    def test_displays_only_items_for_that_list(self):
        '''тест: отображаются элементы только для этого списка'''
        correct_list = List.objects.create()
        Item.objects.create(text='itemey 1', list=correct_list)
        Item.objects.create(text='itemey 2', list=correct_list)

        response = self.client.get(f'/lists/{correct_list.id}/')

        self.assertContains(response, 'itemey 1')
        self.assertContains(response, 'itemey 2')
        self.assertNotContains(response, 'another item 1 list')
        self.assertNotContains(response, 'another item 2 list')

    def test_uses_list_template(self):
        '''тест: используется шаблон списка'''
        list_ = List.objects.create()
        response = self.client.get(f'/lists/{list_.id}/')
        self.assertTemplateUsed(response, 'list.html')

    def test_passes_correct_list_to_template(self):
        '''тест: передаётся правильный шаблон списка'''
        other_list = List.objects.create()
        correct_list = List.objects.create()
        response = self.client.get(f'/lists/{correct_list.id}/')
        self.assertEqual(response.context['list'], correct_list)

    def test_can_save_a_POST_request_to_an_existing_list(self):
        '''тест: можно сохранить post запрос в существующий список'''
        other_list = List.objects.create()
        correct_list = List.objects.create()

        self.client.post(
            f'/lists/{correct_list.id}/',
            data={'text': 'A new item for an existing list'}
        )
        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new item for an existing list')
        self.assertEqual(new_item.list, correct_list)

    def test_POST_redirects_to_list_view(self):
        '''тест: post-запрос переадресуется в представление списка'''
        other_list = List.objects.create()
        correct_list = List.objects.create()

        response = self.client.post(
            f'/lists/{correct_list.id}/',
            data={'text': 'A new item for an existing list'}
        )
        self.assertRedirects(response, f'/lists/{correct_list.id}/')

    def post_invalid_input(self):
        '''отправляет недопустимый ввод'''
        list_ = List.objects.create()
        return self.client.post(f'/lists/{list_.id}/', data={'text': ''})

    def test_for_invalid_input_nothing_saved_to_db(self):
        '''тест на недопустимый ввод: ничего не сохраняется в бд'''
        self.post_invalid_input()
        self.assertEqual(Item.objects.count(), 0)

    def test_for_invalid_input_passes_form_to_template(self):
        '''тест на недопустимый ввод: форма передаётся в шаблон'''
        response = self.post_invalid_input()
        self.assertIsInstance(response.context['form'], ExistingListItemForm)

    def test_for_invalid_input_renders_list_template(self):
        '''тест на недопустимый ввод: отображается шаблон списка'''
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'list.html')

    def test_for_invalid_input_passes_form_template(self):
        '''тест на недопустимый ввод: форма передаётся в шаблон'''
        response = self.post_invalid_input()
        self.assertIsInstance(response.context['form'], ItemForm)

    def test_for_invalid_input_shows_error_on_page(self):
        '''тест на недопустимый ввод: на странице показывается ошибка'''
        response = self.post_invalid_input()
        self.assertContains(response, escape(EMPTY_ITEM_ERROR))

    def test_displays_item_forms(self):
        '''тест отображения формы для элемента'''
        list_ = List.objects.create()
        response = self.client.get(f'/lists/{list_.id}/')
        self.assertIsInstance(response.context['form'], ExistingListItemForm)
        self.assertContains(response, 'name="text"')

    def test_duplicate_item_validation_errors_end_up_on_lists_page(self):
        '''тест: ошибки валидации повторяющегося элемента
            оканчиваются на странице списков'''
        list1 = List.objects.create()
        item1 = Item.objects.create(list=list1, text='textey')
        response = self.client.post(
            f'/lists/{list1.id}/', data={'text': 'textey'}
        )

        expected_error = escape(DUPLICATE_ITEM_ERROR)
        self.assertContains(response, expected_error)
        self.assertTemplateUsed(response, 'list.html')
        self.assertEqual(Item.objects.all().count(), 1)


class NewListTest(TestCase):
    '''тест нового списка'''

    def test_can_save_a_POST_request(self):
        '''тест: может сохранить post-запрос'''
        response = self.client.post('/lists/new',
                                    data={'text': 'A new list item'})
        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new list item')

    def test_redirects_after_POST(self):
        '''тест: переадресует после post-запроса'''
        response = self.client.post('/lists/new',
                                    data={'text': 'A new list item'})
        new_list = List.objects.first()
        self.assertRedirects(response, f'/lists/{new_list.id}/')

    def test_invalid_list_items_arent_saved(self):
        '''тест: не сохраняются недопустимые элементы списка'''
        self.client.post('/lists/new', data={'text': ''})
        self.assertEqual(List.objects.count(), 0)
        self.assertEqual(Item.objects.count(), 0)

    def test_for_invalid_input_renders_home_templates(self):
        '''тест на недопустимый ввод: отображает домашний шаблон'''
        response = self.client.post('/lists/new', data={'text': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_validation_errors_are_shown_on_home_page(self):
        '''тест: ошибки валидации выводятся надомашней странице'''
        response = self.client.post('/lists/new', data={'text': ''})
        self.assertContains(response, escape(EMPTY_ITEM_ERROR))

    def test_list_owner_is_saved_if_user_is_authenticated(self):
        '''тест: владелец списка сохраняется, если
        пользователь аутентифицорован'''
        user = User.objects.create(email='a@b.com')
        self.client.force_login(user)
        self.client.post('/lists/new', data={'text': 'new item'})
        list_ = List.objects.first()
        self.assertEqual(list_.owner, user)


class MyListsTests(TestCase):
    """тест представления для моих списков"""

    def test_my_lists_url_renders_my_lists_templates(self):
        '''тест: используется шаблон my_lists.html для отображения ссылок
        на мои списки'''
        User.objects.create(email='a@b.com')
        response = self.client.get('/lists/users/a@b.com/')
        self.assertTemplateUsed(response, 'my_lists.html')

    def test_passes_correct_owner_to_template(self):
        '''тест: передаётся правильный владелец списков в шаблон'''
        User.objects.create(email='wrong@owner.com')
        correct_user = User.objects.create(email='a@b.com')
        response = self.client.get('/lists/users/a@b.com/')
        self.assertEqual(response.context['owner'], correct_user)


class ShareListTest(TestCase):
    '''тест поделиться моим списком'''

    def test_post_redirects_to_lists_page(self):
        '''тест: переадресует после post-запроса на страницу списка'''
        new_list = List.objects.create()
        response = self.client.post(f'/lists/{new_list.id}/share')
        self.assertRedirects(response, f'/lists/{new_list.id}/')

    def test_user_add_in_list(self):
        '''тест: пользователь добавляется в лист'''
        owner = User.objects.create(email='a1@b.com')
        user = User.objects.create(email='a2@b.com')
        new_list = List.objects.create(owner=owner)
        self.client.post(f'/lists/{new_list.id}/share',
                         data={'share': user.email})
        self.assertIn(user, new_list.shared_with.all())

    def test_displays_only_added_users_for_that_list(self):
        '''тест: отображаются пользователи-совладельцы только для этого списка'''
        owner = User.objects.create(email='a3@b.com')
        user1 = User.objects.create(email='a4@b.com')
        user2 = User.objects.create(email='a5@b.com')
        user3 = User.objects.create(email='a6@b.com')
        list1 = List.objects.create(owner=owner)
        list2 = List.objects.create(owner=owner)
        list1.shared_with.add(user1.email)
        list1.shared_with.add(user2.email)
        list2.shared_with.add(user3.email)

        response_get_list1 = self.client.get(f'/lists/{list1.id}/')
        response_get_list2 = self.client.get(f'/lists/{list2.id}/')

        self.assertContains(response_get_list1, user1.email)
        self.assertContains(response_get_list1, user2.email)
        self.assertNotContains(response_get_list1, user3.email)

        self.assertContains(response_get_list2, user3.email)
        self.assertNotContains(response_get_list2, user1.email)
        self.assertNotContains(response_get_list2, user2.email)

    def test_my_lists_displays_shared_lists(self):
        '''тест: мои списки отображают списки, которыми со мной поделились'''
        user = User.objects.create(email='a7@b.com')
        owner = User.objects.create(email='a8@b.com')
        list = List.objects.create(owner=owner)
        list.shared_with.add(user.email)
        response = self.client.get(f'/lists/users/{user.email}/')
        self.assertContains(response, list.name)
