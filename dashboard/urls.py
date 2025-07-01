from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),  # default landing page
    path('my-docs/', views.my_docs_view, name='my_docs'),
    path('search/', views.global_search_view, name='global_search'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('docs/create/', views.create_doc_view, name='create_doc'),
    path('docs/<int:doc_id>/edit/', views.edit_doc_view, name='edit_doc'),
    path('docs/<int:doc_id>/delete/', views.delete_doc_view, name='delete_doc'),
    path('search/', views.global_search_view, name='global_search'),
    path('docs/<int:doc_id>/download/', views.download_doc_view, name='download_doc'),

]
