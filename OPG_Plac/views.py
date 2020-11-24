from django.shortcuts import HttpResponse, render
from django.core.exceptions import ObjectDoesNotExist

from OPG_Plac import models

# Create your views here.


def index(request):
    return render(request, "index.html", {})


def render_about(request):
    return render(request, "components/about/about.html", {})


# render blog overview page -- returns blog categories from db and sends them as a list to template
def render_blog(request):

    blog_categories = models.BlogCategory.objects.all().order_by('position_index')

    categories = []  # Sort categories and pack in list
    for category in blog_categories:
        categories.append(category.category)

    return render(request, "components/blog/blog.html", {"categories": categories})


def view_blog_item(request):

    seo_url = request.GET["article"]

    try:
        article = models.BlogArticle.objects.get(seo_url=seo_url)
    except ObjectDoesNotExist:
        return render(request, "components/utility/error.html", {
            "error": "Not Found",
            "status": 404,
            "message": "Maybe try again or check spelling ?"
        })

    author = article.author.username
    category = article.category
    title = article.title
    content = article.Article_content
    keywords = article.seo_keywords
    timestamp = article.timestamp
    img = article.title_image
    seo_url = article.seo_url

    return render(request, 'components/blog/view_article/view_article.html', {
        "author": author,
        "category": category,
        "title": title,
        "content": content,
        "keywords": keywords,
        "timestamp": timestamp,
        "img": img,
        "seo_url": seo_url
    })
