from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import OTP
from .forms import EmailForm, OTPForm, PasswordForm
import random
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

def register_view(request):
    context = {}

    if 'step' not in request.session:
        request.session['step'] = 1

    if request.method == 'POST':
        step = request.session['step']

        if step == 1:
            form = EmailForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']

        # 🔐 Check if email is already registered
                if User.objects.filter(email=email).exists():
                    context['form'] = EmailForm()
                    context['step'] = 1
                    context['error'] = "Email already registered — try logging in."
                    return render(request, 'authapp/register.html', context)

                otp_code = str(random.randint(100000, 999999))

                OTP.objects.create(email=email, otp_code=otp_code)

                send_mail(
                    subject="Your OTP Code",
                    message=f"Your OTP is {otp_code}",
                    from_email=None,
                    recipient_list=[email],
                    fail_silently=False
                )

                request.session['email'] = email
                request.session['step'] = 2
                return redirect('register')


        elif step == 2:
            form = OTPForm(request.POST)
            if form.is_valid():
                email = request.session.get('email')
                entered_otp = form.cleaned_data['otp']
                try:
                    otp_obj = OTP.objects.filter(email=email).latest('created_at')
                    if otp_obj.otp_code == entered_otp and otp_obj.is_valid():
                        request.session['step'] = 3
                        return redirect('register')
                    else:
                        # 🛑 Invalid OTP: Reset flow
                        request.session.flush()
                        request.session['step'] = 1
                        context['form'] = EmailForm()
                        context['step'] = 1
                        context['error'] = "OTP was invalid or expired — start again"
                        return render(request, 'authapp/register.html', context)
                except OTP.DoesNotExist:
                    # 🛑 No OTP found: Reset flow
                    request.session.flush()
                    request.session['step'] = 1
                    context['form'] = EmailForm()
                    context['step'] = 1
                    context['error'] = "OTP not found — start again"
                    return render(request, 'authapp/register.html', context)

        elif step == 3:
            form = PasswordForm(request.POST)
            if form.is_valid():
                email = request.session.get('email')
                password = form.cleaned_data['password']
                User.objects.create_user(username=email, email=email, password=password)
                request.session.flush()
                return redirect('/')

    else:
        # GET request
        step = request.session.get('step', 1)
        form = EmailForm() if step == 1 else OTPForm() if step == 2 else PasswordForm()

    context['form'] = form
    context['step'] = request.session['step']
    return render(request, 'authapp/register.html', context)


def login_view(request):
    from .forms import LoginForm
    context = {}

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Check if user exists with given email
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)

                if user is not None:
                    login(request, user)
                    return redirect('/dashboard/')
                else:
                    context['error'] = "Invalid email or password"
            except User.DoesNotExist:
                context['error'] = "Invalid email or password"
    else:
        form = LoginForm()

    context['form'] = form
    return render(request, 'authapp/login.html', context)



@login_required
def dashboard_view(request):
    return HttpResponse(f"Welcome, {request.user.username}! This is your dashboard.")
