from django.db import models
from django.conf import settings
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class ProfileCard(models.Model):
    day_hours = [(x, str(x).zfill(2)+':00') for x in range(25)]
    rate_list = [(x, str(x)) for x in range(10)]
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='user pk')
    gamer_name = models.CharField(verbose_name='게임아이디', max_length=20)
    game_name = models.ForeignKey('CardGameName', on_delete=models.SET_NULL, verbose_name='게임명', null=True)
    card_img = models.ManyToManyField('CardImage', verbose_name='사진')

    community = models.ManyToManyField('CardCommunity', verbose_name="커뮤니티", blank=True)
    streamer = models.ManyToManyField('CardStreamer', verbose_name="스트리머", blank=True)

    liker = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liker', verbose_name="좋아요누른사람", blank=True)
    disliker = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='disliker', verbose_name="싫어요누른사람", blank=True)

    title = models.CharField(verbose_name='제목', max_length=50)
    contents = models.CharField(verbose_name='내용', max_length=2000)
    # 너무 느릴수 있다면 별도의 테이블을 만들어서 보관

    game_day = models.CharField(max_length=14, verbose_name="플레이요일")
    game_hours_s = models.PositiveSmallIntegerField(choices=day_hours, verbose_name='플레이 시작시간')
    game_hours_e = models.PositiveSmallIntegerField(choices=day_hours, verbose_name='플레이 끝난시간')

    is_noob = models.BooleanField(verbose_name='뉴비', default=False)
    play_style = models.PositiveSmallIntegerField(choices=rate_list, verbose_name='플레이 스타일')

    last_update = models.DateTimeField(verbose_name='마지막 업데이트', auto_now=True)
    date_created = models.DateTimeField(verbose_name='생성일', auto_now_add=True)

    class Meta:
        unique_together = ['owner', 'game_name']
        ordering = ('-date_created',)

    def __str__(self):
        return str(self.owner_id) + '-' + str(self.id)


def upload_location(instance, filename, **kwargs):
    path_id = str(instance.owner).split('-')[-1]
    file_path = 'card/{card_id}/{filename}'.format(
        card_id=path_id, filename=filename
    )
    return file_path


class CardImage(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='user pk')
    image = models.ImageField(upload_to=upload_location, null=False, blank=True)
    date_published = models.DateTimeField(auto_now_add=True, verbose_name="업로드일")

    def __str__(self):
        return str(self.id)


class CardGameName(models.Model):
    player_game = models.CharField(verbose_name="게임명", unique=True, max_length=20)

    def __str__(self):
        return self.player_game


class CardCommunity(models.Model):
    player_community = models.CharField(verbose_name="커뮤니티", unique=True, max_length=20)

    def __str__(self):
        return self.player_community


class CardStreamer(models.Model):
    player_streamer = models.CharField(verbose_name="스트리머", unique=True, max_length=20)

    def __str__(self):
        return self.player_streamer


class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sender')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='receiver')
    message = models.CharField(max_length=1200)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message

    class Meta:
        ordering = ('-timestamp',)


# user 생성시 자동으로 함수를 호출 된다. 그래서 함수명을 바꾸면 안되고 철자하나 틀리면 안됨
class MyAccountManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError('User must have an email address')
        if not username:
            raise ValueError('User must have a username')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=username,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Account(AbstractBaseUser):
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = models.CharField(max_length=11, unique=True)
    date_joined = models.DateTimeField(verbose_name='가입일', auto_now_add=True)
    last_login = models.DateTimeField(verbose_name='마지막 로그인', auto_now=True)
    is_admin = models.BooleanField(verbose_name="어드민", default=False)
    is_active = models.BooleanField(verbose_name="활동중", default=True)
    is_staff = models.BooleanField(verbose_name="스태프", default=False)
    is_superuser = models.BooleanField(verbose_name="슈퍼유저", default=False)
    is_match = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name="매칭된사람", blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    # python manage.py superuser 생성시 요구되는 필드를 정의한다.
    # 위에서 정의한 필드 들은 default 값이 있어서 굳이 요청을 하지 않아도 되기에 username 를 추가한다.
    # 이메일과 비밀번호 같은 경우 기본적으로 포함되어 있다.

    objects = MyAccountManager()

    def __str__(self):
        return str(self.username) + '-' + str(self.id)

    def has_perm(self, perm, obj=None):
        return self.is_superuser
    # 계정(객체)의 권한을 확인 한다. perm 은 구체적으로 어떤 권한 인지 세부적으로 나눠서 관리할 수 있다.

    def has_module_perms(self, app_label):
        return self.is_superuser
    # Returns True if the user has any permissions in the given package (the Django app label).
    # If the user is inactive, this method will always return False. For an active superuser, this method will always return True.
    # 세팅 파일에 있는 app 목록에 접근하는 권한 app 목록에는 예민한 것도 포함


@receiver(models.signals.post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_toke(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
