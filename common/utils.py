import re
import exrex
import time
import random
import json
from common.logger import Logger

logger = Logger().log


class Parameterization:

    def __init__(self, context, db):
        """

        :param context: 存储临时变量的上下文类实例
        :param db: 数据库实例
        """
        self.env = getattr(context, "ENV")
        self.data = self.env.get("data")
        self.context = context
        self.db = db

    def get_data(self, var):
        try:
            value = getattr(self.context, var)
        except AttributeError:
            value = self.data.get(var)
        return str(value)

    # "#" 表示的是要从local variable里面取的参数
    def __replace(self, data):
        p = r"#(\w+?)#"
        for variable in re.finditer(p, data):
            variable = variable.group(1)
            value = self.get_data(variable)
            data = re.sub(p, value, data, count=1)
            logger.debug("正在进行替换#{}# ---->---> {}".format(variable, value))
        return data

    # "*" 表示的是要自己生成的参数
    def __generator(self, data):
        p = r"\*(\w+?)\*"
        for variable in re.finditer(p, data):
            variable = variable.group(1)
            func = getattr(self, variable)
            value = str(func())
            setattr(self.context, variable, value)
            data = re.sub(p, value, data, count=1)
            logger.debug("正在进行生成*{}* ---->---> {}".format(variable, value))
        return data

    @classmethod
    def __transform_type(cls, data):  # TODO: 此处可优化 直接利用 read_execl.CasesData的setattr方法即可
        try:  # TODO: 此处暂时这样处理, 如果想优化可以增加模式去区分
            try:
                data = json.loads(data)
            except json.decoder.JSONDecodeError:  # 此处防止用例非标准json
                data = eval(data)  #
        except (TypeError, SyntaxError, NameError, json.decoder.JSONDecodeError):
            pass
        return data

    def replace_data(self, data):
        data = str(data)
        logger.debug("数据处理前:{}".format(data))
        data = self.__replace(data)
        data = self.__generator(data)
        data = self.__transform_type(data)
        logger.debug("数据处理后:{}".format(data))
        return data


class Utils(Parameterization):
    """
    存放共用的工具类
    """

    def data_generator(self, pattern, sql):
        """
        数据生成器
        :param pattern: 正则表达式,用来生成符合该规则的数据
        :param sql: 用于判断生成数据是否唯一的sql
        :return:
        """
        sql = self.replace_data(sql)
        while True:
            value = exrex.getone(pattern)
            sql = sql.format(value)
            if not self.db.single_execute(sql):  # 如果数据库查不到,则表示该数据未被使用过,可以使用
                break
        logger.info("生成的数据为 ---->---> {}".format(value))
        return value

    @staticmethod
    def now_datetime():
        datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        return datetime

    @staticmethod
    def birthday(start="1-1-1971", end="31-12-1999"):
        start = time.strptime(start, "%d-%m-%Y")
        end = time.strptime(end, "%d-%m-%Y")
        start = time.mktime(start)
        end = time.mktime(end)
        time_tuple = time.localtime(random.randint(int(start), int(end)))
        return time.strftime("%d-%m-%Y", time_tuple)

    @staticmethod
    def appsflyer_id():
        pattern = r"[a-zA-Z0-9]{30}"
        return exrex.getone(pattern)


class OneProductDemoUtils(Utils):
    """
    存放某个产品线的工具类
    """

    def cellphone(self):
        pattern = r"+86\d{11}"
        sql = "SELECT id FROM account where phone = '{}' order by id desc;"
        phone = self.data_generator(pattern, sql)
        return phone


class TwoProductDemoUtils(Utils):

    def cellphone(self):
        pattern = r"+123\d{11}"
        sql = "SELECT id FROM account where phone = '{}' order by id desc;"
        phone = self.data_generator(pattern, sql)
        return phone
