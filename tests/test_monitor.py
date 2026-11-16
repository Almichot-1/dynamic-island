import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import fcntl

spec = importlib.util.spec_from_file_location('monitor', str(Path(__file__).resolve().parents[1] / 'scripts/island-codex-monitor.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MonitorTests(unittest.TestCase):
    def test_new_question_alerts_without_hooks_and_async_acceptance_stays_pending(self):
        alerts=[]
        s=m.Session('s','/unused',on_attention=lambda call,stamp: alerts.append(call))
        s.watch_started=0
        s.take({'timestamp':'2026-11-16T08:00:00Z','type':'response_item','payload':
                {'type':'function_call','name':'request_user_input_async','call_id':'question-1'}})
        self.assertEqual(alerts,['question-1'])
        s.take({'timestamp':'2026-11-16T08:00:01Z','type':'response_item','payload':
                {'type':'function_call_output','call_id':'question-1','output':'{"accepted":true}'}})
        self.assertEqual(s.state,'asking')
        s.take({'timestamp':'2026-11-16T08:00:02Z','type':'response_item','payload':
                {'type':'message','role':'user','content':[{'type':'input_text','text':'<send_user_message_question_reply>answer</send_user_message_question_reply>'}]}})
        self.assertEqual(s.state,'working')
        s.take({'timestamp':'2026-11-16T08:00:02Z','type':'event_msg','payload':{'type':'task_complete'}})
        self.assertEqual(s.state,'idle')

    def test_turn_lifecycle_and_input_resolution(self):
        s = m.Session('test', '/unused')
        def take(kind, body):
            s.take({'timestamp':'2026-11-16T08:00:00Z','type':kind,'payload':body})
        take('event_msg', {'type':'task_started'})
        self.assertEqual(s.state, 'working')
        take('response_item', {'type':'function_call','name':'request_user_input','call_id':'q1'})
        self.assertEqual(s.state, 'asking')
        take('response_item', {'type':'function_call_output','call_id':'q1'})
        self.assertEqual(s.state, 'working')
        take('event_msg', {'type':'task_complete'})
        self.assertEqual(s.state, 'idle')

    def test_permission_hook_is_informational_and_deduplicated(self):
        event = {'session_id':'session-test','hook_event_name':'PermissionRequest',
                 'turn_id':'turn-1','tool_use_id':'tool-1','cwd':'/tmp/project',
                 'tool_input':{'command':'example'}}
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.subprocess, 'run') as send:
            self.assertIsNone(m.hook(event, Path(tmp)))
            m.hook(event, Path(tmp))
            self.assertEqual(send.call_count, 1)
            row = json.loads((Path(tmp)/'session-test.json').read_text())
            self.assertEqual(row['state'], 'asking')
            self.assertEqual(row['reason'], 'approval')
            self.assertNotIn('decision',row)
            self.assertNotIn('command',row)
            event['hook_event_name']='PostToolUse'
            m.hook(event,Path(tmp))
            self.assertEqual(json.loads((Path(tmp)/'session-test.json').read_text())['state'],'working')

    def test_new_input_request_produces_attention_alert(self):
        event={'session_id':'session-test','hook_event_name':'PreToolUse',
               'turn_id':'t1','tool_name':'request_user_input','tool_use_id':'input-1'}
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.subprocess,'run') as send:
            m.hook(event,Path(tmp))
            self.assertEqual(send.call_count,1)
            self.assertIn('Codex needs your input',send.call_args.args[0])

    def test_mentions_are_not_input_requests(self):
        self.assertFalse(m.needs_input('exec','print("request_user_input documentation")'))
        self.assertTrue(m.needs_input('exec','await tools.request_user_input_async({questions: []})'))

    def test_all_locked_sessions_and_no_abandoned_sessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); folder=root/'thread-writer-locks'; folder.mkdir()
            held=[]
            try:
                for i in range(7):
                    f=(folder/f'agent-{i}.lock').open('w'); fcntl.flock(f,fcntl.LOCK_EX); held.append(f)
                (folder/'closed.lock').touch()
                self.assertEqual(set(m.held_threads(root)),{f'agent-{i}' for i in range(7)})
            finally:
                for f in held:f.close()

    def test_old_hook_does_not_override_completed_turn(self):
        s=m.Session('s','/unused'); s.lifecycle=2000; s.state='idle'
        self.assertEqual(s.snapshot({}, {'updatedAt':1000,'state':'asking'})['state'],'idle')


if __name__=='__main__':unittest.main()
