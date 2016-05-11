import yaml
import salishsea_cmd.api


print('yo')
stream = open('/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/jpetrie/SMELT5x5test.yaml', 'r')
run_desc = yaml.load(stream)

salishsea_cmd.api.run_in_subprocess("test_salishsea_api", run_desc,'/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/iofiles/iodef_bio_1hr.xml','/data/jpetrie/MEOPAR/SalishSea/results/test_salishsea_api')

