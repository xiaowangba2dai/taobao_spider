from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from openpyxl import workbook  # 写入Excel表所用

'''
使用selenium 实现淘宝的模拟登陆并采集数据
1. 推荐使用显式等待：指满足某一个条件之后在执行后面的代码，可以设置最长的等待时间
    (1) WebDriverWait库: 负责循环等待
    (2) expected_conditions: 负责条件
2. css定位
    （1） #: 表示id属性 driver.find_element_by_css_selector('#id_name')
    （2） .: 表示class属性    driver.find_element_by_css_selector('.class_name')
    （3） 标签直接使用  driver.find_element_by_css_selector('input')
    （4） 其他: driver.find_element_by_css_selector('[...="..."]')
3. xpath定位
    （1）browser.find_element_by_xpath('//*[@class="btn_tip"]/a/span')
        指的是从根目录(//)开始寻找任意(*)一个class名为btn_tip的元素，并找到btn_tip的子元素a标签中的子元素span
'''

class TaobaoSpider:

    def __init__(self, url, username, password, goods):
        '''
        初始化参数
        :param username:
        :param password:
        :param goods:
        '''

        self.url = url
        self.username = username
        self.password = password
        self.goods = goods
        self.currentPage = 1 # 当前页数

        driver = webdriver.ChromeOptions()
        # 设置为开发者模式，避免被识别，防止被各大网站识别出来使用了Selenium
        driver.add_experimental_option('excludeSwitches',['enable-automation'])
        # 不加载图片,加快访问速度
        driver.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
        self.browser = webdriver.Chrome(options=driver)
        self.wait = WebDriverWait(self.browser, 10)

    def login(self):
        '''
        登陆接口
        :return:
        '''
        self.browser.get(self.url)
        try:
            print('模拟淘宝登陆中...')
            # 点击密码登陆
            # (1) presence_of_all_elements_located 判断页面的元素是否已经加载出来
            # (2) element_to_be_clickable 判断当前的这个元素是否可以点击
            password_login = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.forget-pwd.J_Quick2Static'))
            )
            password_login.click()

            # 输入用户名
            username_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#TPL_username_1'))
            )
            username_element.send_keys(self.username)
            # 输入密码
            password_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#TPL_password_1'))
            )
            password_element.send_keys(self.password)

            # 等待几秒手动滑块验证
            time.sleep(5)
            # 点击登录
            login_btn = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#J_SubmitStatic'))
            )
            login_btn.click()

            # 等待几秒手动滑块验证
            time.sleep(5)
            # 输入密码
            password_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#TPL_password_1'))
            )
            password_element.send_keys(self.password)

            # 点击登录
            login_btn = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#J_SubmitStatic'))
            )
            login_btn.click()
            print('登录成功')
        except Exception as e:
            print('登陆失败', e)
        finally:
            pass

    def search_product(self):
        '''
        搜索商品
        :return:
        '''
        try:
            print('正在搜索商品：', self.goods)
            search_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
            )
            search_input.send_keys(self.goods)

            search_btn = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.btn-search'))
            )
            search_btn.click()
            time.sleep(2)

            now_handle = self.browser.current_window_handle  # 获取当前窗口的句柄
            # print(self.browser.title)  # 获取打开页面的标题

            all_handles = self.browser.window_handles  # 获取到当前所有的句柄,所有的句柄存放在列表当中
            print(all_handles)  # 打印句柄
            # 获取非最初打开页面的句柄
            for handles in all_handles:
                if now_handle != handles:
                    self.browser.switch_to_window(handles)
            # print(self.browser.title)  # 获取切换后的标题
            print(self.browser.page_source)
            return self.browser.page_source
        except Exception as e:
            print('搜索商品出错', e)
        finally:
            pass

    def get_information(self, html):
        '''
        根据搜索结果抓取商品信息
        (1) 抓取总页数
        (2) 获取商品名称，价格，运费，是否是天猫，店名，地区，购买人数
        (3) 写入excel文件
        (4) 翻页再次抓取
        :param html: 搜索商品返回的html
        :return:
        '''

        global ws  # 全局工作表对象

        # 获取总页数，仅仅在第一页获取
        if self.currentPage == 1:
            totalPage_pattern = '"totalPage":(.*?),'
            try:
                totalPage = re.findall(totalPage_pattern, html)
            except Exception as e:
                print('获取页码失败：', e)

            if totalPage:
                self.totalPage = int(totalPage[0])
                self.totalPage = 5
                print('商品总共有{}页'.format(self.totalPage))

        name_pattern = '"raw_title":"(.*?)"'    # 名称
        price_pattern = '"view_price":"(.*?)"'  # 价格
        fee_pattern = '"view_fee":"(.*?)"'      # 运费
        is_tmall_pattern = '"isTmall":(.*?),'   # 是否天猫
        nick_pattern = '"nick":"(.*?)"'         # 店名
        place_pattern = '"item_loc":"(.*?)"'    # 地区
        buy_num_pattern = '"view_sales":"(.*?)"'   # 购买人数

        try:
            name_list = re.findall(name_pattern, html)
            price_list = re.findall(price_pattern, html)
            fee_list = re.findall(fee_pattern, html)
            is_tmall_list = re.findall(is_tmall_pattern, html)
            nick_list = re.findall(nick_pattern, html)
            place_list = re.findall(place_pattern, html)
            buy_num_list = re.findall(buy_num_pattern, html)
        except Exception as e:
            print('获取商品信息失败：', e)

        # 将商品信息写入文件
        for i in range(len(name_list)):
            ws.append([name_list[i], price_list[i], fee_list[i], is_tmall_list[i], nick_list[i], place_list[i], buy_num_list[i]])

        print('爬取第{}页完成'.format(self.currentPage))

        # 下一页
        self.currentPage += 1
        if self.currentPage <= self.totalPage:
            nextPageURL = 'https://s.taobao.com/search?q={0}&s={1}'.format(self.goods, str(22*self.currentPage))
            self.browser.get(nextPageURL)
            time.sleep(1)
            self.get_information(self.browser.page_source)
        else:
            wb.save('data.xlsx')


if __name__ == '__main__':
    # 登陆url
    url = 'https://login.taobao.com/member/login.jhtml'
    # 用户名
    username = ''
    # 用户密码
    password = ''
    # 商品名称
    goods = '手机'

    #  创建Excel表并写入数据
    wb = workbook.Workbook()  # 创建Excel对象
    ws = wb.active  # 获取当前正在操作的表对象
    # 往表中写入标题行,以列表形式写入！
    ws.append(['商品名称', '价格', '运费', '是否天猫', '店名', '地区', '购买人数'])

    taobaoSpider = TaobaoSpider(url, username, password, goods)
    # 登陆
    taobaoSpider.login()
    # 搜索商品
    html = taobaoSpider.search_product()
    # 获取商品信息写入文件
    taobaoSpider.get_information(html)
