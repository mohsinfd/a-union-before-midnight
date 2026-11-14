"""Small native-format save fixtures test migration and duplicate prevention."""
import unittest
import build as b
from repair_purchases_r15_2 import repair_text,section,normalised_trade


def fixture():
    flags='\n'.join('JX_'+key+'_'+state+' = '+str(value) for key in
        ('prewar_deck_commission','prewar_navigation_trials') for state,value in
        (('PENDING',1),('DONE',0),('SELECTED_0',1)))
    provinces='\n'.join('province = {\n id = '+str(p)+'\n ic = { size = 10 current_size = 10 }\n}' for p in (1544,1550,1552,1554,1557))
    return ('name = "Test" saved = JAP header = { startdate = { year = 1936 month = april day = 0 hour = 0 }\n'
            'id = { type = 4712 id = 100 }\n}\n'
            'globaldata = { flags = { '+flags+'\n JX_EARLY_oil1934_DONE = 1\n JX_EARLY_fx1933_DONE = 1\n }\n'
            'queued_events = { event = { tag = JAP id = 28600667 hour = 105 } }\n'
            'treaty = { id = { type = 4712 id = 90 } type = trade country = "USA" country = "JAP" '
            'expirydate = { year = 1948 month = december day = 29 hour = 0 } oil = -50 supplies = 15 cancel = no }\n}\n'
            +provinces+'\ncountry = {\n tag = JAP\n transports = 716 escorts = 165 money = 1000 oil = 74000\n'
            'upgrade = { cag = { morale = 12 } }\n}\n'
            'eyr = { history = {\n'
            'name = "8:00 August 3, 1934 : We went with Buy a further 24 oil daily in The oil law needs an actual reserve."\n'
            'name = "22:00 November 18, 1934 : We went with Buy 24 oil and 12 metal daily in Buy oil for a larger fleet."\n'
            '} }\nhistory = { 28600001 }\n')


class SaveReview(unittest.TestCase):
    def test_restore_once_preserves_shipping_bill_units_and_existing_trade(self):
        original=fixture();after,report=repair_text(original)
        self.assertEqual(section(original,'country','JAP')[2],section(after,'country','JAP')[2])
        g=section(after,'globaldata')[2];trades=b.getall(g,'treaty')
        self.assertEqual(len(trades),3)
        self.assertEqual(sum(normalised_trade(t)==(50.,0.,-15.,0.) for t in trades),1)
        queue=b.getall(b.get(g,'queued_events'),'event')
        self.assertEqual([(b.get(q,'id'),b.get(q,'hour')) for q in queue],
                         [('28600667','105'),('28601743','1'),('28601746','1')])
        self.assertEqual(b.get(b.get(section(after,'header')[2],'id'),'id'),'103')
        self.assertTrue(all(b.get(t,'cancel')=='no' for t in trades))
        self.assertEqual(report['contracts'][0]['expiry']['year'],'1937')
        twice,_=repair_text(after);self.assertEqual(twice,after)

    def test_already_delivered_training_is_not_awarded_again(self):
        source=fixture().replace('_DONE = 0','_DONE = 1').replace('_PENDING = 1','_PENDING = 0')
        after,report=repair_text(source)
        self.assertTrue(all(r['status']=='already_delivered' for r in report['receipts']))
        queue=b.getall(b.get(section(after,'globaldata')[2],'queued_events'),'event')
        self.assertEqual(len(queue),1)

    def test_existing_matching_contract_is_not_duplicated(self):
        once,_=repair_text(fixture());again,report=repair_text(once)
        self.assertEqual(once,again)
        self.assertTrue(all(r['status']=='already_present' for r in report['contracts']))

    def test_expired_contracts_do_not_restart_with_a_new_full_duration(self):
        source=fixture().replace('August 3, 1934','August 3, 1931').replace('November 18, 1934','November 18, 1931')
        after,report=repair_text(source)
        self.assertTrue(all(r['status']=='expired_not_restored' for r in report['contracts']))
        self.assertEqual(len(b.getall(section(after,'globaldata')[2],'treaty')),1)


if __name__=='__main__':unittest.main(verbosity=2)
