import logging
from functools import wraps
from common.context import Context
from logging.handlers import RotatingFileHandler
from common.constant import Constant
from common.record import archive_log


def singleton(cls):
    __cls = dict()

    @wraps(cls)
    def single(*args, **kwargs):
        if __cls.get(cls):
            return __cls[cls]
        else:
            __cls[cls] = cls(*args, **kwargs)
            return __cls[cls]

    return single


@singleton
class Logger:
    """
    default level config
    """
    logger_level = "INFO"
    stream_level = "INFO"
    file_level = "INFO"
    file_level_rf = "INFO"
    log_name = "AutoApiTest"

    def __init__(self):
        self.file = archive_log(Constant.LOGS_DIR)
        # 实例化日志收集器
        log = logging.getLogger(self.log_name)
        log.setLevel(self.logger_level)
        self.log_stream = self.__stream_output()
        self.log_rotating = self.__file_rotating_output()

        # 将实例化渠道添加到收集器中
        log.addHandler(self.log_stream)
        # log.addHandler(log_file)
        log.addHandler(self.log_rotating)

        self.log = log
        self.info = self.log.info
        self.debug = self.log.debug
        self.error = self.log.error
        self.warning = self.log.warning

    def __stream_output(self):
        # 设置日志格式
        log_fmt = logging.Formatter(fmt='%(asctime)s - [%(levelname)s]: \n%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        # 实例化控制台渠道
        log_stream = logging.StreamHandler()
        log_stream.setFormatter(log_fmt)
        log_stream.setLevel(self.stream_level)
        return log_stream

    def __file_output(self):
        # 设置日志格式
        log_fmt = logging.Formatter(fmt='%(asctime)s - [%(levelname)s]: \n%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        # 实例化输出文件渠道
        log_file = logging.FileHandler(self.file, encoding="UTF-8")
        log_file.setFormatter(log_fmt)
        log_file.setLevel(self.file_level)
        return log_file

    def __file_rotating_output(self):
        # 设置日志格式
        log_fmt = logging.Formatter(fmt='%(asctime)s - [%(levelname)s]: \n%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        # 日志文件过大处理, 当单个日志文件大于10M时, 重新开新的文件, 最多4个
        log_rotating = RotatingFileHandler(self.file, maxBytes=2560000, backupCount=3, encoding="utf8")
        log_rotating.setFormatter(log_fmt)
        log_rotating.setLevel(self.file_level_rf)
        return log_rotating

    def __get_config(self):
        try:
            log_config = getattr(Context, "ENV").get("log")
            self.logger_level = log_config['logger_level']
            self.stream_level = log_config['stream_level']
            self.file_level = log_config['file_level']
            self.file_level_rf = log_config['file_level_rf']
        except AttributeError as e:
            self.error(f"Configuration not read: Msg:{e}")

    def __remove_output(self):
        self.log_stream.close()
        self.log_rotating.close()
        self.log.removeHandler(self.log_stream)
        self.log.removeHandler(self.log_rotating)

    def init(self):
        self.__get_config()
        self.__remove_output()
        self.__init__()
        return self


logger = Logger()
if __name__ == '__main__':
    logger1 = Logger()
    logger2 = Logger()
    logger1.info("========asdas=========")
    logger1.info("asfasfsafas")
    logger1.log.debug("asfasfsafas")
    logger2.log.info("asfasfsafas")
    logger2.log.debug("asfasfsafas")
    logger2.log.debug("asfasfsafas")
    logger2.log.debug("asfasfsafas")

    logger1.log.info("=======================")

    logger2 = Logger().init()
    logger3 = Logger()
    logger4 = Logger()
    logger1.log.info("asfasfsafas")
    logger1.log.debug("asfasfsafas")
    logger3.log.info("asfasfsafas")
    logger3.log.debug("asfasfsafas")