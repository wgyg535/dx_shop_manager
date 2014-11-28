# coding=utf-8
'''
Created on 2014年8月8日
user模型
@author: tubin
'''
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, \
    SiteProfileNotAvailable, UserManager
from django.core import validators
import re
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
import warnings
from django.core.exceptions import ImproperlyConfigured
from utils.uuid import uuid
from rest_framework.authtoken.models import Token


class User(AbstractBaseUser, PermissionsMixin):
    '''
    用户模型，暂时测试用
    '''
    id = models.CharField(max_length=32, unique=True, primary_key=True, default=None, editable=False)
    username = models.CharField(_('username'), max_length=30, unique=True,
                                validators=[
                                    validators.RegexValidator(re.compile('^[\w.@+-]+$'), _('Enter a valid username.'),
                                                              'invalid')
                                ])
    email = models.EmailField(_('email address'), blank=True, max_length=30)
    phone = models.CharField(_('phone nums'), blank=True, max_length=11)
    login_num = models.IntegerField(default=0)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now())
    modified_date = models.DateTimeField(blank=True, null=True)
    user_parent_id = models.CharField(max_length=32, blank=True, null=True)
    secure_phone = models.CharField(max_length=11, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    sex = models.SmallIntegerField(blank=True, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    class Meta:
        db_table = 'user'
        swappable = 'AUTH_USER_MODEL'

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def incr_login_num(self, num=1):
        '''增加登录次数'''
        self.login_num += num
        self.save()

    def save(self, *args, **kwargs):
        if self.id is None or self.id == 0:
            self.id = uuid()
        super(User, self).save()

    @classmethod
    def create_user(cls, data=None):
        if not data:
            return None;
        try:
            user = User.objects.create(id=data['id'], username=data['username'])
            if data.get('email', None) is not None:
                user.email = data['email']
            if data.get('phone', None) is not None:
                user.phone = data['phone']
            user.save()
            return user
        except BaseException, e:
            print e
            return None

    def get_profile(self):
        """
        Returns site-specific profile for this user. Raises
        SiteProfileNotAvailable if this site does not allow profiles.
        """
        warnings.warn("The use of AUTH_PROFILE_MODULE to define user profiles has been deprecated.",
                      DeprecationWarning, stacklevel=2)
        if not hasattr(self, '_profile_cache'):
            from django.conf import settings

            if not getattr(settings, 'AUTH_PROFILE_MODULE', False):
                raise SiteProfileNotAvailable(
                    'You need to set AUTH_PROFILE_MODULE in your project '
                    'settings')
            try:
                app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
            except ValueError:
                raise SiteProfileNotAvailable(
                    'app_label and model_name should be separated by a dot in '
                    'the AUTH_PROFILE_MODULE setting')
            try:
                model = models.get_model(app_label, model_name)
                if model is None:
                    raise SiteProfileNotAvailable(
                        'Unable to load the profile model, check '
                        'AUTH_PROFILE_MODULE in your project settings')
                self._profile_cache = model._default_manager.using(
                    self._state.db).get(user__id__exact=self.id)
                self._profile_cache.user = self
            except (ImportError, ImproperlyConfigured):
                raise SiteProfileNotAvailable
        return self._profile_cache


class MToken(Token):
    """
    移动登录token对象，用于标记用户登录相关信息
    """
    terminal = models.SmallIntegerField()
    version = models.DecimalField(max_digits=10, decimal_places=5)

    class Meta:
        db_table = 'auth_token'

    @staticmethod
    def get_or_create(user=None, terminal=None, version=None):
        try:
            token = MToken.objects.get(user_id=user.id)
        except:
            token = MToken.objects.create(user_id=user.id, terminal=terminal, version=version)
        return token
        