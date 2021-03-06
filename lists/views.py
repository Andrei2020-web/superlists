from django.shortcuts import render, redirect
from lists.models import Item, List
from lists.forms import ItemForm, ExistingListItemForm
from django.contrib.auth import get_user_model

User = get_user_model()


# Create your views here.
def home_page(request):
    '''домашняя страница'''
    return render(request, 'home.html', {'form': ItemForm()})


def view_list(request, list_id):
    '''представление списка'''
    list_ = List.objects.get(id=list_id)
    form = ExistingListItemForm(for_list=list_)

    if request.method == 'POST':
        form = ExistingListItemForm(for_list=list_, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(list_)
    return render(request, 'list.html', {'list': list_, 'form': form})


def new_list(request):
    '''новый список'''
    form = ItemForm(data=request.POST)
    if form.is_valid():
        list_ = List()
        if request.user.is_authenticated:
            list_.owner = request.user
        list_.save()
        form.save(for_list=list_)
        return redirect(list_)
    else:
        return render(request, 'home.html', {'form': form})


def my_lists(request, email):
    '''мои списки'''
    owner = User.objects.get(email=email)
    return render(request, 'my_lists.html', {'owner': owner})


def share_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    list_.shared_with.add(request.POST.get('share'))
    return redirect(list_)
