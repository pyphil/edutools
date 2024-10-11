from django.shortcuts import render, redirect
from django.urls import reverse
from .models import InventoryItem, LibraryCategoryShelfmark, LibraryLocation, LibraryStatus, LibraryBorrowedItem
from .forms import InventoryItemForm, LibraryBorrowedItemsForm, LibraryCategoryShelfmarkNewForm
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required


def is_library_admin(user):
    return user.is_staff or user.groups.filter(name='library_admin').exists()


def is_library_assistant(user):
    return user.groups.filter(name='library_assistant').exists()


@login_required
def inventory(request):
    if request.GET.get('location'):
        current_location = request.GET.get('location')
    else:
        # use first location as default
        current_location = LibraryLocation.objects.filter().first()
        if current_location:
            current_location = int(current_location.id)

    # Get objects for location
    library_items = InventoryItem.objects.filter(location=current_location)

    # Get locations for filter
    locations = LibraryLocation.objects.all()

    # Get status for filter
    status_items = LibraryStatus.objects.all()

    # Filter by category if specified
    if request.GET.get('filter_category'):
        if request.GET.get('filter_category') != "0":
            library_items = library_items.filter(category_shelfmark=request.GET.get('filter_category'))
        current_category = request.GET.get('filter_category')
    else:
        current_category = 0

    # Filter by status if specified
    if request.GET.get('filter_status'):
        if request.GET.get('filter_status') != "0":
            library_items = library_items.filter(status=request.GET.get('filter_status'))
        current_status = request.GET.get('filter_status')
    else:
        current_status = 0

    # Filter by text if specified
    current_text = ""
    if request.GET.get('filter_text'):
        library_items = library_items.filter(author__icontains=request.GET.get('filter_text')) | library_items.filter(title__icontains=request.GET.get('filter_text')) | library_items.filter(inventory_number__icontains=request.GET.get('filter_text'))
        current_text = request.GET.get('filter_text')

    item_count = None
    if not request.GET.get('show_all'):
        # Slice the QuerySet to get the first 100 items
        item_count = library_items.count()
        if item_count <= 100:
            item_count = None
        library_items = library_items[:100]

    category_items = LibraryCategoryShelfmark.objects.all()
    return render(request, 'library_inventory.html', {
        'library_items': library_items,
        'category_items': category_items,
        'current_category': int(current_category),
        'current_text': current_text,
        'item_count': item_count,
        'locations': locations,
        'current_location': current_location,
        'status_items': status_items,
        'current_status': int(current_status),
        'library_admin': is_library_admin(request.user),
        }
    )


@login_required
@user_passes_test(is_library_admin)
def edit(request, id):
    obj = InventoryItem.objects.get(id=id)

    if request.method == 'POST':
        f = InventoryItemForm(request.POST, instance=obj)
        if f.is_valid():
            inst = f.save(commit=False)
            if request.POST.get('lost'):
                current_status, created = LibraryStatus.objects.get_or_create(name="verschwunden")
                inst.status = current_status
            elif inst.status.name == "verschwunden":
                inst.status = LibraryStatus.objects.get(name="verfügbar")
            inst.save()
            filter_category = request.GET.get('filter_category', '0')
            filter_status = request.GET.get('filter_status', '0')
            filter_text = request.GET.get('filter_text', '')
            return redirect(f"{reverse('inventory')}?filter_category={filter_category}&filter_status={filter_status}&filter_text={filter_text}")
        else:
            return render(request, 'library_edit.html', {'form': f})

    f = InventoryItemForm(instance=obj)
    return render(request, 'library_edit.html', {'form': f})


@login_required
@user_passes_test(is_library_admin)
def new(request):
    if request.method == 'POST':
        f = InventoryItemForm(request.POST)
        if f.is_valid():
            inst = f.save(commit=False)
            inst.inventory_number = inst.next_inventory_number
            location_obj = LibraryLocation.objects.get(id=request.GET.get('location'))
            inst.location = location_obj
            current_status, created = LibraryStatus.objects.get_or_create(name="verfügbar")
            inst.status = current_status
            inst.save()
            return redirect(f"{reverse('inventory')}?filter_category=&filter_text={inst.inventory_number}")
        else:
            return render(request, 'library_new.html', {'form': f})

    default_status = LibraryStatus.objects.filter().last()
    f = InventoryItemForm(initial={'status': default_status})
    return render(request, 'library_new.html', {'form': f})


