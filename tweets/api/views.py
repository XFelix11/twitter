from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from tweets.api.serializers import (
    TweetSerializer, 
    TweetSerializerForCreate, 
    TweetSerializerForDetail,
)
from tweets.models import Tweet
from newsfeeds.services import NewsFeedService
from utils.decorators import required_params
from utils.paginations import EndlessPagination
from tweets.services import TweetService
from ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator


class TweetViewSet(viewsets.GenericViewSet):
    """
    API endpoint that allows users to create, list tweets
    """
    serializer_class = TweetSerializerForCreate
    queryset = Tweet.objects.all()
    pagination_class = EndlessPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    @required_params(params=['user_id'])
    def list(self, request):
        """
        重载 list 方法，不列出所有 tweets，必须要求指定 user_id 作为筛选条件
        """

        # # 这句查询会被翻译为
        # # select * from twitter_tweets
        # # where user_id = xxx
        # # order by created_at desc
        # # 这句 SQL 查询会用到 user 和 created_at 的联合索引
        # # 单纯的 user 索引是不够的
        # user_id = request.query_params['user_id']
        # tweets = TweetService.get_cached_tweets(user_id=user_id)
        # tweets = self.paginate_queryset(tweets)
        user_id = request.query_params['user_id']
        #tweets = Tweet.objects.filter(user_id=user_id).prefetch_related('user')
        cached_tweets = TweetService.get_cached_tweets(user_id)
        page = self.paginator.paginate_cached_list(cached_tweets, request)
        if page is None:
            # 这句查询会被翻译为
            # select * from twitter_tweets
            # where user_id = xxx
            # order by created_at desc
            # 这句 SQL 查询会用到 user 和 created_at 的联合索引
            # 单纯的 user 索引是不够的
            queryset = Tweet.objects.filter(user_id=user_id).order_by('-created_at')
            page = self.paginate_queryset(queryset)

        serializer = TweetSerializer(
            page, 
            context={'request':request}, 
            many=True
        )
        # 一般来说 json 格式的 response 默认都要用 hash 的格式
        # 而不能用 list 的格式（约定俗成）
        return self.get_paginated_response(serializer.data)
    
    @method_decorator(ratelimit(key='user_or_ip', rate='5/s', method='GET', block=True))
    def retrieve(self, request, *args, **kwargs):
        tweet = self.get_object()
        serializer = TweetSerializerForDetail(
            tweet,
            context={'request': request},
        )
        return Response(serializer.data)
        
    @method_decorator(ratelimit(key='user', rate='1/s', method='POST', block=True))
    @method_decorator(ratelimit(key='user', rate='5/m', method='POST', block=True))
    def create(self, request, *args, **kwargs):
        """
        重载 create 方法，因为需要默认用当前登录用户作为 tweet.user
        """
        serializer = TweetSerializerForCreate(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': "Please check input",
                'errors': serializer.errors,
            }, status=400)
        #save will call create method in TweetSerializerForCreate
        tweet = serializer.save()
        NewsFeedService.fanout_to_followers(tweet)
        return Response(
            TweetSerializer(
            tweet, context={'request':request},).data, 
            status=201,
        )
    
