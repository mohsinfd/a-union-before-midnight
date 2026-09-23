import unittest
from dh_save_spans import Node,parse
import aubm_release_ownership as patch


def evaluate(n,state):
    checks=[]
    for f in n.fields:
        k,v=f.key,f.value
        if k=='NOT':checks.append(not evaluate(v,state))
        elif k=='AND':checks.append(evaluate(v,state))
        elif k=='OR':checks.append(any(evaluate(Node(fields=[x]),state) for x in v.fields))
        elif k=='exists':checks.append(v in state['exists'])
        elif k=='ispuppet':checks.append(v in state['puppets'])
        elif k=='puppet':checks.append(state['puppets'].get(v.all('country')[0])==v.all('country')[1])
        elif k=='war':checks.append(frozenset(v.all('country')) in state['wars'])
        elif k in ('owned','control','core'):
            p=v.get('province');tag=v.get('data')
            checks.append((tag,p) in state['cores'] if k=='core' else state[k].get(p)==tag)
        else:raise AssertionError(k)
    return all(checks)


class ReleaseTests(unittest.TestCase):
    def state(self):return dict(exists={'IND','INO','JAP'},puppets={},wars=set(),
                               owned={'1639':'IND'},control={'1639':'JAP'},cores={('INO','1639')})

    def run_callback(self,s):
        e=parse(patch.callback('INO')).get('event')
        for a in patch.actions(e):
            if not evaluate(a.get('trigger'),s):continue
            for c in a.all('command'):
                if not evaluate(c.get('trigger'),s):continue
                p=c.get('value');target=c.get('which')
                if s['owned'].get(p)=='IND':s['owned'][p]=target
                if s['control'].get(p)=='IND':s['control'][p]=target
            break

    def test_foreign_occupation_remains_without_war(self):
        s=self.state();self.run_callback(s)
        self.assertEqual(s['owned']['1639'],'INO');self.assertEqual(s['control']['1639'],'JAP')
        self.assertFalse(s['wars']);self.assertFalse(s['puppets'])
        before=repr(s);self.run_callback(s);self.assertEqual(repr(s),before)

    def test_failed_release_enemy_rival_puppet_and_indian_cores_protected(self):
        mutations=[lambda s:s['exists'].remove('INO'),lambda s:s['wars'].add(frozenset(['IND','INO'])),
                   lambda s:s['puppets'].update(INO='JAP'),lambda s:s['cores'].add(('IND','1639')),
                   lambda s:s['control'].update({'1639':'IND'}),lambda s:s['control'].update({'1639':'REB'}),
                   lambda s:s['owned'].update({'1639':'JAP'})]
        for change in mutations:
            s=self.state();change(s);before=repr(s);self.run_callback(s);self.assertEqual(repr(s),before)

    def test_indian_puppet_receives_title(self):
        s=self.state();s['puppets']['INO']='IND';self.run_callback(s);self.assertEqual(s['owned']['1639'],'INO')

    def test_callback_is_queued_before_release_with_original_gate(self):
        text='event = { id = 1 country = IND desc = "Test" action_a = { name = "Independent" command = { trigger = { flag = earned NOT = { exists = INO } } type = independence which = INO value = 1 } } }'
        files={patch.MODULE:text};result,_=patch.transform_all(files)
        e=parse(result[patch.MODULE]).all('event')[0];cs=e.get('action_a').all('command')
        self.assertEqual([c.get('type') for c in cs],['event','independence'])
        self.assertEqual(cs[0].get('when'),'1');self.assertEqual(cs[0].get('trigger').get('flag'),'earned')
        self.assertEqual(patch.transform_all(result)[0],result)

    def test_every_shared_helper_uses_preserve_control_transfers_only(self):
        for tag in patch.CALLBACKS:
            e=parse(patch.callback(tag)).get('event')
            for k in ['date','offset','deathdate','decision','trigger']:self.assertIsNone(e.get(k))
            self.assertEqual(e.get('name'),'AI_EVENT')
            for a in patch.actions(e):
                for c in a.all('command'):
                    self.assertEqual(c.get('type'),'secedeprovince');self.assertEqual(c.get('when'),'1')
                    self.assertEqual(c.get('which'),tag)


if __name__=='__main__':unittest.main()
