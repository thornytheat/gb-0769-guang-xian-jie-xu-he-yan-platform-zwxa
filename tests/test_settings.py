import pytest

from app.errors import InspectionError
from app.modules.calibration.contract import setup


@pytest.mark.parametrize('patch, code', [({'zero_a_m':-1},'BAD_SETTING'),({'pair_tol_m':2000},'BAD_LINK_RANGE'),({'length_m':False},'BAD_SETTING')])
def test_settings_have_strict_range(dirty,patch,code):
    with pytest.raises(InspectionError,match=code):
        setup({**dirty['settings'],**patch})
