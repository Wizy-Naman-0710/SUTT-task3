from django.urls import path 
from . import views 
from django.conf import settings
from django.conf.urls.static import static

app_name = 'users'

urlpatterns = [ 

    #login and logout urls 
    path('logout/', views.logout_views, name='logout'), 
    path('', views.signIn,  name='sign-in'),      

    #student urls 
    path('google/login/redirect/', views.google_login, name='google_login'), 
    path('student_info/', views.student_info, name='student_info'), 
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student_search_books/', views.student_search_books, name='student_search_books'),
    path('student_history/', views.student_history, name = 'student_history'),
    path('student_feedback/', views.student_feedback, name='student_feedback'),
    path('student_favourites/', views.student_favourites, name='student_favourites'),
    path('student_book_details/<str:book_isbn>/', views.student_book_details, name="student_book_details"),
    path('borrow_book/<str:book_isbn>/', views.borrow_book, name='borrow_book'),
    path('return_book/<str:record_id>/', views.return_book, name='return_book'),
    path('reissue_book/<str:record_id>/', views.reissue_book, name='reissue_book'),
    path('add_favourite/<str:book_isbn>/', views.add_favourite, name='add_favourite'),
    path('remove_favourite/<str:book_isbn>/', views.remove_favourite, name='remove_favourite'),

    
    #admin_urls 
    path('admin_dashboard/', views.admin_dashboard, name="admin_dashboard"),
    path('admin_add_books/', views.admin_add_books, name='admin_add_books'),
    path('download_excel/', views.download_excel, name='download_excel'),
    path('admin_edit_book/', views.admin_edit_book, name = 'admin_edit_book'),
    path('admin_feedback/', views.admin_feedback, name='admin_feedback'),
    path('admin_book_details/<str:book_isbn>/', views.admin_book_details, name="admin_book_details"),
    path('admin_change_details/<str:book_isbn>/', views.admin_change_details, name="admin_change_details"),
    path('delete_book/<str:book_isbn>/', views.delete_book, name='delete_book'),
    path('add_book_info/', views.add_book_info, name='add_book_info'),
    path('admin_chat/<str:bits_id>/', views.admin_chat, name='admin_chat'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)