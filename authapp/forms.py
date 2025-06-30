from django import forms

class EmailForm(forms.Form):
    email = forms.EmailField(label="Enter your email")

class OTPForm(forms.Form):
    otp = forms.CharField(label="Enter OTP", max_length=6)

class PasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)