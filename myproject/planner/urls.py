from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('password_reset/', views.password_reset_view, name='password_reset'),
    path('my_page/', views.my_page_view, name='my_page'),
    path('my_schedule/', views.my_schedule_view, name='my_schedule'),
    path('schedule/<int:plan_no>/delete/', views.schedule_delete_view, name='schedule_delete'),
    path('schedule/<int:plan_no>/', views.schedule_detail_view, name='schedule_detail'),
    path('update_profile/', views.update_profile_view, name='update_profile'),
    path('delete_profile/', views.delete_profile_view, name='delete_profile'),
    path('plan_schedule/', views.plan_schedule_view, name='plan_schedule'),
    path('save_schedule/', views.save_schedule_view, name='save_schedule'),
    path('update_destination/', views.update_destination_view, name='update_destination'),
    # 게시판 관련 URL
    path('board/', views.board_list, name='board_list'),
    path('board/create/', views.board_create, name='board_create'),
    path('board/<int:board_id>/', views.board_detail, name='board_detail'),
    path('board/<int:board_id>/update/', views.board_update, name='board_update'),
    path('board/<int:board_id>/delete/', views.board_delete, name='board_delete'),
    # 댓글 관련 URL
    path('board/<int:board_id>/comment/create/', views.comment_create, name='comment_create'),
    path('comment/<int:comment_id>/delete/', views.comment_delete, name='comment_delete'),
    path('comment/<int:comment_id>/update/', views.comment_update, name='comment_update'),

    path('search/', views.search_view, name='search'),
    path("chatbot/", views.chatbot, name="chatbot"),
]