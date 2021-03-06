from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.urls import reverse

from .forms import LoginForm, UserRegistrationForm, UserEditForm, \
    ProfileEditForm, EmailPostForm, NewsForm, ConferenceForm, AdsForm, SubscribeForm, EmailMasForm, ImagesForm
from django.contrib.auth.decorators import login_required, permission_required
from .models import Profile, News, Conference, Ads, Polls, Polls_comment, Polls_questions, Polls_secret, User_mas, Images
from django.contrib import messages
from django.core.mail import EmailMessage
from .forms import CreatePollsForm
from .forms import CreatePollsComment
from .forms import CreatePollsQuest
from .forms import CreatePollsSecret
from django.shortcuts import redirect
from django.conf import settings
from django.core.mail import send_mail

def add_question(request):
    Polls.objects.all().order_by("-id")
    p = Polls.objects.latest('id').id
    poll = CreatePollsForm(request.POST)
    if request.method == 'POST':
        question = CreatePollsQuest(request.POST)
        if question.is_valid():
            q = question.save()
            q.polls_id = p + 1
            q.save()
            return render(request, 'poll/create.html', {'poll': poll})
    question = CreatePollsQuest()
    return render(request, 'poll/add_q.html', {'question': question, 'poll': poll})


############################ рассылка ###########################

def comment(request, poll_id):
    user = request.user.profile
    if request.method == 'POST':
        comments = CreatePollsComment(request.POST)
        if comments.is_valid():
            c = comments.save()
            c.polls_id = poll_id
            c.user_id = user.id
            c.save()
        return render(request, 'poll/comment.html')
    form = CreatePollsComment()
    return render(request, 'poll/comment.html', {'form': form})



############################ рассылка ###########################
def post_email_mas(request):
    if request.method == 'POST':
        form = EmailMasForm(request.POST, request.FILES)
        if form.is_valid():
            subject = form.cleaned_data['title']
            sender = settings.EMAIL_HOST_USER
            message = form.cleaned_data['text']
            if request.FILES:
                uploaded_file = request.FILES['file']
            for User in User_mas.objects.all():
                recipients = [User.email]
                try:
                    email = EmailMessage(subject, message, sender, recipients)
                    email.attach(uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)
                    email.send()
                except:
                    return "Ошибка"
            messages.success(request, 'Письмо успешно отправлено')
            return render(request, 'account/dashboard.html')
    else:
        form = EmailMasForm()
    return render(request, 'email/email_mas.html', {'form': form})


def subscribe(request):
    if request.method == 'POST':
        form = SubscribeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Вы подписались на рассылку')
            return HttpResponseRedirect('/account')
    else:
        form = SubscribeForm()
    return render(request, 'account/subscribe.html', {'form': form})


############################ отправка письма одному человеку ###########################
@permission_required('account.can_edit')
def post_email(request):
    if request.method == 'POST':
        form = EmailPostForm(request.POST, request.FILES)
        if form.is_valid():
            subject = form.cleaned_data['title']
            recipients = form.cleaned_data['to']
            message = form.cleaned_data['text']
            if request.FILES:
                uploaded_file = request.FILES['file']
            try:
                theme = subject

                email = EmailMessage(theme, message, settings.EMAIL_HOST_USER, [recipients])

                email.attach(uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)
                email.send()
                messages.success(request, 'Письма успешно отправлены')
                return render(request, 'account/dashboard.html')
            except:
                return "Ошибка"
    else:
        form = EmailPostForm()
    return render(request, 'email/email.html', {'form': form})


############################ Голосование ###########################




def delete(request, poll_id):
    try:
        poll = Polls.objects.get(id=poll_id)
        poll.delete()
        return home(request)
    except Polls.DoesNotExist:
        return home(request)


def home(request):
    polls = Polls.objects.all()

    context = {
        'polls': polls
    }
    return render(request, 'poll/home.html', context)


