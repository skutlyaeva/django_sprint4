from django.urls import path
from . import views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserChangeForm
from django.urls import reverse_lazy
from django.views.generic import UpdateView

class EditProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'blog/edit_profile.html'
    form_class = UserChangeForm
    
    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'slug': self.request.user.username})

app_name = 'blog'

urlpatterns = [
    path('', 
        views.index, 
        name='index'),
    path('posts/<int:pk>/', 
        views.post_detail, 
        name='post_detail'),
    path(
        'category/<slug:category_slug>/',
        views.category_posts,
        name='category_posts'
    ),
    path(
        'profile/<slug:slug>/',
        views.profile,
        name='profile'),
    path(
        'posts/create/',
        views.create_post,
        name='create_post'),
    path(
        'posts/<int:pk>/edit/',
        views.edit_post,
        name='edit_post'),
    path(
        'posts/<int:pk>/delete/',
        views.delete_post,
        name='delete_post'),
    path(
        'posts/<int:pk>/comment/',
        views.add_comment,
        name='add_comment'),
    path(
        'posts/<int:pk>/edit_comment/<int:id>',
        views.edit_comment,
        name='edit_comment'),
    path(
        'posts/<int:pk>/delete_comment/<int:id>',
        views.delete_comment,
        name='delete_comment'),
    path(
    'blog/edit_profile/',
    EditProfileView.as_view(),
    name='edit_profile',
    )   
]
