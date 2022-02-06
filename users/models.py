from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator


class CustomAccountManager(BaseUserManager):

    def create_superuser(self, email, password, **other_fields):

        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)

        if other_fields.get('is_staff') is not True:
            raise ValueError(
                'Superuser must be assigned to is_staff=True.')
        if other_fields.get('is_superuser') is not True:
            raise ValueError(
                'Superuser must be assigned to is_superuser=True.')

        return self.create_user(email, password, **other_fields)

    def create_user(self, email, password=None, **other_fields):

        if not email:
            raise ValueError(_('You must provide an email address'))

        email = self.normalize_email(email)
        user = self.model(email=email, **other_fields)
        user.set_password(password)
        user.save()
        return user


class NewUser(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(_('email address'), unique=True)
    # username = None
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    start_date = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = CustomAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

class UserFlightsSearchModel(models.Model):
    originplace = models.CharField(max_length=10)
    destinationplace = models.CharField(max_length=10)
    outbounddate = models.CharField(max_length=100)
    inbounddate = models.CharField(max_length=100, blank=True)
    adults = models.IntegerField(default=0)
    children = models.IntegerField(default=0, blank=True)
    infants = models.IntegerField(default=0, blank=True)
    country = models.CharField(max_length=100, default='IN')
    currency = models.CharField(max_length=100)
    locale = models.CharField(max_length=100)
    user_id = models.ForeignKey(NewUser, related_name="user_id", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

class UserHotelSearchModel(models.Model):
    destination = models.CharField(max_length=10)
    checkInDate = models.CharField(max_length=10,
        validators=[RegexValidator(regex='^.{10}$', message='Length has to be 10')])
    checkOutDate = models.CharField(max_length=10,
        validators=[RegexValidator(regex='^.{10}$', message='Length has to be 10')])
    adults = models.IntegerField(default=0, validators=[MinValueValidator(1)])
    children = models.IntegerField(default=0, blank=True)
    user_id = models.ForeignKey(NewUser, related_name="u_id", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

class FlightsHotelPackageModel(models.Model):
    originplace = models.CharField(max_length=10)
    destinationplace = models.CharField(max_length=10)
    outbounddate = models.CharField(max_length=10,
        validators=[RegexValidator(regex='^.{10}$', message='Length has to be 10')])
    inbounddate = models.CharField(max_length=10, blank=True,
        validators=[RegexValidator(regex='^.{10}$', message='Length has to be 10')])
    adults = models.IntegerField(default=0)
    rooms = models.IntegerField(default=0, validators=[MinValueValidator(1)])
    children = models.IntegerField(default=0, blank=True)
    infants = models.IntegerField(default=0, blank=True)
    country = models.CharField(max_length=10, default='IN')
    currency_format = models.CharField(max_length=10)
    destination_code = models.CharField(max_length=10)
    locale = models.CharField(max_length=10)
    trip_days = models.IntegerField(default=1, blank=True, validators=[MaxValueValidator(30)])
    number_of_extended_months = models.IntegerField(default=0, blank=True, validators=[MaxValueValidator(2)])
    user_id = models.ForeignKey(NewUser, related_name="package_user_id", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
