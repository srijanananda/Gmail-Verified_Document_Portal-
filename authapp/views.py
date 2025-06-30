from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import OTP
from .forms import EmailForm, OTPForm, PasswordForm
import random
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


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

from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse

def login_view(request):
    from .forms import LoginForm
    context = {}

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)

                if user:
                    login(request, user)

                    # Generate JWT tokens
                    refresh = RefreshToken.for_user(user)
                    return JsonResponse({
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                        'message': "Login successful",
                    })
                else:
                    context['error'] = "Invalid credentials"
            except User.DoesNotExist:
                context['error'] = "Invalid credentials"
    else:
        form = LoginForm()

    context['form'] = form
    return render(request, 'authapp/login.html', context)



@login_required
def dashboard_view(request):
    return redirect('dashboard_home')


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_api_view(request):
    return Response({"message": f"Hello {request.user.username}, you're authorized!"})
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.core.mail import send_mail
import random
from django.contrib import messages

# Store OTPs temporarily (you can use DB or cache later)
RESET_OTP_STORE = {}

def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            otp = random.randint(100000, 999999)
            RESET_OTP_STORE[email] = otp
            send_mail(
                "Password Reset OTP",
                f"Your OTP is: {otp}",
                "noreply@example.com",
                [email],
                fail_silently=False,
            )
            request.session['reset_email'] = email
            messages.success(request, "OTP sent to your email")
            return redirect('verify_reset_otp')
        except User.DoesNotExist:
            messages.error(request, "Email not found")

    return render(request, 'authapp/forgot_password.html')


def verify_reset_otp_view(request):
    if request.method == "POST":
        email = request.session.get("reset_email")
        entered_otp = request.POST.get("otp")
        if email in RESET_OTP_STORE and str(RESET_OTP_STORE[email]) == entered_otp:
            return redirect('reset_password')
        else:
            messages.error(request, "Invalid OTP")
            return redirect('forgot_password')
    return render(request, "authapp/verify_reset_otp.html")


def reset_password_view(request):
    email = request.session.get("reset_email")

    if not email:
        messages.error(request, "Session expired. Start again.")
        return redirect('forgot_password')

    if request.method == "POST":
        password = request.POST.get("password")

        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            messages.success(request, "Password reset successful. You can now log in.")
            request.session.flush()  # clear session after successful reset
            return redirect('login')

        except User.DoesNotExist:
            messages.error(request, "User not found. Try again.")
            return redirect('forgot_password')

    context = {"email": email}
    return render(request, 'authapp/reset_password.html', context)
from django.shortcuts import render

def home_view(request):
    return render(request, 'authapp/home.html')
