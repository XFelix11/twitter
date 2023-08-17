from testing.testcases import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
# Create your tests here.

LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'

class AccountApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = self.create_user(
            username='admin',
            email='admin@jiuzhang.com',
            password='correct password',
        )

    # def create_user(self, username, email, password):
    #     #we can not code like User.objects.create() here
    #     #because password need to be encoded and  username and email need to be normalized 
    #     return User.objects.create_user(username, email, password)
    
    def test_login(self):
        #every test function need to be named beginning with test_ and it will be called when testing 
        #测试必须用post而不是get
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        #登陆失败， http status code返回 405 = METHOD_NOT_ALLOWED
        self.assertEqual(response.status_code, 405)

        #用了post， 但密码错了
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrong password',
        })
        self.assertEqual(response.status_code, 400)

        #用了post和正确的密码， 但username错了
        response = self.client.post(LOGIN_URL, {
            'username': 'notexists',
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data['errors']['username'][0]), 'User does not exist.')

        #验证还没登录
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)
        #用正确的密码
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['email'], 'admin@jiuzhang.com')
        #验证已经登录了
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        #先登录
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        #验证用户已经登录
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)
        #测试必须用post
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)
        #改用post成功logout
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)
        #验证用户已经登出
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'someone',
            'email': 'someone@jiuzhang.com',
            'password': 'any password',
        }
        #测试必须用post 这里用get， 请求失败
        response = self.client.get(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 405)

        #测试错误的邮箱
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'not a correct email',
            'password': 'any password'
        })
        self.assertEqual(response.status_code, 400)

        #测试密码太短
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@jiuzhang.com',
            'password': '123',
        })
        self.assertEqual(response.status_code, 400)

        #测试用户名太长
        response = self.client.post(SIGNUP_URL, {
            'username': 'username is toooooooooo loooooooooooong',
            'email': 'someone@jiuzhang.com',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)

        #成功注册
        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')
        
        # 验证 user profile 已经被创建
        created_user_id = response.data['user']['id']
        profile = UserProfile.objects.filter(user_id=created_user_id).first()
        self.assertNotEqual(profile, None)

        #验证用户已经登入
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)






















