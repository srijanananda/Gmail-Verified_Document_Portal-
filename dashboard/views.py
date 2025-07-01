from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Document, Notification
from .forms import DocumentForm


@login_required
def dashboard_home(request):
    return render(request, 'dashboard/home.html')


@login_required
def my_docs_view(request):
    documents = Document.objects.filter(author=request.user)
    return render(request, 'dashboard/my_docs.html', {'documents': documents})

def create_notifications(doc, tagged_users):
    for user in tagged_users:
        Notification.objects.get_or_create(
            user=user,
            document=doc,
            message=f"You were tagged in '{doc.title}'"
        )


@login_required
def create_doc_view(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.author = request.user
            doc.save()
            form.save_m2m()  # Save tags

            if doc.visibility == 'tagged':
                create_notifications(doc, doc.tags.all())

            return redirect('my_docs')
    else:
        form = DocumentForm()
    return render(request, 'dashboard/doc_form.html', {'form': form, 'action': 'Create'})


@login_required
def edit_doc_view(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id, author=request.user)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.author = request.user
            doc.save()
            form.save_m2m()

            if doc.visibility == 'tagged':
                create_notifications(doc, doc.tags.all())

            return redirect('my_docs')
    else:
        form = DocumentForm(instance=doc)
    return render(request, 'dashboard/doc_form.html', {'form': form, 'action': 'Edit'})


@login_required
def delete_doc_view(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id, author=request.user)
    if request.method == 'POST':
        doc.delete()
        return redirect('my_docs')
    return render(request, 'dashboard/confirm_delete.html', {'doc': doc})


@login_required
def global_search_view(request):
    query = request.GET.get('q', '')
    user = request.user

    my_docs = Document.objects.filter(author=user).filter(
        Q(title__icontains=query) | Q(content__icontains=query)
    )

    public_docs = Document.objects.filter(visibility='public') \
        .exclude(author=user) \
        .filter(Q(title__icontains=query) | Q(content__icontains=query))

    tagged_docs = Document.objects.filter(visibility='tagged', tags=user) \
        .exclude(author=user) \
        .filter(Q(title__icontains=query) | Q(content__icontains=query))

    context = {
        'query': query,
        'my_docs': my_docs,
        'public_docs': public_docs,
        'tagged_docs': tagged_docs
    }

    return render(request, 'dashboard/search_results.html', context)


@login_required
def notifications_view(request):
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')

    if request.method == 'POST':
        notif_id = request.POST.get("delete_id")
        Notification.objects.filter(id=notif_id, user=user).delete()
        return redirect('notifications')

    return render(request, 'dashboard/notifications.html', {'notifications': notifications})
