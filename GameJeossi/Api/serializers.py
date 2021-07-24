from rest_framework import serializers
from .models import Account, ProfileCard, CardCommunity, CardStreamer, CardGameName, CardImage, Message


class RegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = Account
        fields = ['email', 'username', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def save(self, **kwargs):
        account = Account(
            email=self.validated_data['email'],
            username=self.validated_data['username']
        )
        password = self.validated_data['password']
        password2 = self.validated_data['password2']
        if password != password2:
            raise serializers.ValidationError({'password': 'Passwords must match.'})
        account.set_password(password)
        account.save()
        return account


class CardGameNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardGameName
        fields = ['player_game']


class CardImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardImage
        fields = ['image']


class CardCommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CardCommunity
        fields = ['player_community']


class CardStreamerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardStreamer
        fields = ['player_streamer']


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'username']


class ProfileCardSerializer(serializers.ModelSerializer):
    owner = MatchSerializer()
    game_name = CardGameNameSerializer()
    card_img = CardImageSerializer(many=True)
    community = CardCommunitySerializer(many=True)
    streamer = CardStreamerSerializer(many=True)

    class Meta:
        model = ProfileCard
        fields = ['id', 'owner', 'gamer_name', 'game_name', 'title', 'contents', 'game_day', 'card_img',
                  'game_hours_s', 'game_hours_e', 'is_noob', 'community', 'streamer', 'play_style']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'message', 'timestamp']
