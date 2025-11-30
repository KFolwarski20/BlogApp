from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.views.generic import ListView
from .models import Post
from taggit.models import Tag
from .forms import EmailPostForm, CommentForm


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])
    paginator = Paginator(object_list, 3)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # Jeżeli zmienna page nie jest liczbą całkowitą
        # wówczas pobierana jest pierwsza strona wyników.
        posts = paginator.page(1)
    except EmptyPage:
        # Jeżeli zmienna page ma wartość większą niż numer ostatniej strony
        # wyników, wtedy pobierana jest ostatnia strona wyników.
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html', {'posts': posts, 'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post,
                                   status='published',
                                   publish__year=year,
                                   publish__month=month,
                                   publish__day=day)

    # Lista aktywnych komentarzy dla danego posta.
    comments = post.comments.filter(active=True)

    new_comment = None

    if request.method == 'POST':
        # Komentarz został opublikowany.
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Utworzenie obiektu Comment; jeszcze jednak nie zapisujemy go w bazie danych.
            new_comment = comment_form.save(commit=False)
            # Przypisanie komentarza do bieżącego posta.
            new_comment.post = post
            # Zapisanie komentarza w bazie danych.
            new_comment.save()

            # Przekierowanie, aby formularz się wyczyścił
            return redirect('blog:post_detail',
                            year=post.publish.year,
                            month=post.publish.month,
                            day=post.publish.day,
                            post=post.slug)
    else:
        comment_form = CommentForm()
    return render(request,
                  'blog/post/detail.html',
                  {'post': post, 'comments': comments, 'comment_form': comment_form})


def post_share(request, post_id):
    # Pobieranie posta na podstawie jego identyfikatora
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False

    if request.method == 'POST':
        # Formularz został wysłany
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Weryfikacja formularza zakończyła się powodzeniem...
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} zachęca {cd['email']} do przeczytania \"{post.title}\"."
            message = (f"Przeczytaj post \"{post.title}\" na stronie {post_url}\n\n Komentarz dodany przez:"
                       f"{cd['name']}: {cd['comments']}")
            send_mail(subject, message, 'test@dev.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})
