from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordChangeDoneView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    # Полный адрес страницы регистрации - auth/signup/,
    # но префикс auth/ обрабатывется в головном urls.py
    path('signup/', views.SignUp.as_view(), name='signup'),
    path(
        'logout/',
        # Шабло для отображения возвращаемой страницы.
        LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'
    ),
    path(
        'login/',
        LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path(
        'password_change/',
        PasswordResetView.as_view(),
        name='password_change'
    ),
    path(
        'password_change/done',
        PasswordChangeDoneView.as_view(),
        name='password_change_done'
    ),
    path(
        'password_reset',
        PasswordResetView.as_view(),
        name='password_reset'
    ),
    path(
        'password_reset/done',
        PasswordResetDoneView.as_view(),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(),
        name='password_confirm'
    ),
    path(
        'reset/done/',
        PasswordResetCompleteView.as_view(),
        name='password_complete'
    ),
]
