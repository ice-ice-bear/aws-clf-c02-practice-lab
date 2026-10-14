import json
import subprocess
import unittest
from pathlib import Path

import app
from session_report import build_session_report
from test_session_report import item


ROOT = Path(__file__).resolve().parents[1]


class SessionReportUiTest(unittest.TestCase):
    def test_report_rendering_retry_links_and_read_only_result_loading(self):
        report = build_session_report([item("iam", 0, 100), item("iam", 1),
                                       item("compute", None)], app.DOMAIN_WEIGHTS, app.EXAM_PACE_SECONDS)
        script = r"""
        const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
        class Node {
          constructor(tag){this.tagName=tag;this.children=[];this.textContent='';this.classList={add(){},toggle(){}};}
          append(...nodes){this.children.push(...nodes);}
          replaceChildren(...nodes){this.children=nodes;}
          scrollIntoView(){}
        }
        const nodes=new Map();
        const document={hidden:false,createElement:tag=>new Node(tag),getElementById(id){
          if(!nodes.has(id))nodes.set(id,new Node('div'));return nodes.get(id);
        }};
        const context=vm.createContext({document,assert,fixture:JSON.parse(fs.readFileSync(0,'utf8')),
          console, performance:{now:()=>1000},calls:[],rendered:null});
        const source=fs.readFileSync('static/app.js','utf8');
        vm.runInContext(source.slice(0,source.indexOf('for(let i=1;i<=23;i++)')),context);
        vm.runInContext(`
          session={id:1,total:3,complete:true,report:fixture};
          rendered=renderSessionReport(session);
          setView=view=>calls.push(['view',view]);loadQuestion=id=>calls.push(['question',id]);
        `,context);
        const all=[];function visit(node){all.push(node);for(const child of node.children)visit(child);}
        visit(context.rendered);
        const texts=all.map(n=>n.textContent).join('\n');
        assert.match(texts,/33\.3/);assert.match(texts,/50\.0%/);
        assert.match(texts,/시간 기록 없음/);assert.match(texts,/영역 진단/);
        assert.match(texts,/실제 AWS 시험/);assert.match(texts,/문항별 복습/);
        const retries=all.filter(n=>n.textContent==='관련 문제 다시 풀기');
        assert.equal(retries.length,2);retries[0].onclick();
        assert.equal(context.calls[1][1],context.fixture.concepts[0].question_ids[0]);
        assert.equal(all.filter(n=>n.tagName==='caption').length,2);
        const links=all.filter(n=>n.textContent==='개념 읽기');
        assert.ok(links.every(n=>n.href.startsWith('#concept=')));
        vm.runInContext(`
          api=async (path,body)=>{calls.push(['api',path,body]);return {session:{id:1,complete:true}};};
          applySession=value=>{assert.equal(value.id,1);};
          renderSessionChrome=()=>{};
          globalThis.task=loadSession(1,true);
        `,context);
        (async()=>{
          await context.task;
          const call=context.calls.at(-1);assert.equal(call[1],'/api/session?id=1');assert.equal(call[2],undefined);
          vm.runInContext('rendered=renderSessionReport({total:3,report:null});',context);
          assert.match(context.rendered.children[1].textContent,/재시작/);
        })().catch(error=>{console.error(error);process.exitCode=1;});
        """
        result = subprocess.run(["node", "-e", script], cwd=ROOT, input=json.dumps(report), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
