from rest_framework import status
from rest_framework import viewsets
from django.core.paginator import Paginator
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from django_filters import rest_framework as filters
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import login, logout, authenticate
from rest_framework.pagination import PageNumberPagination
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from .serializers import RegistrationSerializer, ProfileCardSerializer, MatchSerializer, MessageSerializer
from .models import Account, ProfileCard, CardCommunity, CardStreamer, CardGameName, CardImage, Message


@api_view(['POST', ])
@permission_classes([])
@authentication_classes([])
def login_view(request):
    data = {}
    email = request.data.get('email', '0').lower()
    password = request.data.get('password', '0')
    user = authenticate(username=email, password=password)

    if user:
        login(request, user)
        try:
            token = request.user.auth_token
        except Account.auth_token.RelatedObjectDoesNotExist:
            token = Token.objects.create(user=user)
        data['response'] = 'Login success.'
        data['token'] = token.key
    else:
        data['response'] = 'Login fail.'

    return Response(data)


@api_view(['POST', ])
def logout_view(request):
    data = {}
    request.user.auth_token.delete()
    logout(request)
    data['response'] = 'Logout success.'

    return Response(data)


@api_view(['POST', ])
@permission_classes([])
@authentication_classes([])
def registration_view(request):
    data = {}
    email = request.data.get('email', '0').lower()
    # email 이 없을 경우 0을 반환함
    if validate_email(email):
        data['error_message'] = 'That email is already in use.'
        data['response'] = 'Error'
        return Response(data)

    username = request.data.get('username', '0')
    if validate_username(username):
        data['error_message'] = 'That username is already in use.'
        data['response'] = 'Error'
        return Response(data)

    serializer = RegistrationSerializer(data=request.data)
    if serializer.is_valid():
        account = serializer.save()
        data['response'] = 'successfully registered new user.'
        data['email'] = account.email
        data['pk'] = account.pk
        token = Token.objects.get(user=account).key
        data['token'] = token

        admin = Account.objects.get(id=1)
        account.is_match.add(admin)
        mess = {"sender": admin,
                "message": "   " 





    else:
        data = serializer.errors

    return Response(data)


#################################################################################


@api_view(['POST'])
def create_card(request):
    data = {"owner": request.user,
            "title": request.data["title"],
            "contents": request.data["contents"],
            "game_day": request.data["game_day"],
            "game_hours_s": request.data["game_hours_s"],
            "game_hours_e": request.data["game_hours_e"],
            "is_noob": request.data["is_noob"],
            "play_style": request.data["play_style"],
            "gamer_name": request.data["gamer_name"],
            "game_name": request.data["game_name"],
            "streamer": request.data.getlist("streamer"),
            "community": request.data.getlist("community"),
            "images": request.data.getlist("images"),
            }

    images = data.pop('images')
    if not images:
        return Response({'response': 'create fail.'})
    community_data = data.pop('community')
    streamer_data = data.pop('streamer')
    game_name = data["game_name"].replace(" ", "")
    # 띄어쓰기 제거
    data["game_name"] = CardGameName.objects.get_or_create(player_game=game_name)[0]
    temp_list = [[], []]
    temp_list[0] = community_exist(community_data[:10])
    temp_list[1] = streamer_exist(streamer_data[:10])
    images_list = images_url(images, data["owner"])

    p_card = ProfileCard.objects.create(**data)
    try:
        p_card.community.add(*temp_list[0])
        p_card.streamer.add(*temp_list[1])
        p_card.card_img.add(*images_list)
    except:
        p_card.delete()
        data = {'response': 'create fail.'}
        return Response(data)

    data.pop('owner')
    data["game_name"] = game_name
    data["community"] = community_data
    data["streamer"] = streamer_data
    data['response'] = 'create success.'

    return Response(data)


@api_view(['DELETE'])
def delete_card(request):
    try:
        p_card = ProfileCard.objects.get(id=request.data['card_id'])
    except ProfileCard.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if int(str(p_card).split('-')[0]) != request.user.id:
        return Response({"response": "permission denied"}, status=status.HTTP_404_NOT_FOUND)

    operation = p_card.delete()
    if operation:
        return Response({"response": "delete success."})
    else:
        return Response({'response': "wrong request"})


@api_view(['PUT'])
def like_card(request):
    try:
        p_card = ProfileCard.objects.select_related('owner').get(id=request.data['card_id'])
    except ProfileCard.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if p_card.owner == request.user:
        return Response({'response': "wrong request"})

    # 좋아요
    if int(request.data['is_like']) == 1:
        p_card.liker.add(request.user)
        user_card = ProfileCard.objects.select_related('owner').filter(owner=request.user, liker=p_card.owner)
        if user_card:
            user_card[0].owner.is_match.add(p_card.owner)
            p_card.owner.is_match.add(user_card[0].owner)
            Response({"response": "New match!"})

    # 싫어요
    if int(request.data['is_like']) == 0:
        p_card.disliker.add(request.user)

    return Response({"response": "like success."})


@api_view(['PUT'])
def unmatch(request):
    try:
        unmatch_user = Account.objects.get(id=request.data['user_id'])
    except Account.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    unmatch_user.is_match.remove(request.user)
    request.user.is_match.remove(unmatch_user)
    unmatch_card = ProfileCard.objects.filter(owner=unmatch_user, liker=request.user)
    for card in unmatch_card:
        card.liker.remove(request.user)

    return Response({"response": "unmatch success."})


@api_view(['GET'])
def match_list(request):
    match_user = request.user.is_match.all()[:100]
    serializer = MatchSerializer(match_user, many=True)

    return Response({'results': serializer.data, 'requestId': request.user.id})


@api_view(['GET'])
def message_list(request, sender=None, receiver=None):
    if request.user.id == receiver:
        # 받은 입장
        try:
            chat = Message.objects.filter(sender=sender, receiver=receiver)[:100]
        except Message.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        # 채팅 내용 없음

        serializer = MessageSerializer(chat, many=True)
        return Response({'results': serializer.data})

    if request.user.id == sender:
        # 보낸 입장
        try:
            chat = Message.objects.filter(sender=sender, receiver=receiver)[:100]
        except ProfileCard.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        # 채팅 내용 없음

        serializer = MessageSerializer(chat, many=True)
        return Response({'results': serializer.data})

    return Response({"response": "permission denied"})


@api_view(['POST'])
def send_message(request):
    data = {"sender": request.user,
            "message": request.data["message"],
            "receiver": Account.objects.get(id=request.data["user_id"]),
            }

    Message.objects.create(**data)

    return Response({"response": "message send success."})


@api_view(['GET'])
def user_info(request):
    return Response({'results': {'username': request.user.username,
                                 'email': request.user.email,
                                 'userid': request.user.id}})


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class ProfileCardFilter(filters.FilterSet):
    streamer_in = CharInFilter(field_name='streamer__player_streamer', lookup_expr='in')
    community_in = CharInFilter(field_name='community__player_community', lookup_expr='in')

    class Meta:
        model = ProfileCard
        fields = ['streamer_in', 'community_in', 'owner__id', 'is_noob', 'game_name__player_game']


class ProfileCardListView(ListAPIView):
    serializer_class = ProfileCardSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = PageNumberPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = ProfileCardFilter

    def get_queryset(self):
        userinfo = self.request.query_params.get('getUser', None)
        owner_id = self.request.query_params.get('owner__id', None)
        if userinfo:
            return ProfileCard.objects.prefetch_related('streamer', 'community', 'card_img').select_related(
                'game_name', 'owner').filter(owner__id=self.request.user.id)
        if owner_id:
            return ProfileCard.objects.prefetch_related('streamer', 'community', 'card_img').select_related('game_name', 'owner')
        return ProfileCard.objects.prefetch_related('streamer', 'community', 'card_img').select_related(
            'game_name', 'owner').exclude(owner=self.request.user).exclude(liker=self.request.user).exclude(disliker=self.request.user)


#################################################################################


def validate_email(email):
    try:
        account = Account.objects.get(email=email)
    except Account.DoesNotExist:
        return None
    if account:
        return email


def validate_username(username):
    try:
        account = Account.objects.get(username=username)
    except Account.DoesNotExist:
        return None
    if account:
        return username


def community_exist(community_data):
    communities = [c.replace(" ", "") for c in community_data]
    community_list = []
    community_set = CardCommunity.objects.filter(player_community__in=communities)
    for community in community_set:
        community_list.append(community)
        if str(community) in communities:
            communities.remove(str(community))
    for community in communities:
        community_list.append(CardCommunity.objects.create(player_community=community))

    return community_list


def streamer_exist(streamer_data):
    streamers = [s.replace(" ", "") for s in streamer_data]
    streamer_list = []
    streamer_set = CardStreamer.objects.filter(player_streamer__in=streamers)
    for streamer in streamer_set:
        streamer_list.append(streamer)
        if str(streamer) in streamers:
            streamers.remove(str(streamer))
    for streamer in streamers:
        streamer_list.append(CardStreamer.objects.create(player_streamer=streamer))

    return streamer_list


def images_url(image_data, owner_data):
    images = []
    for img in image_data:
        images.append(CardImage.objects.create(image=img, owner=owner_data))

    return images
