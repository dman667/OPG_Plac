from django.shortcuts import HttpResponse, render, redirect
from django.contrib.auth import logout
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
import math

from OPG_Plac import models
from OPG_Plac import serializers

# views


def index(request):

    categories_qset = models.ProductCategory.objects.filter(on_homepage=True).order_by("position_index")

    # Get homepage_square categories
    categories_list = []
    for category in categories_qset:
        categories_list.append({
            "name": category.category,
            "image": category.category_img
        })

    # Get most frequently ordered items
    top_picks_qset = models.OrderItem.objects \
        .annotate(count=Count('product')).order_by('-count')

    # Extract five top Product objs
    top_picks = []
    i = 0
    while len(top_picks) < 5 and i < len(top_picks_qset):  # Stop at 5, ensure no overrun
        already_exists = False
        for product in top_picks:  # Get only unique products
            if product == top_picks_qset[i].product:
                already_exists = True
        if not already_exists:
            top_picks.append(top_picks_qset[i].product)
        i = i + 1

    # Serialize top_picks for view
    top_picks = serializers.serialize_products(top_picks)

    for serialized_product in top_picks:  # Shorten name and description if required
        if len(serialized_product["short_desc"]) > 35:
            serialized_product["short_desc"] = serialized_product["short_desc"][:35] + "..."
        if len(serialized_product["name"]) > 35:
            serialized_product["name"] = serialized_product["name"][:35] + "..."

    return render(request, "index.html", {
        "categories": categories_list,
        "top_picks": top_picks
    })


def view_about(request):
    return render(request, "components/about/about.html", {})


# render blog overview page -- returns blog categories from db and sends them as a list to template
def view_blog_previews(request):

    category_filter = request.GET.get("category", "all")
    page_num = int(request.GET.get("page", 1))

    blog_categories = models.BlogCategory.objects.all().order_by('position_index')

    categories = []  # Sort categories and pack in list
    for category in blog_categories:
        categories.append(category.category)

    if category_filter == "all":   # Filter articles by category
        qset = models.BlogArticle.objects.all()

    else:
        category_obj = models.BlogCategory.objects.get(category=category_filter)
        qset = models.BlogArticle.objects.filter(category=category_obj)

    total_pages = math.ceil(len(qset) / 8)

    try:
        p = Paginator(qset, 8,)
        articles = p.page(page_num)
    except EmptyPage:
        articles = []

    previews = serializers.serialize_previews(articles)

    return render(request, "components/blog/blog.html", {
        "categories": categories,
        "category_filter": category_filter,
        "article_previews": previews,
        "total_pages": total_pages,
        "current_page": page_num
    })


def view_blog_article(request):

    seo_url = request.GET["article"]

    try:
        article = models.BlogArticle.objects.get(seo_url=seo_url)
    except ObjectDoesNotExist:
        return render(request, "components/utility/error.html", {
            "error": "Not Found",
            "status": 404,
            "message": "Maybe try again or check spelling ?"
        })

    author = article.author.email
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


