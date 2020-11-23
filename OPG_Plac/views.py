from django.shortcuts import render
from django.shortcuts import HttpResponse, render

# Create your views here.


def index(request):
    return render(request, "index.html", {})


def render_about(request):
    return render(request, "components/about/about.html", {})


def render_blog(request):
    return render(request, "components/blog/blog.html", {})


def view_blog_item(request):
    print(request.GET)

    return render(request, 'components/blog/view_article/view_article.html', {})
