import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class QuestionConceptTest(unittest.TestCase):
    def test_matching_note_and_timer_survive_open_close_and_hidden_tab(self):
        script = r"""
        const assert = require('node:assert/strict');
        const fs = require('node:fs');
        const vm = require('node:vm');
        let now = 1000;
        const nodes = new Map();
        const document = {hidden: false, getElementById(id) {
          if (!nodes.has(id)) nodes.set(id, {open: false,
            showModal() {this.open = true;},
            replaceChildren(value) {this.content = value;}});
          return nodes.get(id);
        }};
        const sandbox = vm.createContext({document, assert,
          performance: {now: () => now},
          renderMarkdown: (body, options) => ({body, options})});
        const source = fs.readFileSync('static/app.js', 'utf8');
        const bootstrap = source.indexOf('for(let i=1;i<=23;i++)');
        assert.ok(bootstrap > 0);
        vm.runInContext(source.slice(0, bootstrap), sandbox);
        vm.runInContext(String.raw`
          current = {id: 'E11-Q34', concept: {id: 's3-storage', title: 'S3', summary: '요약'}};
          concepts = [{id: 'iam', title: 'IAM', body: '다른 개념'},
            {id: 's3-storage', title: 'S3 상세', body: '선택표\n## 내 오답\n개인 메모'}];
          selected = new Set(['B']); startedAt = 0;
          openQuestionConcept();
          assert.equal($('question-concept-title').textContent, 'S3 상세');
          assert.equal($('question-concept-body').content.body, '선택표\n');
          assert.equal(elapsedMs, 1000); assert.equal(startedAt, null);
          assert.equal(current.id, 'E11-Q34'); assert.ok(selected.has('B'));
          assert.equal(answered, null);
        `, sandbox);
        now = 11000;
        document.hidden = true;
        vm.runInContext('resumeTimer(); assert.equal(startedAt, null);', sandbox);
        document.hidden = false;
        vm.runInContext('resumeTimer(); assert.equal(startedAt, null);', sandbox);
        nodes.get('question-concept-dialog').open = false;
        vm.runInContext(String.raw`
          resumeTimer(); assert.equal(startedAt, 11000); assert.equal(elapsedMs, 1000);
          assert.ok(selected.has('B')); assert.equal(current.id, 'E11-Q34');
          concepts = []; openQuestionConcept();
          assert.equal($('question-concept-body').content.body, '요약');
          assert.equal(resolveStudyLink('../private.pdf'), null);
          assert.equal(resolveStudyLink('book.pdf#page=195'), '/api/reference?name=book.pdf#page=195');
        `, sandbox);
        """
        result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