def view_proizvodi(request):
    results_per_page = 12  # Controls the number of products per pagination page

    category_filter = request.GET.get("category", None)
    subcategory_filter = request.GET.get("subcategory", None)
    search_query = request.GET.get("searchq", "%None%")
    sort_filter = request.GET.get("sort", None)

    # Map sort filters
    if sort_filter == "name_asc":
        sort_filter = "name"
    elif sort_filter == "name_desc":
        sort_filter = "-name"
    elif sort_filter == "price_asc":
        sort_filter = "price"
    elif sort_filter == "price_desc":
        sort_filter = "-price"
    else:
        sort_filter = "name"

    page_num = request.GET.get("page", 1)

    category_qset = models.ProductCategory.objects.all().order_by("position_index")  # Fetch category and subcategory qsets
    subcategory_qset = models.ProductSubCategory.objects.all().order_by("position_index")

    categories_dict = {}  # Build a dict with categories and their subcategories
    for category in category_qset:  # Pass to view for categories_menu construction
        subcategories = []

        for subcategory in subcategory_qset:
            if subcategory.parent_category == category:
                subcategories.append(subcategory.subcategory)
        categories_dict[category.category] = subcategories

    # Get products_qset
    if search_query == "%None%":
        if category_filter is None:
            products = models.Product.objects.all()
            subcategory_filter = None  # ensure no active subfilter if main_category filter is None

        else:
            category_obj = models.ProductCategory.objects.get(category=category_filter)

            if subcategory_filter is not None:
                subcategory_obj = models.ProductSubCategory.objects.get(subcategory=subcategory_filter)

                products = models.Product.objects.filter(category=category_obj, subcategory=subcategory_obj)

            else:
                products = models.Product.objects.filter(category=category_obj)
    else:  # Handle search
        products = models.Product.objects.filter(
            Q(name__icontains=search_query) | Q(item_id__iexact=search_query) |
            Q(brand__name__icontains=search_query) | Q(category__category__icontains=search_query) |
            Q(subcategory__subcategory__icontains=search_query)
        )

    products = products.order_by(sort_filter)  # apply sort_filter

    # Calculate total pages
    product_count = products.count()
    total_pages = math.ceil(product_count / results_per_page)

    # Paginate
    try:
        p = Paginator(products, results_per_page)
        products_page = p.page(page_num)
    except EmptyPage:
        products_page = []

    # Serialize
    products_page = serializers.serialize_products(products_page)

    return render(request, "components/products/products.html", {
        "categories": categories_dict,
        "products": products_page,
        "active_category": category_filter,
        "active_subcategory": subcategory_filter,
        "total_pages": total_pages,
        "total_results": product_count,
        "current_page": page_num,
        "search_query": search_query
    })


def view_proizvod_artikl(request, product_url):

    try:
        product_obj = models.Product.objects.get(seo_url=product_url)
    except ObjectDoesNotExist:
        return render(request, "components/utility/error.html", {
            "error": "Not Found",
            "status": 404,
            "message": "Maybe try again or check spelling ?"
        })

    try:
        product_img = product_obj.product_image.url
    except ValueError:
        product_img = None

    product = {
        "product_name": product_obj.name,
        "item_id": product_obj.item_id,
        "product_img": product_img,
        "alt_img1": product_obj.second_image,
        "alt_img2": product_obj.third_image,
        "price": product_obj.price,
        "short_description": product_obj.short_description,
        "brand": product_obj.brand.name,
        "banner_img": product_obj.brand.img,
        "availability": product_obj.availability.status_name,
        "category": product_obj.category,
        "subcategory": product_obj.subcategory.subcategory,
        "description": product_obj.description
    }

    return render(request, "components/products/product_view/view_artikl.html", product)


def view_signin(request):
    if request.user.is_authenticated:
        return redirect("/")
    else:
        return render(request, "components/signin/signin.html", {})


# Logout path
def view_logout(request):
    logout(request)
    return redirect("/")


@login_required(login_url="/prijava")
def view_cart(request):

    user = models.User.objects.get(email=request.user)
    cart = user.cart.all()

    cart_count = sum([item.quantity for item in cart])

    cart = serializers.serialize_cart(cart)

    total = round(float(sum([item["sum"] for item in cart])), 2)
    base_sum = round(total/1.25, 2)
    vat = round(total - base_sum)
    shipping_cost = 20
    total_sum = round(total + shipping_cost, 2)

    return render(request, "components/cart/cart.html", {
        "cart": cart,
        "total": total_sum,
        "base_sum": base_sum,
        "vat": vat,
        "shipping_cost": shipping_cost,
        "cart_count": cart_count
    })


