import pytest


class TestSmoke:

    def test_smoke(self, data, case_template_object):
        if data.use == 0:
            pytest.skip("该用例跳过,不执行")
        case_template_object.case(data)

