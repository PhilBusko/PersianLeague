"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
MEMBERS/FORMS.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from django import forms
import django.contrib.auth.models as DM

import allauth.account.models as AM
import allauth.account.forms as AF

import logging
prog_lg = logging.getLogger('progress')
excp_lg = logging.getLogger('exception')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
CUSTOM MEMBER FORMS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class MemberChangeNameForm(AF.UserForm): 
    username = forms.CharField(label='New Name:', max_length=30)
    
    def __init__(self, *args, **kwargs):
        super(MemberChangeNameForm, self).__init__(*args, **kwargs)
    
    def clean_username(self):
        userN = self.cleaned_data['username']
        if DM.User.objects.filter(username=userN).exists():
             self.add_error('username', "Name already exists.")
        return userN



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
ALLAUTH FORM OVERRIDES
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from django.utils.translation import ugettext_lazy as _


class MemberLoginForm(AF.LoginForm):
    def __init__(self, *args, **kwargs):
        super(MemberLoginForm, self).__init__(*args, **kwargs)
        self.fields['login'].label = "Login"


class MemberPasswordForm(AF.ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super(MemberPasswordForm, self).__init__(*args, **kwargs)
    
    
class MemberResetPasswordKeyForm(AF.ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        self.uidb = "zz"
        super(MemberResetPasswordKeyForm, self).__init__(*args, **kwargs)
        
        if self.user:
            from allauth.account.utils import user_pk_to_url_str
            self.uidb = user_pk_to_url_str(self.user)


class MemberAddEmailForm(AF.AddEmailForm):
    def __init__(self, *args, **kwargs):
        #prog_lg.info("MemberAddEmailForm.init")
        super(MemberAddEmailForm, self).__init__(*args, **kwargs)
    
    def clean_email(self):
        value = self.cleaned_data["email"]
        
        errors = {
            "this_account": "This e-mail address is already associated"
                            " with this account.",
            "different_account": "This e-mail address is already associated"
                                 " with another account.",
        }
        
        from allauth.account.utils import filter_users_by_email
        users = filter_users_by_email(value)
        on_this_account = [u for u in users if u.pk == self.user.pk]
        on_diff_account = [u for u in users if u.pk != self.user.pk]
        
        if on_this_account:
            
            # delete from account_emailconfirmation
            AM.EmailConfirmation.objects.get(email_address__email = value).delete()
            
            # delete from account_emailaddress
            AM.EmailAddress.objects.get(email = value).delete()
            
            # let rest of code re-add email and send confirmation
            #raise forms.ValidationError(errors["this_account"])
        
        if on_diff_account: #and app_settings.UNIQUE_EMAIL:
            raise forms.ValidationError(errors["different_account"])
        
        return value



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""