from django.shortcuts import render
from django.views.generic import TemplateView



class About(TemplateView):
    template_name = 'pages/about.html' 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'О проекте'
        return context

class Rules(TemplateView):
    template_name = 'pages/rules.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Наши правила'
        return context

def page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404) 

def server_error(request):
    return render(request, 'pages/500.html', status=500)

def csrf_failure(request, reason=''):
    return render(request, 'pages/403csrf.html', status=403) 
