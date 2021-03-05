import os
import time
import re
from common.constant import Constant
import shutil


def archive_file(filepath=Constant.REPORT_DIR) -> None:  # 打包归档文件
    file = os.path.join(filepath, "history", time.strftime("%Y%m%d"))
    dirs = str(os.listdir(filepath))
    p = r"\w+.html"
    dirs = re.findall(p, dirs)
    if not os.path.exists(file) and dirs:
        os.makedirs(file)
    elif dirs:
        for i in dirs:
            shutil.move("{}/{}".format(filepath, i), file)


# archive_file(REPORT_DIR)  # 归档报告

def archive_log(filepath=Constant.LOGS_DIR) -> str:
    dir_name = os.path.join(filepath, time.strftime("%Y-%m"))
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    return os.path.join(dir_name, "{}.log".format(time.strftime('%Y-%m-%d')))