def create(request):
    if request.method == 'POST':
        form = CreatePollsForm(request.POST)
        if form.is_valid():
            form.save()

            return redirect('home')
    else:
        form = CreatePollsForm()

    context = {'form': form}
    return render(request, 'poll/create.html', context)


def results(request, poll_id):
    poll = Polls.objects.get(pk=poll_id)
    question = Polls_questions.objects.all()
    context = {
        'poll': poll,
        'questions': question
    }
    return render(request, 'poll/results.html', context)


def vote(request, poll_id):
    poll = Polls.objects.get(pk=poll_id)
    q = Polls_questions.objects.get(polls_id=poll_id)
    if request.method == 'POST':

        selected_option = request.POST['poll']
        if selected_option == 'option1':
            poll.option_one_count += 1
        elif selected_option == 'option2':
            poll.option_two_count += 1
        elif selected_option == 'option3':
            poll.option_three_count += 1
        else:
            return HttpResponse(400, 'Invalid form option')

        poll.save()

        return redirect('results', poll.id)

    context = {
        'poll': poll
    }
    return render(request, 'poll/vote.html', context)


############################## Аккаунт ##############################
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request,
                                username=cd['username'],
                                password=cd['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponse('Аутентификация прошла успешно')
            else:
                return HttpResponse('Неверный аккаунт')
        else:
            return HttpResponse('Неверный логин')
    else:
        form = LoginForm()
    return render(request, 'account/login.html', {'form': form})


@login_required
def dashboard(request):
    return render(request, 'account/dashboard.html', {'section': 'dashboard'})


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(
                user_form.cleaned_data['password'])
            new_user.save()
            Profile.objects.create(user=new_user)
            return render(request,
                          'account/register_done.html',
                          {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request,
                  'account/register.html',
                  {'user_form': user_form})


def submit_an_application(request):
    user = request.user.profile
    profile_form = ProfileEditForm(instance=request.user.profile, data=request.POST, files=request.FILES)
    # user = Profile.objects.get(id=id)
    if not user.user_submit:
        user.user_submit = True
    user.save()
    messages.success(request, 'заявка успешно отправлена')
    return HttpResponseRedirect("/account")


@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=request.user.profile, data=request.POST, files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль успешно отредактирован')
        else:
            messages.error(request, 'Ошибка при редактировании профиля')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    return render(request,
                  'account/edit.html',
                  {'user_form': user_form,
                   'profile_form': profile_form})


############################## Новости ##############################
@permission_required('account.can_add')
def create_news(request):
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/account')
    else:
        form = NewsForm()
    return render(request, 'news/create_news.html', {'form': form})


@permission_required('account.can_edit')
def detail_news(request, news_id):
    try:
        news = News.objects.get(id=news_id)
    except:
        raise Http404("Новость не найдена")

    if request.method == "POST":
        form = NewsForm(data=request.POST, instance=news)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/account/list_of_news")
    else:
        form = NewsForm(instance=news)

    img_list=news.images_set.all()
    return render(request, "news/detail_news.html", {"news": news, "form": form, "img_list": img_list})


@permission_required('account.can_delete')
def delete_news(request, id):
    new = News.objects.get(id=id)
    new.delete()
    return HttpResponseRedirect("/account")


def list_of_news(request):
    news = News.objects.all()
    return render(request, "news/list_of_news.html", {"news": news})

@permission_required('account.can_edit')
def detail_carusel(request, news_id):
    try:
        news = News.objects.get(id=news_id)
    except:
        raise Http404("Новость не найдена")

    if request.method == "POST":
        form = NewsForm(data=request.POST, instance=news)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/account/list")
    else:
        form = NewsForm(instance=news)

    img_list = news.images_set.all()
    return render(request, "news/detail_carusel.html", {"news": news, "img_list": img_list})

@permission_required('account.can_edit')
def leave_img(request, news_id):
    try:
        news = News.objects.get(id=news_id)
    except:
        raise Http404("Новость не найдена")
    if request.method == 'POST':
        form = ImagesForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            photo = Images(news=news, image=image)
            photo.save()
            img_list=news.images_set.all()
            return render(request, "news/detail_carusel.html", {"news": news, "form": form, "img_list": img_list})
    else:
        form = ImagesForm()
    return render(request, 'news/leave_img.html', {'form': form})

@permission_required('account.can_delete')
def delete_img(request, news_id, id):
    img = Images.objects.get(id=id)
    news=News.objects.get(id=news_id)
    img.delete()
    return HttpResponseRedirect(reverse('detail_carusel', args=(news.id,)))



@permission_required('account.can_delete')
def delete_news(request, id):
    new = News.objects.get(id=id)
    new.delete()
    return HttpResponseRedirect("/account")


def list_of_news(request):
    news = News.objects.all()
    return render(request, "news/list_of_news.html", {"news": news})


############################## Объявления ##############################
@permission_required('account.can_add')
def create_ads(request):
    if request.method == 'POST':
        form = AdsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/account')
    else:
        form = NewsForm()
    return render(request, 'ads/create_ads.html', {'form': form})


@permission_required('account.can_edit')
def edit_ads(request, id):
    n = Ads.objects.get(id=id)
    if request.method == "POST":
        form = AdsForm(data=request.POST, files=request.FILES, instance=n)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/account")
    else:
        form = AdsForm(instance=n)
    return render(request, "ads/edit_ads.html", {"form": form})


@permission_required('account.can_delete')
def delete_ads(request, id):
    new = Ads.objects.get(id=id)
    new.delete()
    return HttpResponseRedirect("/account")


def list_of_ads(request):
    ads = Ads.objects.all()
    return render(request, "ads/list_of_ads.html", {"ads": ads})


############################## Конференции ##############################
@permission_required('account.can_add')
def create_conference(request):
    if request.method == 'POST':
        form = ConferenceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/account')
    else:
        form = ConferenceForm()
    return render(request, "conference/create_conference.html", {'form': form})


@permission_required('account.can_edit')
def edit_conference(request, id):
    conference = Conference.objects.get(id=id)
    if request.method == "POST":
        form = ConferenceForm(data=request.POST, files=request.FILES, instance=conference)
        if form.is_valid():
            form.save()
        return HttpResponseRedirect("/account")
    else:
        form = ConferenceForm(instance=conference)
        return render(request, "conference/edit_conference.html", {"form": form})


@permission_required('account.can_delete')
def delete_conference(request, id):
    conference = Conference.objects.get(id=id)
    conference.delete()
    return HttpResponseRedirect("/account")


def list_of_conference(request):
    conference = Conference.objects.all()
    return render(request, "conference/list_of_conference.html", {"conference": conference})


############################## Список пользователей ##############################
@permission_required('account.can_view')
def list_of_scientists(request):
    users = Profile.objects.all()
    return render(request, "scientists/list_of_scientists.html", {"users": users})


@permission_required('account.can_delete')
def delete_user(request, id):
    user = Profile.objects.get(id=id)
    user.user.delete()
    return HttpResponseRedirect("/account")


############################## Список ученых ##############################
@permission_required('account.can_edit')
def add_to_scientists(request, id):  ##добавление в совет
    user = Profile.objects.get(id=id)
    user.scientist = True
    # user.user_is_reject = False
    user.save()
    messages.success(request, 'заявка успешно отправлена')
    return HttpResponseRedirect("/account")


@permission_required('account.can_edit')
def delete_from_scientists(request, id):  ##удаление из совета
    user = Profile.objects.get(id=id)
    if not user.user_is_reject and user.scientist:
        user.scientist = False
        user.user_is_reject = False
    elif not user.user_is_reject:
        user.user_is_reject = True
        user.user_submit = False
    user.save()
    return HttpResponseRedirect("/account")