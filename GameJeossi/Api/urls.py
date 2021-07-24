from django.conf.urls import url
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import registration_view, login_view, logout_view, create_card, ProfileCardListView, user_info, match_list, message_list, like_card, unmatch, send_message, delete_card


urlpatterns = [
    path('register', registration_view, name="register"),
    path('login', login_view, name="login"),
    path('logout', logout_view, name="logout"),
    path('authtoken', obtain_auth_token, name="authtoken"),
    
    path('create', create_card, name="create"),
    path('like', like_card, name="like"),
    
    path('unmatch', unmatch, name="unmatch"),
    path('match', match_list, name="match"),
    
    path('delete', delete_card, name="delete"),
    path('send', send_message, name="send"),
    path('info', user_info, name="info"),

    path('messages/<int:sender>/<int:receiver>', message_list, name='message'),
    path('list', ProfileCardListView.as_view(), name="list"),
]
