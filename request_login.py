import requests
import re
from bs4 import BeautifulSoup

'''
1. request完成淘宝模拟登陆
'''

# requests库的session对象能够帮我们跨请求保持某些参数，也会在同一个session实例发出的所有请求之间保持cookies
s = requests.Session()

# 代理ip池
proxies = {
    'https': 'https://113.119.38.177:3128'
}
# 是否用代理
is_proxies = False

class Taobao:
    '''
    淘宝对象
    '''
    def __init__(self, username, ua, tpl_password):
        '''
        账户登陆对象
        :param username: 用户名
        :param ua: 淘宝的ua参数
        :param tpl_password: 加密后的密码
        '''

        # 淘宝最先登陆的页面URL
        self.first_url = 'https://login.taobao.com/'
        # 检测是否需要滑动验证码的URL
        self.nick_check_url = 'https://login.taobao.com/member/request_nick_check.do?_input_charset=utf-8'
        # 提交用户名密码登陆的URL
        self.login_url = 'https://login.taobao.com/member/login.jhtml'
        # 搜索物品URL
        self.search_url = 'https://s.taobao.com/search?q='

        # 淘宝用户名
        self.username = username
        self.ua = ua
        self.tpl_password = tpl_password
        self.time_out = 3
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0'
        }

    def __get_token__(self):
        '''
        获取登陆表单需要提交的ncoToken
        :return:
        '''
        if is_proxies:
            html = s.get(self.first_url, headers=self.headers, proxies=proxies).text
        else:
            html = s.get(self.first_url, headers=self.headers).text
        id_name = 'J_NcoToken'
        soup = BeautifulSoup(html, 'html.parser')
        self.ncoToken = soup.find('input', id=id_name)['value']
        print('ncoToken: ', self.ncoToken)

    def __nick_check__(self):
        '''
        检测是否需要滑动验证码的URL
        :return:
        '''
        data = {
            'username': self.username,
            'ua': self.ua
        }
        if is_proxies:
            resp = s.post(self.nick_check_url, headers=self.headers, proxies=proxies, data=data, timeout=self.time_out)
        else:
            resp = s.post(self.nick_check_url, headers=self.headers, data=data, timeout=self.time_out)

        print('是否需要滑动验证：', resp.text)

    def __login_first__(self):
        '''
        登陆并获取st_url
        :return:
        '''
        data = {
            'TPL_username': self.username,
            'TPL_password': '',
            'ncoSig': '',
            'ncoSessionid': '',
            'ncoToken': self.ncoToken,
            'slideCodeShow': 'false',
            'useMobile': 'false',
            'lang': 'zh_CN',
            'loginsite': '0',
            'newlogin': '0',
            'TPL_redirect_url': 'https://i.taobao.com/my_taobao.htm?nekot=eGlhb3dhbmdiYTJkYWk%3D1566972630567',
            'from': 'tb',
            'fc': 'default',
            'style': 'default',
            'css_style': '',
            'keyLogin': 'false',
            'qrLogin': 'true',
            'newMini': 'false',
            'newMini2': 'false',
            'tid': '',
            'loginType': '3',
            'minititle': '',
            'minipara': '',
            'pstrong': '',
            'sign': '',
            'need_sign': '',
            'isIgnore': '',
            'full_redirect': '',
            'sub_jump': '',
            'popid': '',
            'callback': '',
            'guf': '',
            'not_duplite_str': '',
            'need_user_id': '',
            'poy': '',
            'gvfdcname': '10',
            'gvfdcre': '68747470733A2F2F6C6F67696E2E74616F62616F2E636F6D2F6D656D6265722F6C6F676F75742E6A68746D6C3F73706D3D61317A30322E312E3735343839343433372E372E323432393738326432756876797126663D746F70266F75743D7472756526726564697265637455524C3D6874747073253341253246253246692E74616F62616F2E636F6D2532466D795F74616F62616F2E68746D2533466E656B6F7425334465476C6862336468626D646959544A6B59576B253235334431353636393732363330353637',
            'from_encoding': '',
            'sub': '',
            'TPL_password_2': self.tpl_password,
            'loginASR': '1',
            'loginASRSuc': '1',
            'allp': '',
            'oslanguage': 'zh-CN',
            'sr': '1366*768',
            'osVer': 'windows|6.1',
            'naviVer': 'firefox|68',
            'osACN': 'Mozilla',
            'osAV': '5.0 (Windows)',
            'osPF': 'Win32',
            'miserHardInfo': '',
            'appkey': '00000000',
            'nickLoginLink': '',
            'mobileLoginLink': 'https://login.taobao.com/member/login.jhtml?redirectURL=https://i.taobao.com/my_taobao.htm?nekot=eGlhb3dhbmdiYTJkYWk%3D1566972630567&useMobile=true',
            'showAssistantLink': '',
            'um_token': 'TA215EF3D75E8233F5AFBE8BD875A3C8D0665E19FF02B512F5B4CFA2AB8',
            'ua': self.ua,
        }
        try:
            if is_proxies:
                html = s.post(self.login_url, data=data, headers=self.headers, proxies=proxies, timeout=self.time_out).text
            else:
                html = s.post(self.login_url, data=data, headers=self.headers, timeout=self.time_out).text

        except Exception as e:
            print('登陆请求失败，原因: ')
            raise e

        # 获取st_url
        pattern = '<script src="(.*?)"'
        self.stURL = re.findall(pattern, html)[0]
        print('st码url: ', self.stURL)

        # 获取重定向url
        pattern = "redirectURL:'(.*?)'"
        self.redirectURL = re.findall(pattern, html)[0]
        print('重定向url: ', self.redirectURL)

    def __apply_st__(self):
        '''
        申请st码
        :return:
        '''
        try:
            if is_proxies:
                result = s.get(self.stURL, headers=self.headers, proxies=proxies)
            else:
                result = s.get(self.stURL, headers=self.headers)

        except Exception as e:
            print('申请st码请求失败，原因: ')
            raise e

        pattern = '"data":{"st":"(.*?)"'
        code = re.findall(pattern, result.text)
        if code:
            self.st_code = code[0]
            print('st码: ', self.st_code)
        else:
            raise RuntimeError('获取st码失败')

    def __login_redirect__(self):
        '''
        登陆重定向
        :return:
        '''
        try:
            if is_proxies:
                html = s.get(self.redirectURL, headers=self.headers, proxies=proxies).text
            else:
                html = s.get(self.redirectURL, headers=self.headers).text

        except Exception as e:
            print('重定向失败，原因: ')
            raise e

        # 获取用户名
        if html:
            id_name = 'mtb-nickname'
            soup = BeautifulSoup(html, 'html.parser')
            self.nickname = soup.find('input', id=id_name)['value']
            print('登陆成功，用户名为: ', self.nickname)
            return True
        else:
            return False

    def login(self):
        # 获取登陆必须参数token
        self.__get_token__()
        # 判断是否需要滑动条
        self.__nick_check__()
        # 登陆
        self.__login_first__()
        # 获取st码
        self.__apply_st__()
        # 登陆重定向
        return self.__login_redirect__()


if __name__ == '__main__':
    # 登陆必须参数，可以从浏览器或者抓包工具提取
    username = ''
    ua = ''
    tpl_password = ''

    # 建立淘宝对象
    taobao = Taobao(username, ua, tpl_password)
    # 登陆
    is_login = taobao.login()
