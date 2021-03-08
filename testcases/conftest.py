import pytest

from common.case_base import CaseBase
from common.context import Context
from common.http_request import HTTPRequest
from common.mysql_data import MySqlData
from common.hook_func import *


@pytest.fixture(scope="session")
def setup_init():
    db_conf = getattr(Context, "ENV").get("mysql")  # 数据库配置
    db = MySqlData(db_conf["host"], user=db_conf["user"], password=db_conf["password"])
    request = HTTPRequest()
    yield db, request


@pytest.fixture(scope="class")
def case_template_object(setup_init, worker_id, tmp_path_factory):
    db = setup_init[0]
    request = setup_init[1]
    context = Context()
    get_token(worker_id, tmp_path_factory, db, request, context)
    case = CaseBase(db=db, request=request, context=context, utils=get_utils())
    yield case


if __name__ == '__main__':
    pytest.main(["-v", "-E=test", "-P=G", "-n=auto", "--dist=loadscope",
                 "--rename=on", r"--skip-json=../skip.json", "--mark=test",
                 "--alluredir=../reports/allure-result"])
