from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Document, Notification
from .forms import DocumentForm
from django.views.decorators.cache import never_cache
from django.http import HttpResponse
from django.template.loader import render_to_string

@never_cache
@login_required
def dashboard_home(request):
    user = request.user

    public_docs = Document.objects.filter(visibility='public')
    tagged_docs = Document.objects.filter(visibility='tagged', tags=user)

    html = render_to_string('dashboard/home.html', {
        'public_docs': public_docs,
        'tagged_docs': tagged_docs,
        'request': request
    })

    response = HttpResponse(html)
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
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

@never_cache
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

@never_cache
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

@never_cache
@login_required
def delete_doc_view(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id, author=request.user)
    if request.method == 'POST':
        doc.delete()
        return redirect('my_docs')
    return render(request, 'dashboard/confirm_delete.html', {'doc': doc})

@never_cache
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

@never_cache
@login_required
def notifications_view(request):
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')

    if request.method == 'POST':
        notif_id = request.POST.get("delete_id")
        Notification.objects.filter(id=notif_id, user=user).delete()
        return redirect('notifications')

    return render(request, 'dashboard/notifications.html', {'notifications': notifications})

from django.http import FileResponse, Http404
import os

@never_cache
@login_required
def download_doc_view(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)

    # ✅ Access control
    if doc.visibility == 'private' and doc.author != request.user:
        raise Http404("Unauthorized access")

    if doc.visibility == 'tagged' and request.user not in doc.tags.all() and doc.author != request.user:
        raise Http404("Unauthorized access")

    # ✅ Check if file exists on disk
    if not doc.file or not os.path.exists(doc.file.path):
        raise Http404("File not found on disk")

    return FileResponse(doc.file.open('rb'), as_attachment=True)
