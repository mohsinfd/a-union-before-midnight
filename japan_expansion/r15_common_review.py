"""Cross-project budget, cancellation and ownership-lock checks; no game."""
import copy,unittest
import build as b
from FLOW_review import HumanWorld
from simulate import BY_KEY,BY_ID
import r15_common as c

b.prepare_catalog()


def register_test_projects():
    for suffix,retry in (('one',False),('two',False),('retry',True)):
        key='r15_test_'+suffix
        if key in BY_KEY:continue
        c.proposal(key,'An offline test project','A test-only transaction.',
                   'war = { country = JAP country = USA }',[
                       dict(label='First investment',cost=dict(money=100,supplies=400,oil=200,metal=100,manpower=10),days=30,
                            valid='control = { province = 1552 data = JAP }',rewards=[b.cmd('supplies',value=900)],focus='TEST'),
                       dict(label='Second investment',cost=dict(money=150,supplies=800,oil=100,metal=150,manpower=20),days=60,
                            valid='control = { province = 1552 data = JAP }',rewards=[b.cmd('supplies',value=1500)],focus='TEST_TWO')],
                   year=1941,retry_on_failure=retry,module='r15_test')
    b.IDS.update({e.key:e.id for e in b.EVENTS})
    BY_KEY.update({e.key:e for e in b.EVENTS});BY_ID.update({str(e.id):e for e in b.EVENTS})


register_test_projects()


def cached(w,key,index=0):
    for command in BY_KEY[key].actions[index].commands:w.command(b.parse(b.resolve(command)),'JAP')


class CommitmentReview(unittest.TestCase):
    def world(self):
        w=HumanWorld();w.year=1944;w.controlled[1552]=w.owned[1552]='JAP'
        w.resources['JAP'].update(money=5000,supplies=50000,oil=20000,metal=10000,manpower=500)
        return w

    def test_two_valid_offers_cannot_spend_the_same_commitment(self):
        w=self.world();start=copy.deepcopy(w.resources['JAP'])
        self.assertTrue(w.action('r15_test_one',0))
        self.assertFalse(w.action('r15_test_one',1));self.assertFalse(w.action('r15_test_two',0))
        for key,value in dict(money=100,supplies=400,oil=200,metal=100,manpower=10).items():self.assertEqual(w.resources['JAP'][key],start[key]-value)
        after=copy.deepcopy(w.resources);cached(w,'r15_test_two',0);cached(w,'r15_test_one',0)
        self.assertEqual(w.resources,after)

    def test_completion_releases_only_its_own_slot_and_replay_is_inert(self):
        w=self.world();w.action('r15_test_one');w.advance(30)
        self.assertFalse(w.flags.get('JX_R15_MAJOR_PENDING'))
        self.assertTrue(w.flags.get('JX_R15_TEST_ONE_CLOSED'));self.assertTrue(w.flags.get('JX_R15_FOCUS_TEST_DONE'))
        self.assertTrue(w.action('r15_test_two'));after=copy.deepcopy(w.resources)
        cached(w,'r15_test_one_finish_0');self.assertEqual(w.resources,after)
        self.assertTrue(w.flags.get('JX_R15_MAJOR_PENDING'))

    def test_abort_recovers_recruits_and_unspent_stocks_with_real_loss(self):
        for index,cost in enumerate((dict(money=100,supplies=400,oil=200,metal=100,manpower=10),dict(money=150,supplies=800,oil=100,metal=150,manpower=20))):
            w=self.world();start=copy.deepcopy(w.resources['JAP']);w.action('r15_test_one',index);w.advance(10)
            self.assertTrue(w.action('r15_test_one',4+index))
            for key,amount in start.items():
                lost=cost.get(key,0)*(1 if key=='money' else .25 if key=='supplies' else 0)
                self.assertEqual(w.resources['JAP'][key],amount-lost,(index,key))
            after=copy.deepcopy(w.resources);cached(w,'r15_test_one',4+index);self.assertEqual(w.resources,after)
            self.assertTrue(w.action('r15_test_two'));w.advance(20)
            self.assertTrue(w.flags.get('JX_R15_MAJOR_PENDING'),'Old completion must not clear new project lock')
            self.assertFalse(w.action('r15_test_one',1-index))

    def test_failed_delivery_full_refund_and_dated_retry(self):
        w=self.world();start=copy.deepcopy(w.resources['JAP']);w.action('r15_test_retry')
        w.controlled[1552]='USA';w.advance(30)
        self.assertEqual(w.resources['JAP'],start)
        self.assertFalse(w.flags.get('JX_R15_MAJOR_PENDING'));self.assertFalse(w.flags.get('JX_R15_TEST_RETRY_CLOSED'))
        w.controlled[1552]='JAP';self.assertFalse(w.action('r15_test_retry'))
        cached(w,'r15_test_retry_return_0');self.assertTrue(w.flags.get('JX_R15_TEST_RETRY_WAIT'))
        w.advance(89);self.assertFalse(w.action('r15_test_retry'))
        w.advance(1);self.assertTrue(w.action('r15_test_retry',1))
        after=copy.deepcopy(w.resources);cached(w,'r15_test_retry_finish_0');cached(w,'r15_test_retry_return_0')
        self.assertEqual(w.resources,after);self.assertTrue(w.flags.get('JX_R15_MAJOR_PENDING'))

    def test_early_finish_wrong_choice_and_insufficient_budget_cannot_reward(self):
        w=self.world();w.action('r15_test_one');after=copy.deepcopy(w.resources)
        cached(w,'r15_test_one_finish_0');cached(w,'r15_test_one_finish_1')
        self.assertEqual(w.resources,after)
        for resource in ('money','supplies','oil','metal','manpower'):
            v=self.world();v.resources['JAP'][resource]=0;before=copy.deepcopy(v.resources)
            self.assertFalse(v.action('r15_test_one'));cached(v,'r15_test_one')
            self.assertEqual(v.resources,before)

    def test_keep_available_and_dismiss_never_reserve_or_spend(self):
        w=self.world();before=copy.deepcopy(w.resources)
        self.assertTrue(w.action('r15_test_one',2));self.assertEqual(w.resources,before)
        self.assertTrue(w.action('r15_test_one',3));self.assertFalse(w.action('r15_test_one',0))
        self.assertEqual(w.resources,before);self.assertFalse(w.flags.get('JX_R15_MAJOR_PENDING'))

    def test_reopening_pending_offer_cannot_move_the_delivery_date(self):
        w=self.world();start=w.resources['JAP']['supplies'];w.action('r15_test_one')
        w.advance(10);self.assertTrue(w.action('r15_test_one',2))
        w.advance(19);self.assertTrue(w.action('r15_test_one',2))
        self.assertEqual(w.resources['JAP']['supplies'],start-400)
        w.advance(1)
        self.assertEqual(w.resources['JAP']['supplies'],start-400+900)
        self.assertTrue(w.flags.get('JX_R15_TEST_ONE_CLOSED'))
        self.assertFalse(w.flags.get('JX_R15_MAJOR_PENDING'))


if __name__=='__main__':unittest.main(verbosity=2)
