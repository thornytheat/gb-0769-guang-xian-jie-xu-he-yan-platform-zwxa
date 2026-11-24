from .errors import InspectionError
from .modules.trace.service import ingest
from .modules.calibration.contract import setup
from .modules.calibration.service import calibrate
from .modules.pairs.service import join
from .modules.loss.service import judge
from .modules.design.service import reconcile


def run(material, stage='design'):
    if any(len(text)>250_000 for text in material['traces'].values()):
        raise InspectionError('TRACE_TOO_LARGE', status=413)
    output = {'trace': ingest(material['traces'])}
    if stage == 'trace':
        return output
    config = setup(material.get('settings'))
    output['calibration'] = calibrate(output['trace']['traces'], config)
    if stage == 'calibration':
        return output
    output['pairs'] = join(output['calibration'])
    if stage == 'pairs':
        return output
    output['loss'] = judge(output['pairs'], config)
    if stage != 'loss':
        output['design'] = reconcile(output['calibration'], output['pairs'], output['loss'])
    return output
