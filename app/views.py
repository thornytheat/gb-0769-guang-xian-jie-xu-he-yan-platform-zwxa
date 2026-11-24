from decimal import Decimal

LABELS = {'trace':'轨迹文件采信','calibration':'距离方向校准','pairs':'双端最优配对','loss':'接续损耗判定',
          'design':'设计实测对账','archive':'批次留档复跑','certificate':'光纤证据签发'}
CODES = {'PASS':'通过','OVER_LIMIT':'超限','INVALID_NET_GAIN':'净增益无效','SINGLE_SIDE_ONLY':'仅单端有测','NO_COUPLED_EVIDENCE':'双端缺证','DESIGN_OUTSIDE_LINK':'设计点越界'}


def metres(mm):
    return format(Decimal(mm)/1000, 'f')


def half_mm_metres(units):
    return f'{Decimal(units)/2000:.4f}'


def trace_frames(calibrated):
    span = calibrated['settings']['length_mm']
    return {side:[{**r, 'mark':f'{Decimal(r["chain_mm"]) * 100 / span:.5f}'}
                  for r in calibrated['aligned'][side]] for side in ('a','b')}