@login_required(login_url="/prijava")
def view_delivery(request):
    user = models.User.objects.get(email=request.user)

    # If cart is empty -- redirect to cart view ( Features empty cart notification )
    if len(user.cart.all()) == 0:
        return redirect("/košarica")

    try:
        user_info = serializers.serialize_user_info(user.extendeduser)
    except ObjectDoesNotExist:
        user_info = {
            "first_name": user.first_name,
            "last_name": user.last_name
        }

    return render(request, "components/cart/delivery.html", user_info)


@login_required(login_url="/prijava")
def view_checkout(request):

    user = models.User.objects.get(email=request.user)
    cart = user.cart.all()

    if len(cart) == 0:
        return redirect("/košarica")

    cart = serializers.serialize_cart(user.cart.all())

    try:
        order = user.orders.get(status=None)
    except ObjectDoesNotExist:
        return redirect("/košarica")

    total = float(sum([item["sum"] for item in cart]))
    base_sum = round(total/1.25, 2)
    vat = round(total - base_sum)
    shipping_cost = 20
    total_sum = total + shipping_cost

    payopts_qset = models.PaymentOption.objects.all()
    payment_options = []
    for option in payopts_qset:
        payment_options.append({
            "descriptive_name": option.descriptive_name,
            "reference": option.reference,
            "tooltip": option.tooltip
        })

    context = {
        "cart": cart,
        "total": "{:.2f}".format(total_sum),
        "base_sum": base_sum,
        "vat": vat,
        "shipping_cost": shipping_cost,
        "payment_options": payment_options
    }

    # provide order_information to context
    context.update(serializers.serialize_order_info(order))

    return render(request, "components/cart/checkout.html", context)


@login_required(login_url="/prijava")
def view_order_confirmation(request):
    return render(request, "components/cart/order_confirmation.html")


@login_required(login_url="/prijava")
def view_order_history(request):

    user = models.User.objects.get(email=request.user)

    orders_qset = user.orders.all().exclude(status=None).order_by('-id')

    orders = []
    for order in orders_qset:
        orders.append({
            "id": "{} / {}".format(order.id, order.history.all()[0].timestamp.strftime("%Y")),
            "created_on": order.history.all()[0].timestamp.strftime('%d.%m.%Y %H:%M'),
            "items_count": sum([item.quantity for item in order.items.all()]),
            "total": round(sum([item.item_price * item.quantity for item in order.items.all()]), 2) + 20,
            "status": order.status,
            "plain_id": order.id
        })

    return render(request, "components/order_history/order_history.html", {
        "orders": orders
    })


@login_required(login_url="/prijava")
def view_order_info(request):

    user = models.User.objects.get(email=request.user)

    try:
        order_id = request.GET["id"]
    except KeyError:
        return render(request, "components/utility/error.html", {
            "error": "Nije pronađeno",
            "status": 404,
            "message": "Jeste li ispravno upisali link?"
        })

    try:  # Get order obj, ensure id is valid, is applicable to current user and has no None status
        order = user.orders.get(id=order_id)
    except ObjectDoesNotExist:
        return redirect("/")
    if order.status is None:
        return redirect("/")

    order_info = {
        "header": f"Narudžba br.{order.id}",
        "created_on": order.history.all()[0].timestamp.strftime('%d.%m.%Y.'),
        "payment_type": order.paymentOption.descriptive_name,
        "payment_reference": order.paymentOption.reference
    }

    order_info.update(serializers.serialize_order_info(order))

    items_qset = order.items.all()

    # 20 is shipping price TODO make shipping price a configurable variable
    grand_total = sum([item.item_price * item.quantity for item in items_qset]) + 20
    base_price = float(grand_total) / 1.25
    vat = float(grand_total) - base_price

    price_summary = {
        "base_price": "{:.2f}".format(base_price),
        "vat": "{:.2f}".format(vat),
        "shipping_cost": 20,
        "grand_total": "{:.2f}".format(grand_total)
    }

    order_info.update(price_summary)

    return render(request, "components/order_history/order_info.html", order_info)

