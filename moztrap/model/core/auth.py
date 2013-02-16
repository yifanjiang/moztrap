"""
Proxy User and Role models.

"""
import base64
import hashlib

from django.conf import settings
from django.db.models import Q

from django.contrib.auth.backends import ModelBackend as DjangoModelBackend
# Permission is imported solely so other places can import it from here
from django.contrib.auth.models import User as BaseUser, Group, Permission

from django_browserid.auth import BrowserIDBackend as BaseBrowserIDBackend
from preferences import preferences
from registration.models import RegistrationProfile
from registration.signals import user_registered

from django_openid_auth.auth import OpenIDBackend as BaseOpenIDBackend

# monkeypatch the User model to ensure unique email addresses
BaseUser._meta.get_field("email")._unique = True

class OpenIDBackend(BaseOpenIDBackend):

    # Use moztrap.model.core.auth.User instead of django.contrib.auth.models.User
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


    def filter_users_by_email(self, email):
        """Return all users matching the specified email."""
        return User.objects.filter(email=email)


    def create_user_from_openid(self, openid_response):
        details = self._extract_user_details(openid_response)
        required_attrs = getattr(settings, 'OPENID_SREG_REQUIRED_FIELDS', [])
        if getattr(settings, 'OPENID_STRICT_USERNAMES', False):
            required_attrs.append('nickname')

        for required_attr in required_attrs:
            if required_attr not in details or not details[required_attr]:
                raise RequiredAttributeNotReturned(
                    "An attribute required for logging in was not "
                    "returned ({0}).".format(required_attr))

        email = details['email'] or ''

        nickname = details['nickname'] or 'openiduser'
        username = self._get_available_username(details['nickname'], openid_response.identity_url)
        user = User.objects.create_user(username, email, password=None)

        add_new_user_role(user)

        self.associate_openid(user, openid_response)
        self.update_user_details(user, details, openid_response)

        return user


class User(BaseUser):
    """Proxy for contrib.auth User that adds action methods and roles alias."""
    class Meta:
        proxy = True


    def delete(self, user=None):
        """
        Delete this user.

        We ignore the passed-in user since User is not a MTModel and doesn't
        track created_by / modified_by.

        We have to delete registration profiles manually, to avoid
        https://code.djangoproject.com/ticket/16128.

        """
        # @@@ Django ticket 16128, hopefully fixed in 1.4?
        # RegistrationProfile's FK is to Django's user model, not ours
        RegistrationProfile.objects.filter(user=self).delete()
        super(User, self).delete()


    def activate(self, user=None):
        """Activate this user."""
        self.is_active = True
        self.save(force_update=True)


    def deactivate(self, user=None):
        """Deactivate this user."""
        self.is_active = False
        self.save(force_update=True)


    @property
    def roles(self):
        """Maps our name (roles) to Django name (groups)."""
        return self.groups



Role = Group



class ModelBackend(DjangoModelBackend):
    """Accepts username or email and returns our proxy User model."""
    def authenticate(self, username=None, password=None):
        """Return User for given credentials, or None."""
        candidates = User.objects.filter(Q(username=username) | Q(email=username))
        for user in candidates:
            if user.check_password(password):
                return user
        return None


    def get_user(self, user_id):
        """Return User for given ID, or None."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class BrowserIDBackend(BaseBrowserIDBackend):
    """BrowserID backend that returns our proxy user."""
    def filter_users_by_email(self, email):
        """Return all users matching the specified email."""
        return User.objects.filter(email=email)

    def get_user(self, user_id):
        """Return User for given ID, or None."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None



AUTO_USERNAME_PREFIX = ":auto:"
USERNAME_MAX_LENGTH = User._meta.get_field("username").max_length
DIGEST_LENGTH = USERNAME_MAX_LENGTH - len(AUTO_USERNAME_PREFIX)



def browserid_create_user(email):
    """Create and return a new User for a new BrowserID login."""
    digest = base64.urlsafe_b64encode(hashlib.sha1(email).digest())
    username = AUTO_USERNAME_PREFIX + digest[:DIGEST_LENGTH]

    user = User.objects.create_user(username=username, email=email)
    add_new_user_role(user)

    return user



def add_new_user_role(user, **kwargs):
    role = preferences.CorePreferences.default_new_user_role
    if role is not None:
        # Have to use groups, not roles, because registration doesn't send our
        # proxy User with its signal.
        user.groups.add(role)



user_registered.connect(add_new_user_role)