@login_required
@user_passes_test(is_library_admin)
def delete(request, id):
    obj = InventoryItem.objects.get(id=id)

    if request.method == 'POST':
        if request.POST.get('delete'):
            obj.delete()
        return redirect('inventory')

    return render(request, 'library_delete.html', {'obj': obj})


@login_required
@user_passes_test(is_library_admin)
def borrow(request, id):
    if request.method == 'POST':
        f = LibraryBorrowedItemsForm(request.POST)
        if f.is_valid():
            inst = f.save(commit=False)
            inventory_item = InventoryItem.objects.get(id=id)
            inst.book = inventory_item
            inst.borrowing_date = timezone.now()
            days = int(request.POST.get('days'))
            inst.return_date = timezone.now() + timezone.timedelta(days)
            inst.save()
            new_status, created = LibraryStatus.objects.get_or_create(name='entliehen')
            inventory_item.status = new_status
            inventory_item.save()
            return redirect('inventory')
        else:
            print(f.errors.as_text())

    f = LibraryBorrowedItemsForm()
    book = InventoryItem.objects.get(id=id)
    return render(request, 'library_borrow.html', {'form': f, 'book': book})


@login_required
@user_passes_test(is_library_admin)
def returnlist(request):
    borrowed_items = LibraryBorrowedItem.objects.all()
    return render(request, 'library_returnlist.html', {'borrowed_items': borrowed_items})


@login_required
@user_passes_test(is_library_admin)
def return_book(request, id):
    if request.method == 'POST':
        obj = LibraryBorrowedItem.objects.get(id=id)
        book = InventoryItem.objects.get(id=obj.book.id)
        new_status = LibraryStatus.objects.get(name='verfügbar')
        book.status = new_status
        book.save()
        obj.delete()
        return redirect('inventory')

    obj = LibraryBorrowedItem.objects.get(id=id)
    return render(request, 'library_return.html', {'obj': obj})


@login_required
@user_passes_test(is_library_admin)
def manage_categories(request):
    if request.method == 'POST':
        if request.POST.get('delete'):
            obj = LibraryCategoryShelfmark.objects.get(id=request.POST.get('delete'))
            obj.delete()
            return redirect('manage_categories')

    categories = LibraryCategoryShelfmark.objects.all()
    return render(request, 'library_categories.html', {'categories': categories})


@login_required
@user_passes_test(is_library_admin)
def new_category(request):
    if request.method == 'POST':
        f = LibraryCategoryShelfmarkNewForm(request.POST)
        if f.is_valid():
            f.save()
            return redirect('manage_categories')
        else:
            return render(request, 'library_new_category.html', {'form': f})

    f = LibraryCategoryShelfmarkNewForm()
    return render(request, 'library_new_category.html', {'form': f})


@login_required
@staff_member_required
def book_import(request):
    if request.method == 'POST':
        books = request.POST.get('books').split('\n')
        for book in books:
            i = book.split(';')
            obj_category_shelfmark, category_created = LibraryCategoryShelfmark.objects.get_or_create(category=i[2])
            if category_created:
                obj_category_shelfmark.shelfmark = i[3]
                obj_category_shelfmark.save()
            obj_location, created = LibraryLocation.objects.get_or_create(name=i[5].strip())
            obj_status, created = LibraryStatus.objects.get_or_create(name="verfügbar")
            InventoryItem.objects.create(
                author=i[0],
                title=i[1],
                category_shelfmark=obj_category_shelfmark,
                inventory_number=i[4],
                location=obj_location,
                status=obj_status
            )
        return redirect('inventory')

    return render(request, 'library_import.html', {})
